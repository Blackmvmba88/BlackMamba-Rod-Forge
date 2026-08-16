from __future__ import annotations

from dataclasses import dataclass

from .checkpointing import CheckpointManager
from .cognition import CognitiveEngine, Hypothesis
from .critic import Critic
from .part_graph import PartGraph
from .repair_engine import RepairEngine
from .schemas import ProjectState, Task, TaskStatus
from .state_manager import StateManager


@dataclass(slots=True)
class RunSummary:
    completed: int
    blocked: int
    skipped: int
    global_failures: int
    done: bool


class Orchestrator:
    def __init__(self, state_manager: StateManager, checkpoint_manager: CheckpointManager,
                 executor, critic: Critic | None = None, repair_engine: RepairEngine | None = None,
                 cognitive_engine: CognitiveEngine | None = None,
                 checkpoint_every: int = 2, max_global_failures: int = 20):
        self.state_manager = state_manager
        self.checkpoint_manager = checkpoint_manager
        self.executor = executor
        self.critic = critic or Critic()
        self.repair_engine = repair_engine or RepairEngine()
        self.cognitive_engine = cognitive_engine
        self.checkpoint_every = max(1, checkpoint_every)
        self.max_global_failures = max_global_failures

    def run(self, state: ProjectState) -> RunSummary:
        graph = PartGraph(state.tasks)
        self.state_manager.save(state)

        while not state.done:
            if state.global_failures >= self.max_global_failures:
                state.blocked_reason = "global failure budget exhausted"
                break

            task = graph.next_viable(state)
            if task is None:
                unresolved = graph.unresolved_critical()
                if unresolved:
                    state.blocked_reason = ", ".join(task.task_id for task in unresolved)
                    break

                unfinished = [
                    task for task in state.tasks.values()
                    if task.status not in {TaskStatus.COMPLETED, TaskStatus.SKIPPED}
                ]
                if unfinished:
                    state.blocked_reason = "no viable task remains"
                    break

                state.done = True
                break

            state.active_task_id = task.task_id
            task.status = TaskStatus.RUNNING
            task.attempts += 1

            hypothesis: Hypothesis | None = None
            if self.cognitive_engine is not None:
                hypothesis = self.cognitive_engine.imagine(task)
                self._run_counterfactual_probes(state, task, hypothesis)
                hypothesis = self.cognitive_engine.imagine(task)
                self.cognitive_engine.apply(task, hypothesis)

            self.state_manager.save(state)

            result = self.executor.execute(task)
            verdict = self.critic.review(task, result.to_dict())

            if self.cognitive_engine is not None and hypothesis is not None:
                self.cognitive_engine.learn(
                    project_name=state.project_name,
                    task=task,
                    accepted=verdict.accepted,
                    metrics=verdict.metrics,
                    hypothesis=hypothesis,
                )

            if verdict.accepted:
                task.status = TaskStatus.COMPLETED
                task.evidence = result.evidence
                task.last_error = None
                state.completed_order.append(task.task_id)
                state.active_task_id = None
                interval_checkpoint = len(state.completed_order) % self.checkpoint_every == 0
                milestone_checkpoint = bool(task.metadata.get("checkpoint"))
                if interval_checkpoint or milestone_checkpoint:
                    self.checkpoint_manager.save(state)
                self.state_manager.save(state)
                continue

            state.global_failures += 1
            task.last_error = verdict.reason
            task.status = TaskStatus.FAILED
            decision = self.repair_engine.decide(task)
            self.repair_engine.apply(task, decision)
            state.active_task_id = None
            self.state_manager.save(state)

        if state.done and state.completed_order:
            final_count = state.metadata.get("final_checkpoint_completed_count")
            if final_count != len(state.completed_order):
                self.checkpoint_manager.save(state)
                state.metadata["final_checkpoint_completed_count"] = len(state.completed_order)
        self.state_manager.save(state)
        return RunSummary(
            completed=sum(task.status == TaskStatus.COMPLETED for task in state.tasks.values()),
            blocked=sum(task.status == TaskStatus.BLOCKED for task in state.tasks.values()),
            skipped=sum(task.status == TaskStatus.SKIPPED for task in state.tasks.values()),
            global_failures=state.global_failures,
            done=state.done,
        )

    def _run_counterfactual_probes(
        self,
        state: ProjectState,
        task: Task,
        hypothesis: Hypothesis,
    ) -> None:
        if self.cognitive_engine is None or not self.critic.counterfactual_feedback_available:
            return

        probe = getattr(self.executor, "probe", None)
        if not callable(probe):
            return

        strategies = self.cognitive_engine.probe_candidates(hypothesis)
        if not strategies:
            return

        cognition = task.metadata.setdefault("cognition", {})
        probe_errors = cognition.setdefault("probe_errors", [])

        for strategy in strategies:
            try:
                probe_result = probe(task, strategy)
            except Exception as exc:
                probe_errors.append({"strategy": strategy, "error": str(exc)})
                continue

            if not probe_result.success:
                probe_errors.append({
                    "strategy": strategy,
                    "error": probe_result.error or "counterfactual probe failed",
                })
                continue

            preview_path = probe_result.evidence.get("preview_path")
            if not preview_path:
                probe_errors.append({"strategy": strategy, "error": "probe produced no preview"})
                continue

            try:
                metrics = self.critic.observe_preview(
                    preview_path,
                    baseline_reference_match=self.critic.previous_reference_match,
                )
            except Exception as exc:
                probe_errors.append({"strategy": strategy, "error": str(exc)})
                continue

            episode = self.cognitive_engine.learn_probe(
                project_name=state.project_name,
                task=task,
                strategy=strategy,
                metrics=metrics,
                hypothesis=hypothesis,
            )
            if episode is None:
                probe_errors.append({
                    "strategy": strategy,
                    "error": f"probe produced no {hypothesis.metric} metric",
                })

        if not probe_errors:
            cognition.pop("probe_errors", None)

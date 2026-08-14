import pytest

from rodforge.blender_executor import DryRunExecutor, ExecutionResult
from rodforge.checkpointing import CheckpointManager
from rodforge.cognition import CognitiveEngine, ExperienceMemory
from rodforge.critic import Critic
from rodforge.orchestrator import Orchestrator
from rodforge.schemas import ProjectState, Task
from rodforge.state_manager import StateManager


def _wheel_task() -> Task:
    return Task(
        task_id="front_wheels",
        name="Front wheels",
        objective="Choose a wheel construction method",
        strategy="wheel_torus",
        success_criteria={"object_exists": True, "named": True},
        metadata={
            "cognitive_signature": "front_wheels",
            "cognitive_metric": "improvement_score",
            "cognitive_candidates": ["wheel_cylinder"],
        },
    )


def test_probe_candidates_target_underexplored_alternatives(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    engine = CognitiveEngine(
        memory,
        mode="shadow",
        counterfactual_probes=True,
        max_probes_per_task=1,
        probe_sample_target=3,
    )
    task = _wheel_task()
    hypothesis = engine.imagine(task)

    assert engine.probe_candidates(hypothesis) == ["wheel_cylinder"]

    for score in (0.72, 0.76, 0.74):
        episode = engine.learn_probe(
            project_name="probe_training",
            task=task,
            strategy="wheel_cylinder",
            metrics={"improvement_score": score},
            hypothesis=hypothesis,
        )
        assert episode is not None
        assert episode.source == "counterfactual_probe"

    refreshed = engine.imagine(task)
    assert refreshed.prediction_for("wheel_cylinder").samples == 3
    assert engine.probe_candidates(refreshed) == []
    assert task.strategy == "wheel_torus"


def test_probe_learning_records_prediction_error_without_changing_task(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    engine = CognitiveEngine(memory, mode="shadow")
    task = _wheel_task()
    hypothesis = engine.imagine(task)

    episode = engine.learn_probe(
        project_name="probe_training",
        task=task,
        strategy="wheel_cylinder",
        metrics={"improvement_score": 0.80},
        hypothesis=hypothesis,
    )

    assert episode is not None
    assert episode.strategy == "wheel_cylinder"
    assert episode.source == "counterfactual_probe"
    assert episode.predicted_score == pytest.approx(0.5)
    assert episode.observed_score == pytest.approx(0.8)
    assert episode.prediction_error == pytest.approx(0.3)
    assert task.strategy == "wheel_torus"


class _ProbeExecutor(DryRunExecutor):
    def __init__(self):
        self.probed: list[str] = []

    def probe(self, task: Task, strategy: str) -> ExecutionResult:
        self.probed.append(strategy)
        return ExecutionResult(
            True,
            {
                "object_exists": True,
                "object_name": f"RF_{task.task_id}",
                "strategy": strategy,
                "preview_path": f"{strategy}.png",
                "counterfactual": True,
            },
        )


class _ProbeCritic(Critic):
    def __init__(self):
        super().__init__()
        self._previous_reference_match = 0.40

    @property
    def counterfactual_feedback_available(self) -> bool:
        return True

    def observe_preview(self, preview_path, *, baseline_reference_match=None):
        assert baseline_reference_match == 0.40
        return {
            "reference_match": 0.70,
            "improvement_score": 0.65,
        }


def test_orchestrator_probes_then_executes_planned_strategy_in_shadow_mode(tmp_path):
    task = _wheel_task()
    state = ProjectState(project_name="counterfactual_run", tasks={task.task_id: task})
    memory = ExperienceMemory(tmp_path / "cognition" / "experience.json")
    engine = CognitiveEngine(
        memory,
        mode="shadow",
        counterfactual_probes=True,
        max_probes_per_task=1,
        probe_sample_target=3,
    )
    executor = _ProbeExecutor()
    critic = _ProbeCritic()
    orchestrator = Orchestrator(
        state_manager=StateManager(tmp_path / "state.json"),
        checkpoint_manager=CheckpointManager(tmp_path / "checkpoints"),
        executor=executor,
        critic=critic,
        cognitive_engine=engine,
        checkpoint_every=1,
    )

    summary = orchestrator.run(state)

    assert summary.done is True
    assert summary.global_failures == 0
    assert executor.probed == ["wheel_cylinder"]
    assert task.strategy == "wheel_torus"
    assert critic.previous_reference_match == pytest.approx(0.40)
    assert [episode.source for episode in memory.episodes] == [
        "counterfactual_probe",
        "execution",
    ]
    assert memory.episodes[0].strategy == "wheel_cylinder"

from __future__ import annotations

from dataclasses import dataclass

from .schemas import Task, TaskStatus


@dataclass(slots=True)
class RepairDecision:
    action: str
    reason: str


class RepairEngine:
    """Selects the next unused fallback instead of looping blindly."""

    def decide(self, task: Task) -> RepairDecision:
        attempted = set(task.metadata.get("attempted_repairs", []))

        if task.can_retry() and "retry_same" not in attempted:
            return RepairDecision("retry_same", "Retry budget remains")

        for strategy in task.fallback_strategies:
            if strategy not in attempted:
                return RepairDecision(strategy, f"Trying fallback: {strategy}")

        return RepairDecision("block", "No unused repair strategy remains")

    def apply(self, task: Task, decision: RepairDecision) -> None:
        history = task.metadata.setdefault("attempted_repairs", [])
        if decision.action != "block":
            history.append(decision.action)
            task.strategy = decision.action
            task.status = TaskStatus.NEEDS_REPAIR
        else:
            task.status = TaskStatus.BLOCKED if task.is_critical else TaskStatus.SKIPPED

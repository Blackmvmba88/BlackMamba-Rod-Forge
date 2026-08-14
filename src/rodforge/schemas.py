from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REPAIR = "needs_repair"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class Criticality(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class Task:
    task_id: str
    name: str
    objective: str
    dependencies: list[str] = field(default_factory=list)
    strategy: str = "default"
    success_criteria: dict[str, Any] = field(default_factory=dict)
    fallback_strategies: list[str] = field(default_factory=list)
    criticality: Criticality = Criticality.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    evidence: dict[str, Any] = field(default_factory=dict)
    last_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        return self.criticality == Criticality.CRITICAL

    def can_retry(self) -> bool:
        return self.attempts < self.max_attempts

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["criticality"] = self.criticality.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        payload = dict(data)
        payload["status"] = TaskStatus(payload.get("status", TaskStatus.PENDING.value))
        payload["criticality"] = Criticality(payload.get("criticality", Criticality.NORMAL.value))
        return cls(**payload)


@dataclass(slots=True)
class ProjectState:
    project_name: str
    tasks: dict[str, Task] = field(default_factory=dict)
    completed_order: list[str] = field(default_factory=list)
    active_task_id: str | None = None
    global_failures: int = 0
    checkpoint_index: int = 0
    blocked_reason: str | None = None
    done: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "tasks": {key: task.to_dict() for key, task in self.tasks.items()},
            "completed_order": list(self.completed_order),
            "active_task_id": self.active_task_id,
            "global_failures": self.global_failures,
            "checkpoint_index": self.checkpoint_index,
            "blocked_reason": self.blocked_reason,
            "done": self.done,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectState":
        return cls(
            project_name=data["project_name"],
            tasks={key: Task.from_dict(value) for key, value in data.get("tasks", {}).items()},
            completed_order=list(data.get("completed_order", [])),
            active_task_id=data.get("active_task_id"),
            global_failures=int(data.get("global_failures", 0)),
            checkpoint_index=int(data.get("checkpoint_index", 0)),
            blocked_reason=data.get("blocked_reason"),
            done=bool(data.get("done", False)),
            metadata=dict(data.get("metadata", {})),
        )

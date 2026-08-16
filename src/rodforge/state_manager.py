from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .schemas import ProjectState, TaskStatus


class StateManager:
    """Atomic JSON persistence for resumable autonomous runs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> ProjectState:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        with self.path.open("r", encoding="utf-8") as handle:
            state = ProjectState.from_dict(json.load(handle))

        interrupted = [
            task for task in state.tasks.values()
            if task.status == TaskStatus.RUNNING
        ]
        for task in interrupted:
            task.status = TaskStatus.NEEDS_REPAIR
            task.last_error = "interrupted before execution verdict"
            task.metadata.setdefault("recovery_events", []).append({
                "reason": "interrupted_running_task",
                "attempt": task.attempts,
            })
        if interrupted:
            state.active_task_id = None
            state.blocked_reason = None
            state.done = False
            self.save(state)
        return state

    def save(self, state: ProjectState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state.to_dict(), indent=2, sort_keys=True)
        fd, temp_name = tempfile.mkstemp(prefix=self.path.name, dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

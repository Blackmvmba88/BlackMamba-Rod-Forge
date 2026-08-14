from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schemas import Task


@dataclass(slots=True)
class CriticResult:
    accepted: bool
    reason: str = ""


class Critic:
    """Cheap structural critic first; visual critics can plug in later."""

    def review(self, task: Task, result: dict[str, Any]) -> CriticResult:
        if not result.get("success", False):
            return CriticResult(False, result.get("error", "executor failed"))

        criteria = task.success_criteria
        evidence = result.get("evidence", {})

        if criteria.get("object_exists") and not evidence.get("object_exists", False):
            return CriticResult(False, "Expected object was not created")

        if criteria.get("named") and not evidence.get("object_name"):
            return CriticResult(False, "Created object has no canonical name")

        return CriticResult(True, "Structural checks passed")

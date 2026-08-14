from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import Task


@dataclass(slots=True)
class CriticResult:
    accepted: bool
    reason: str = ""
    metrics: dict[str, float] = field(default_factory=dict)


class Critic:
    """Cheap structural critic first; richer visual critics can plug in later.

    Numeric evidence is surfaced as normalized metrics so the cognitive loop
    can compare what it expected with what actually happened. Structural
    success remains available even before a visual critic exists.
    """

    def review(self, task: Task, result: dict[str, Any]) -> CriticResult:
        if not result.get("success", False):
            return CriticResult(
                False,
                result.get("error", "executor failed"),
                {"structural_score": 0.0},
            )

        criteria = task.success_criteria
        evidence = result.get("evidence", {})

        if criteria.get("object_exists") and not evidence.get("object_exists", False):
            return CriticResult(False, "Expected object was not created", {"structural_score": 0.0})

        if criteria.get("named") and not evidence.get("object_name"):
            return CriticResult(False, "Created object has no canonical name", {"structural_score": 0.0})

        metrics: dict[str, float] = {"structural_score": 1.0}

        quality_score = evidence.get("quality_score")
        if isinstance(quality_score, (int, float)) and not isinstance(quality_score, bool):
            metrics["quality_score"] = self._clamp01(float(quality_score))

        score_bundle = evidence.get("scores", {})
        if isinstance(score_bundle, dict):
            for name, value in score_bundle.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    metrics[str(name)] = self._clamp01(float(value))

        return CriticResult(True, "Structural checks passed", metrics)

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, value))

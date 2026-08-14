from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schemas import Task
from .visual_feedback import VisualComparator


@dataclass(slots=True)
class CriticResult:
    accepted: bool
    reason: str = ""
    metrics: dict[str, float] = field(default_factory=dict)


class Critic:
    """Structural + optional visual critic.

    Visual feedback is observational by default: a weak image score does not
    fail the task unless an explicit minimum is configured. This keeps the
    cognitive loop free to learn from bad attempts instead of hiding them.
    """

    def __init__(
        self,
        *,
        reference_image: str | Path | None = None,
        visual_comparator: VisualComparator | None = None,
    ):
        self.reference_image = Path(reference_image) if reference_image else None
        self.visual_comparator = visual_comparator
        self._previous_reference_match: float | None = None

    @property
    def previous_reference_match(self) -> float | None:
        return self._previous_reference_match

    @property
    def visual_feedback_available(self) -> bool:
        return self.visual_comparator is not None and self.reference_image is not None

    @property
    def counterfactual_feedback_available(self) -> bool:
        return (
            self.visual_feedback_available
            and self.reference_image is not None
            and self.reference_image.exists()
        )

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
        self._copy_numeric_evidence(evidence, metrics)
        visual_error = self._review_visual(evidence, metrics)

        minimum_reference_match = criteria.get("min_reference_match")
        if minimum_reference_match is not None and "reference_match" in metrics:
            minimum = self._clamp01(float(minimum_reference_match))
            if metrics["reference_match"] < minimum:
                return CriticResult(
                    False,
                    f"Reference match {metrics['reference_match']:.3f} below required {minimum:.3f}",
                    metrics,
                )

        if visual_error and criteria.get("visual_required"):
            return CriticResult(False, visual_error, metrics)

        reason = "Structural checks passed"
        if "reference_match" in metrics:
            reason += f"; visual match={metrics['reference_match']:.3f}"
        elif visual_error:
            reason += f"; visual feedback unavailable: {visual_error}"
        return CriticResult(True, reason, metrics)

    def observe_preview(
        self,
        preview_path: str | Path,
        *,
        baseline_reference_match: float | None = None,
    ) -> dict[str, float]:
        """Score a temporary preview without mutating the critic's real baseline."""
        if not self.visual_feedback_available:
            return {}

        visual_scores = self.visual_comparator.compare(self.reference_image, preview_path)
        metrics = {
            str(name): self._clamp01(float(value))
            for name, value in visual_scores.items()
        }
        current_match = metrics.get("reference_match")
        if current_match is not None:
            baseline = 0.0 if baseline_reference_match is None else self._clamp01(baseline_reference_match)
            delta = current_match - baseline
            metrics["improvement_score"] = self._clamp01(0.5 + (delta / 2.0))
        return metrics

    def _review_visual(self, evidence: dict[str, Any], metrics: dict[str, float]) -> str | None:
        if not self.visual_feedback_available:
            return None

        preview_path = evidence.get("preview_path")
        if not preview_path:
            return None

        previous_match = self._previous_reference_match
        try:
            visual_metrics = self.observe_preview(
                preview_path,
                baseline_reference_match=previous_match,
            )
        except Exception as exc:
            error = str(exc)
            evidence["visual_feedback_error"] = error
            return error

        metrics.update(visual_metrics)
        current_match = metrics.get("reference_match")
        if current_match is not None:
            baseline = 0.0 if previous_match is None else previous_match
            delta = current_match - baseline
            evidence["visual_feedback"] = {
                "previous_reference_match": previous_match,
                "reference_match": current_match,
                "reference_delta": delta,
                "improvement_score": metrics.get("improvement_score"),
            }
            self._previous_reference_match = current_match

        evidence.setdefault("scores", {}).update(
            {
                name: value
                for name, value in metrics.items()
                if name in {"quality_score", "silhouette_score", "proportion_score", "reference_match", "improvement_score"}
            }
        )
        return None

    def _copy_numeric_evidence(self, evidence: dict[str, Any], metrics: dict[str, float]) -> None:
        quality_score = evidence.get("quality_score")
        if isinstance(quality_score, (int, float)) and not isinstance(quality_score, bool):
            metrics["quality_score"] = self._clamp01(float(quality_score))

        score_bundle = evidence.get("scores", {})
        if isinstance(score_bundle, dict):
            for name, value in score_bundle.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    metrics[str(name)] = self._clamp01(float(value))

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, value))

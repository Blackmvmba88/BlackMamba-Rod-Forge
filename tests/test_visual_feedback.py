from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from rodforge.critic import Critic
from rodforge.schemas import Task
from rodforge.visual_feedback import VisualComparator


def _reference(path: Path) -> None:
    image = Image.new("RGB", (120, 90), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 30, 100, 65), fill="black")
    image.save(path)


def _preview(path: Path, box: tuple[int, int, int, int]) -> None:
    image = Image.new("RGBA", (120, 90), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, fill=(30, 30, 30, 255))
    image.save(path)


def test_visual_comparator_scores_matching_silhouette_high(tmp_path):
    reference = tmp_path / "reference.png"
    preview = tmp_path / "preview.png"
    _reference(reference)
    _preview(preview, (20, 30, 100, 65))

    scores = VisualComparator().compare(reference, preview)

    assert scores["silhouette_score"] > 0.95
    assert scores["proportion_score"] > 0.95
    assert scores["reference_match"] > 0.95


def test_visual_comparator_penalizes_wrong_proportion(tmp_path):
    reference = tmp_path / "reference.png"
    preview = tmp_path / "preview.png"
    _reference(reference)
    _preview(preview, (45, 15, 75, 75))

    scores = VisualComparator().compare(reference, preview)

    assert scores["proportion_score"] < 0.5
    assert scores["reference_match"] < 0.8


class _SequenceComparator:
    def __init__(self, matches: list[float]):
        self.matches = iter(matches)

    def compare(self, reference_image, preview_image):
        match = next(self.matches)
        return {
            "silhouette_score": match,
            "proportion_score": match,
            "reference_match": match,
            "quality_score": match,
        }


def _task() -> Task:
    return Task(
        task_id="body_shell",
        name="Body",
        objective="Refine body",
        success_criteria={"object_exists": True, "named": True},
        metadata={"cognitive_metric": "improvement_score"},
    )


def _result(preview_path: str) -> dict:
    return {
        "success": True,
        "evidence": {
            "object_exists": True,
            "object_name": "RF_body_shell",
            "preview_path": preview_path,
        },
    }


def test_critic_turns_visual_delta_into_normalized_improvement_signal():
    critic = Critic(
        reference_image="reference.png",
        visual_comparator=_SequenceComparator([0.40, 0.70, 0.55]),
    )

    first = critic.review(_task(), _result("first.png"))
    second = critic.review(_task(), _result("second.png"))
    third = critic.review(_task(), _result("third.png"))

    assert first.metrics["reference_match"] == pytest.approx(0.40)
    assert first.metrics["improvement_score"] == pytest.approx(0.70)
    assert second.metrics["improvement_score"] == pytest.approx(0.65)
    assert third.metrics["improvement_score"] == pytest.approx(0.425)
    assert third.metrics["improvement_score"] < 0.5

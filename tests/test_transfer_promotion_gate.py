import pytest

from rodforge.cognition import CognitiveEngine, ExperienceEpisode, ExperienceMemory
from rodforge.config import load_config
from rodforge.schemas import Task


def _episode(*, reference: str, strategy: str, score: float, signature: str = "wheel"):
    return ExperienceEpisode(
        timestamp="2026-08-14T00:00:00+00:00",
        project_name=reference,
        task_id="wheel",
        signature=signature,
        strategy=strategy,
        metric="quality_score",
        predicted_score=0.5,
        observed_score=score,
        prediction_error=score - 0.5,
        accepted=True,
        reference_sha256=reference,
    )


def _task() -> Task:
    return Task(
        task_id="wheel",
        name="Wheel",
        objective="Choose the better wheel construction",
        strategy="method_a",
        metadata={
            "cognitive_signature": "wheel",
            "cognitive_metric": "quality_score",
            "cognitive_candidates": ["method_b"],
        },
    )


def _engine(memory: ExperienceMemory, *, min_refs: int = 3, max_spread: float = 0.10):
    return CognitiveEngine(
        memory,
        mode="active",
        reference_sha256="unseen-reference",
        min_samples=1,
        activation_confidence=0.50,
        activation_margin=0.05,
        min_transfer_references=min_refs,
        max_transfer_spread=max_spread,
    )


def test_transfer_does_not_activate_before_distinct_reference_threshold(tmp_path):
    memory = ExperienceMemory(tmp_path / "memory.json")
    for reference in ("ref-a", "ref-b"):
        memory.append(_episode(reference=reference, strategy="method_a", score=0.30))
        memory.append(_episode(reference=reference, strategy="method_b", score=0.90))

    hypothesis = _engine(memory).imagine(_task())
    candidate = hypothesis.prediction_for("method_b")

    assert candidate is not None
    assert candidate.scope == "signature_transfer"
    assert candidate.transfer_references == 2
    assert candidate.promotion_ready is False
    assert candidate.promotion_reason == "insufficient_distinct_references"
    assert hypothesis.recommended_strategy == "method_a"


def test_replicated_stable_transfer_can_activate(tmp_path):
    memory = ExperienceMemory(tmp_path / "memory.json")
    for reference, low, high in (
        ("ref-a", 0.30, 0.88),
        ("ref-b", 0.32, 0.90),
        ("ref-c", 0.31, 0.89),
    ):
        memory.append(_episode(reference=reference, strategy="method_a", score=low))
        memory.append(_episode(reference=reference, strategy="method_b", score=high))

    hypothesis = _engine(memory).imagine(_task())
    candidate = hypothesis.prediction_for("method_b")

    assert candidate is not None
    assert candidate.transfer_references == 3
    assert candidate.transfer_spread == pytest.approx(0.02)
    assert candidate.promotion_ready is True
    assert candidate.promotion_reason == "replicated_across_references"
    assert hypothesis.recommended_strategy == "method_b"


def test_unstable_transfer_remains_observational_even_with_many_references(tmp_path):
    memory = ExperienceMemory(tmp_path / "memory.json")
    for reference, high in (
        ("ref-a", 0.95),
        ("ref-b", 0.72),
        ("ref-c", 0.50),
    ):
        memory.append(_episode(reference=reference, strategy="method_a", score=0.25))
        memory.append(_episode(reference=reference, strategy="method_b", score=high))

    hypothesis = _engine(memory, max_spread=0.10).imagine(_task())
    candidate = hypothesis.prediction_for("method_b")

    assert candidate is not None
    assert candidate.transfer_references == 3
    assert candidate.transfer_spread == pytest.approx(0.45)
    assert candidate.promotion_ready is False
    assert candidate.promotion_reason == "cross_reference_results_unstable"
    assert hypothesis.recommended_strategy == "method_a"


def test_strategy_only_transfer_never_changes_authoritative_action(tmp_path):
    memory = ExperienceMemory(tmp_path / "memory.json")
    for reference in ("ref-a", "ref-b", "ref-c", "ref-d"):
        memory.append(
            _episode(
                reference=reference,
                strategy="method_b",
                score=0.99,
                signature="different-part",
            )
        )

    hypothesis = _engine(memory).imagine(_task())
    candidate = hypothesis.prediction_for("method_b")

    assert candidate is not None
    assert candidate.scope == "strategy_transfer"
    assert candidate.promotion_ready is False
    assert candidate.promotion_reason == "strategy_only_transfer_never_activates"
    assert hypothesis.recommended_strategy == "method_a"


def test_config_exposes_transfer_promotion_thresholds(tmp_path):
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "cognition:\n"
        "  min_transfer_references: 5\n"
        "  max_transfer_spread: 0.07\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.cognition is not None
    assert config.cognition.min_transfer_references == 5
    assert config.cognition.max_transfer_spread == pytest.approx(0.07)

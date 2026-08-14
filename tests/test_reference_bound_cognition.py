import hashlib
import json

import pytest
from PIL import Image

from rodforge.cli import main
from rodforge.cognition import CognitiveEngine, ExperienceEpisode, ExperienceMemory
from rodforge.cognitive_report import build_cognitive_report
from rodforge.schemas import Task


def _episode(
    *,
    reference_sha256: str | None,
    score: float,
    strategy: str = "method_a",
    signature: str = "wheel",
    metric: str = "quality_score",
) -> ExperienceEpisode:
    return ExperienceEpisode(
        timestamp="2026-08-14T00:00:00+00:00",
        project_name="training",
        task_id="wheel",
        signature=signature,
        strategy=strategy,
        metric=metric,
        predicted_score=0.5,
        observed_score=score,
        prediction_error=score - 0.5,
        accepted=True,
        reference_sha256=reference_sha256,
    )


def _task() -> Task:
    return Task(
        task_id="wheel",
        name="Wheel",
        objective="Build a wheel",
        strategy="method_a",
        metadata={
            "cognitive_signature": "wheel",
            "cognitive_metric": "quality_score",
        },
    )


def test_learning_binds_episode_to_exact_reference(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    engine = CognitiveEngine(memory, mode="shadow", reference_sha256="ref-a")
    task = _task()
    hypothesis = engine.imagine(task)

    episode = engine.learn(
        project_name="figure_a",
        task=task,
        accepted=True,
        metrics={"quality_score": 0.82},
        hypothesis=hypothesis,
    )

    assert episode.reference_sha256 == "ref-a"
    assert memory.episodes[0].reference_sha256 == "ref-a"
    assert task.metadata["cognition"]["last_episode"]["reference_sha256"] == "ref-a"


def test_prediction_prefers_same_reference_before_transfer(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    for _ in range(3):
        memory.append(_episode(reference_sha256="ref-a", score=0.90))
        memory.append(_episode(reference_sha256="ref-b", score=0.20))

    same_reference = CognitiveEngine(
        memory,
        mode="shadow",
        reference_sha256="ref-b",
    ).imagine(_task()).candidates[0]
    unseen_reference = CognitiveEngine(
        memory,
        mode="shadow",
        reference_sha256="ref-c",
    ).imagine(_task()).candidates[0]

    assert same_reference.scope == "reference_signature"
    assert same_reference.expected_score == pytest.approx(0.20)
    assert same_reference.samples == 3

    assert unseen_reference.scope == "signature_transfer"
    assert unseen_reference.expected_score == pytest.approx(0.55)
    assert unseen_reference.samples == 6
    assert unseen_reference.confidence < same_reference.confidence


def test_memory_v1_loads_legacy_episode_without_reference(tmp_path):
    path = tmp_path / "experience.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "episodes": [
                    {
                        "timestamp": "2026-08-14T00:00:00+00:00",
                        "project_name": "legacy",
                        "task_id": "wheel",
                        "signature": "wheel",
                        "strategy": "method_a",
                        "metric": "quality_score",
                        "predicted_score": None,
                        "observed_score": 0.7,
                        "prediction_error": None,
                        "accepted": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    memory = ExperienceMemory(path)

    assert len(memory.episodes) == 1
    assert memory.episodes[0].source == "execution"
    assert memory.episodes[0].reference_sha256 is None


def test_report_separates_references_and_measures_transfer_stability():
    episodes = [
        _episode(reference_sha256="ref-a", score=0.80),
        _episode(reference_sha256="ref-a", score=0.82),
        _episode(reference_sha256="ref-b", score=0.75),
        _episode(reference_sha256="ref-b", score=0.77),
        _episode(reference_sha256=None, score=0.40, strategy="legacy"),
    ]

    report = build_cognitive_report(episodes)

    assert report["references"] == {
        "unique_bound": 2,
        "bound_episodes": 4,
        "unbound_episodes": 1,
    }
    assert report["by_reference"]["ref-a"]["episodes"] == 2
    assert report["by_reference"]["ref-b"]["episodes"] == 2
    assert report["by_reference"]["unbound"]["episodes"] == 1
    assert report["transfer_stability"]["comparable_groups"] == 1
    assert report["transfer_stability"]["stable_groups"] == 1
    assert report["transfer_stability"]["mean_reference_spread"] == pytest.approx(0.05)


def test_cli_run_fingerprints_reference_into_all_new_episodes(tmp_path, capsys):
    reference = tmp_path / "reference.png"
    Image.new("RGB", (128, 96), "white").save(reference)
    expected_sha = hashlib.sha256(reference.read_bytes()).hexdigest()

    memory_path = tmp_path / "experience.json"
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project_name: fingerprint_run\n"
        f"reference_image: {json.dumps(str(reference))}\n"
        "outputs:\n"
        f"  blend: {json.dumps(str(tmp_path / 'out.blend'))}\n"
        f"  state: {json.dumps(str(tmp_path / 'state.json'))}\n"
        f"  checkpoints: {json.dumps(str(tmp_path / 'checkpoints'))}\n"
        "cognition:\n"
        f"  memory_file: {json.dumps(str(memory_path))}\n"
        "visual_feedback:\n"
        "  enabled: false\n",
        encoding="utf-8",
    )

    code = main([
        "run",
        "--config",
        str(config_path),
        "--executor",
        "dry-run",
    ])
    capsys.readouterr()

    memory = ExperienceMemory(memory_path)
    assert code == 0
    assert memory.episodes
    assert {episode.reference_sha256 for episode in memory.episodes} == {expected_sha}

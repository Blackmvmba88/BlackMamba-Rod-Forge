import json

import pytest

from rodforge.cli import main
from rodforge.cognition import ExperienceEpisode, ExperienceMemory
from rodforge.cognitive_report import build_cognitive_report


def _episode(
    *,
    strategy: str,
    predicted: float | None,
    observed: float,
    source: str = "execution",
    metric: str = "improvement_score",
) -> ExperienceEpisode:
    error = None if predicted is None else observed - predicted
    return ExperienceEpisode(
        timestamp="2026-08-14T00:00:00+00:00",
        project_name="training",
        task_id="body_shell",
        signature="body_shell",
        strategy=strategy,
        metric=metric,
        predicted_score=predicted,
        observed_score=observed,
        prediction_error=error,
        accepted=True,
        source=source,
    )


def test_report_detects_prediction_error_improvement():
    episodes = [
        _episode(strategy="body_box", predicted=0.90, observed=0.50),
        _episode(strategy="body_box", predicted=0.80, observed=0.50),
        _episode(strategy="body_tapered", predicted=0.75, observed=0.55, source="counterfactual_probe"),
        _episode(strategy="body_box", predicted=0.66, observed=0.54),
        _episode(strategy="body_tapered", predicted=0.62, observed=0.54, source="counterfactual_probe"),
        _episode(strategy="body_box", predicted=0.59, observed=0.54),
    ]

    report = build_cognitive_report(episodes, window=3)

    assert report["episodes_total"] == 6
    assert report["predictions_total"] == 6
    assert report["sources"] == {"counterfactual_probe": 2, "execution": 4}
    assert report["learning_trend"]["status"] == "improving"
    assert report["learning_trend"]["early_mae"] == pytest.approx(0.30)
    assert report["learning_trend"]["recent_mae"] == pytest.approx((0.12 + 0.08 + 0.05) / 3)
    assert report["learning_trend"]["mae_improvement"] > 0.20
    assert report["prediction_accuracy"]["skill"] > 0.80
    assert report["by_source"]["counterfactual_probe"]["episodes"] == 2
    assert report["by_strategy"]["body_tapered"]["episodes"] == 2


def test_direction_accuracy_tracks_better_or_worse_prediction_sign():
    episodes = [
        _episode(strategy="a", predicted=0.70, observed=0.80),
        _episode(strategy="a", predicted=0.30, observed=0.20),
        _episode(strategy="a", predicted=0.70, observed=0.20),
        _episode(strategy="a", predicted=0.50, observed=0.80),
    ]

    report = build_cognitive_report(episodes, window=2)
    accuracy = report["prediction_accuracy"]

    assert accuracy["direction_samples"] == 3
    assert accuracy["direction_accuracy"] == pytest.approx(2 / 3)


def test_report_handles_unpredicted_and_empty_history():
    empty = build_cognitive_report([], window=5)
    assert empty["learning_trend"]["status"] == "insufficient_data"
    assert empty["prediction_accuracy"]["mae"] is None

    report = build_cognitive_report([
        _episode(strategy="first", predicted=None, observed=0.8),
    ])
    assert report["episodes_total"] == 1
    assert report["predictions_total"] == 0
    assert report["by_strategy"]["first"]["mean_observed_score"] == pytest.approx(0.8)


def test_cli_emits_json_cognition_report(tmp_path, capsys):
    memory_path = tmp_path / "experience.json"
    memory = ExperienceMemory(memory_path)
    memory.append(_episode(strategy="body_box", predicted=0.70, observed=0.60))
    memory.append(_episode(strategy="body_box", predicted=0.65, observed=0.60))

    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project_name: calibration_test\n"
        "cognition:\n"
        f"  memory_file: {json.dumps(str(memory_path))}\n",
        encoding="utf-8",
    )

    code = main([
        "cognition-report",
        "--config",
        str(config_path),
        "--window",
        "2",
    ])
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    assert output["episodes_total"] == 2
    assert output["predictions_total"] == 2
    assert output["prediction_accuracy"]["mae"] == pytest.approx(0.075)

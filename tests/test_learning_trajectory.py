import json
from pathlib import Path

from PIL import Image

from rodforge.config import load_config
from rodforge.curriculum import _trajectory_summary, run_curriculum


def _image(path: Path, color: str) -> None:
    Image.new("RGB", (96, 96), color).save(path)


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "project.yaml"
    path.write_text(
        "project_name: trajectory_test\n"
        "outputs:\n"
        f"  blend: {json.dumps(str(tmp_path / 'unused.blend'))}\n"
        f"  state: {json.dumps(str(tmp_path / 'unused_state.json'))}\n"
        f"  checkpoints: {json.dumps(str(tmp_path / 'unused_checkpoints'))}\n"
        "cognition:\n"
        "  enabled: true\n"
        "  mode: shadow\n"
        f"  memory_file: {json.dumps(str(tmp_path / 'base_memory.json'))}\n"
        "visual_feedback:\n"
        "  enabled: false\n",
        encoding="utf-8",
    )
    return path


def test_curriculum_records_baseline_and_per_figure_snapshots(tmp_path):
    ref_a = tmp_path / "a.png"
    ref_b = tmp_path / "b.png"
    _image(ref_a, "white")
    _image(ref_b, "gray")
    output_root = tmp_path / "school"

    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(
        f"output_root: {json.dumps(str(output_root))}\n"
        f"memory_file: {json.dumps(str(tmp_path / 'memory.json'))}\n"
        "runs:\n"
        "  - id: first\n"
        f"    reference_image: {json.dumps(str(ref_a))}\n"
        "  - id: second\n"
        f"    reference_image: {json.dumps(str(ref_b))}\n",
        encoding="utf-8",
    )

    report = run_curriculum(
        load_config(_config(tmp_path)),
        manifest,
        executor_kind="dry-run",
    )

    assert [point["run_id"] for point in report["trajectory"]] == [
        "baseline",
        "first",
        "second",
    ]
    assert report["trajectory"][0]["episodes_added"] == 0
    assert report["trajectory"][1]["episodes_added"] > 0
    assert report["trajectory"][2]["episodes_added"] > 0
    assert report["trajectory"][1]["bound_references"] == 1
    assert report["trajectory"][2]["bound_references"] == 2
    assert Path(report["trajectory_path"]).is_file()

    persisted = json.loads(Path(report["trajectory_path"]).read_text(encoding="utf-8"))
    assert len(persisted["trajectory"]) == 3
    assert persisted["summary"] == report["trajectory_summary"]


def test_blocked_reference_creates_zero_learning_snapshot(tmp_path):
    missing = tmp_path / "missing.png"
    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(
        f"output_root: {json.dumps(str(tmp_path / 'school'))}\n"
        "runs:\n"
        "  - id: missing_ref\n"
        f"    reference_image: {json.dumps(str(missing))}\n",
        encoding="utf-8",
    )

    report = run_curriculum(
        load_config(_config(tmp_path)),
        manifest,
        executor_kind="dry-run",
    )

    point = report["trajectory"][1]
    assert point["status"] == "blocked_reference"
    assert point["episodes_added"] == 0
    assert point["episodes_total"] == report["trajectory"][0]["episodes_total"]


def test_trajectory_summary_detects_improving_and_regressing_prediction_error():
    improving = _trajectory_summary([
        {"step": 0, "prediction_mae": None},
        {"step": 1, "prediction_mae": 0.30, "prediction_skill": 0.70},
        {"step": 2, "prediction_mae": 0.18, "prediction_skill": 0.82},
        {"step": 3, "prediction_mae": 0.10, "prediction_skill": 0.90},
    ])
    regressing = _trajectory_summary([
        {"step": 0, "prediction_mae": None},
        {"step": 1, "prediction_mae": 0.10, "prediction_skill": 0.90},
        {"step": 2, "prediction_mae": 0.25, "prediction_skill": 0.75},
    ])

    assert improving["status"] == "improving"
    assert improving["mae_improvement"] == 0.20
    assert improving["skill_improvement"] == 0.20
    assert regressing["status"] == "regressing"
    assert regressing["mae_improvement"] == -0.15

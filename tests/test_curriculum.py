import hashlib
import json
from pathlib import Path

from PIL import Image

from rodforge.cli import main
from rodforge.cognition import ExperienceMemory
from rodforge.config import load_config
from rodforge.curriculum import run_curriculum


def _image(path: Path, color: str) -> str:
    Image.new("RGB", (96, 96), color).save(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _base_config(tmp_path: Path) -> Path:
    path = tmp_path / "project.yaml"
    path.write_text(
        "project_name: curriculum_base\n"
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


def test_curriculum_runs_multiple_references_with_shared_memory(tmp_path):
    ref_a = tmp_path / "a.png"
    ref_b = tmp_path / "b.png"
    sha_a = _image(ref_a, "white")
    sha_b = _image(ref_b, "black")
    memory_path = tmp_path / "school_memory.json"
    output_root = tmp_path / "curriculum_outputs"

    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(
        "name: two_figure_school\n"
        f"output_root: {json.dumps(str(output_root))}\n"
        f"memory_file: {json.dumps(str(memory_path))}\n"
        "runs:\n"
        "  - id: figure_a\n"
        f"    reference_image: {json.dumps(str(ref_a))}\n"
        "  - id: figure_b\n"
        f"    reference_image: {json.dumps(str(ref_b))}\n",
        encoding="utf-8",
    )

    report = run_curriculum(
        load_config(_base_config(tmp_path)),
        manifest,
        executor_kind="dry-run",
    )

    assert report["runs_total"] == 2
    assert report["runs_completed"] == 2
    assert report["runs_blocked"] == 0
    assert report["runs_error"] == 0
    assert report["cognition"]["references"]["unique_bound"] == 2
    assert Path(report["report_path"]).is_file()

    memory = ExperienceMemory(memory_path)
    assert memory.episodes
    assert {episode.reference_sha256 for episode in memory.episodes} == {sha_a, sha_b}
    assert {episode.project_name for episode in memory.episodes} == {"figure_a", "figure_b"}


def test_curriculum_blocks_bad_reference_and_continues(tmp_path):
    valid = tmp_path / "valid.png"
    _image(valid, "white")
    missing = tmp_path / "missing.png"
    output_root = tmp_path / "outputs"

    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(
        f"output_root: {json.dumps(str(output_root))}\n"
        "runs:\n"
        "  - id: bad\n"
        f"    reference_image: {json.dumps(str(missing))}\n"
        "  - id: good\n"
        f"    reference_image: {json.dumps(str(valid))}\n",
        encoding="utf-8",
    )

    report = run_curriculum(
        load_config(_base_config(tmp_path)),
        manifest,
        executor_kind="dry-run",
    )

    assert report["runs_attempted"] == 2
    assert report["runs_blocked"] == 1
    assert report["runs_completed"] == 1
    assert report["runs"][0]["status"] == "blocked_reference"
    assert report["runs"][1]["status"] == "completed"


def test_curriculum_cli_emits_complete_json_report(tmp_path, capsys):
    ref_a = tmp_path / "a.png"
    ref_b = tmp_path / "b.png"
    _image(ref_a, "white")
    _image(ref_b, "gray")
    output_root = tmp_path / "outputs"
    memory_path = tmp_path / "memory.json"

    config_path = _base_config(tmp_path)
    manifest = tmp_path / "curriculum.yaml"
    manifest.write_text(
        f"output_root: {json.dumps(str(output_root))}\n"
        f"memory_file: {json.dumps(str(memory_path))}\n"
        "runs:\n"
        "  - id: first\n"
        f"    reference_image: {json.dumps(str(ref_a))}\n"
        "  - id: second\n"
        f"    reference_image: {json.dumps(str(ref_b))}\n",
        encoding="utf-8",
    )

    code = main([
        "curriculum-run",
        "--config",
        str(config_path),
        "--manifest",
        str(manifest),
        "--executor",
        "dry-run",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["runs_completed"] == 2
    assert payload["cognition"]["references"]["unique_bound"] == 2

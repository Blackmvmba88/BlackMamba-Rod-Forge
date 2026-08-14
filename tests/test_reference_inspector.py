from PIL import Image

from rodforge.cli import main
from rodforge.reference_inspector import inspect_reference


def test_missing_reference_is_not_ready(tmp_path):
    report = inspect_reference(tmp_path / "missing.png")

    assert report["exists"] is False
    assert report["ready"] is False
    assert report["errors"] == ["reference image does not exist"]


def test_valid_reference_reports_dimensions_and_hash(tmp_path):
    path = tmp_path / "reference.png"
    Image.new("RGBA", (320, 180), (255, 128, 0, 255)).save(path)

    report = inspect_reference(path)

    assert report["ready"] is True
    assert report["format"] == "PNG"
    assert report["width"] == 320
    assert report["height"] == 180
    assert report["has_alpha"] is True
    assert report["aspect_ratio"] == 320 / 180
    assert len(report["sha256"]) == 64


def test_tiny_reference_is_rejected(tmp_path):
    path = tmp_path / "tiny.png"
    Image.new("RGB", (32, 32), (0, 0, 0)).save(path)

    report = inspect_reference(path)

    assert report["ready"] is False
    assert "too small" in report["errors"][0]


def test_reference_check_cli_returns_readiness_status(tmp_path, capsys):
    reference = tmp_path / "reference.png"
    Image.new("RGB", (128, 96), (10, 20, 30)).save(reference)
    config = tmp_path / "project.yaml"
    config.write_text(
        "project_name: reference_test\n"
        f"reference_image: {reference}\n"
        "outputs:\n"
        f"  blend: {tmp_path / 'out.blend'}\n"
        f"  state: {tmp_path / 'state.json'}\n"
        f"  checkpoints: {tmp_path / 'checkpoints'}\n",
        encoding="utf-8",
    )

    assert main(["reference-check", "--config", str(config)]) == 0
    output = capsys.readouterr().out
    assert '"ready": true' in output
    assert '"width": 128' in output

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image


def inspect_reference(path: str | Path) -> dict[str, Any]:
    """Validate and fingerprint a visual reference without mutating it."""
    reference = Path(path)
    report: dict[str, Any] = {
        "path": str(reference),
        "exists": reference.is_file(),
        "ready": False,
        "errors": [],
    }

    if not reference.is_file():
        report["errors"].append("reference image does not exist")
        return report

    try:
        with Image.open(reference) as image:
            image.verify()
        with Image.open(reference) as image:
            width, height = image.size
            mode = image.mode
            image_format = image.format
            has_alpha = "A" in image.getbands()
    except Exception as exc:
        report["errors"].append(f"reference image is unreadable: {exc}")
        return report

    if width < 64 or height < 64:
        report["errors"].append("reference image is too small; minimum dimension is 64 px")

    report.update(
        {
            "format": image_format,
            "width": width,
            "height": height,
            "mode": mode,
            "has_alpha": has_alpha,
            "aspect_ratio": width / height if height else None,
            "sha256": _sha256(reference),
        }
    )
    report["ready"] = not report["errors"]
    return report


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

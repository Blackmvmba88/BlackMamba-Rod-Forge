from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image


@dataclass(slots=True)
class VisualScores:
    silhouette_score: float
    proportion_score: float
    reference_match: float
    quality_score: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


class VisualComparator:
    """Cheap deterministic image critic for cognitive feedback.

    It intentionally does not pretend to understand design semantics. It asks
    narrower questions that are useful very early in construction:

    - does the rendered silhouette resemble the reference silhouette?
    - does the subject bounding-box proportion resemble the reference?

    Preview renders are expected to use transparency when possible. Reference
    images may be ordinary RGB illustrations; their background is estimated
    from border pixels and removed by color distance.
    """

    def __init__(self, *, normalized_size: int = 128, background_distance: float = 42.0):
        self.normalized_size = max(32, int(normalized_size))
        self.background_distance = max(1.0, float(background_distance))

    def compare(self, reference_image: str | Path, preview_image: str | Path) -> dict[str, float]:
        reference_path = Path(reference_image)
        preview_path = Path(preview_image)
        if not reference_path.exists():
            raise FileNotFoundError(f"Reference image not found: {reference_path}")
        if not preview_path.exists():
            raise FileNotFoundError(f"Preview image not found: {preview_path}")

        reference_mask, reference_bbox = self._subject_mask(reference_path, prefer_alpha=False)
        preview_mask, preview_bbox = self._subject_mask(preview_path, prefer_alpha=True)

        reference_normalized = self._normalize_mask(reference_mask, reference_bbox)
        preview_normalized = self._normalize_mask(preview_mask, preview_bbox)

        silhouette = self._iou(reference_normalized, preview_normalized)
        proportion = self._proportion_score(reference_bbox, preview_bbox)
        reference_match = self._clamp01((0.75 * silhouette) + (0.25 * proportion))

        return VisualScores(
            silhouette_score=silhouette,
            proportion_score=proportion,
            reference_match=reference_match,
            quality_score=reference_match,
        ).to_dict()

    def _subject_mask(self, path: Path, *, prefer_alpha: bool) -> tuple[Image.Image, tuple[int, int, int, int]]:
        with Image.open(path) as source:
            rgba = source.convert("RGBA")

        if prefer_alpha:
            alpha = rgba.getchannel("A")
            alpha_min, alpha_max = alpha.getextrema()
            if alpha_min < alpha_max:
                mask = alpha.point(lambda value: 255 if value >= 16 else 0, mode="L")
                bbox = mask.getbbox()
                if bbox is not None:
                    return mask, bbox

        rgb = rgba.convert("RGB")
        background = self._estimate_background(rgb)
        pixels = list(rgb.getdata())
        threshold_sq = self.background_distance * self.background_distance
        mask_values = [
            255 if self._distance_sq(pixel, background) >= threshold_sq else 0
            for pixel in pixels
        ]
        mask = Image.new("L", rgb.size)
        mask.putdata(mask_values)
        bbox = mask.getbbox()
        if bbox is None:
            raise ValueError(f"Could not extract a subject silhouette from {path}")
        return mask, bbox

    def _estimate_background(self, image: Image.Image) -> tuple[int, int, int]:
        width, height = image.size
        stride = max(1, min(width, height) // 64)
        samples: list[tuple[int, int, int]] = []

        for x in range(0, width, stride):
            samples.append(image.getpixel((x, 0)))
            samples.append(image.getpixel((x, height - 1)))
        for y in range(0, height, stride):
            samples.append(image.getpixel((0, y)))
            samples.append(image.getpixel((width - 1, y)))

        channels = zip(*samples)
        medians = [int(statistics.median(channel)) for channel in channels]
        return medians[0], medians[1], medians[2]

    def _normalize_mask(self, mask: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
        cropped = mask.crop(bbox)
        width, height = cropped.size
        if width <= 0 or height <= 0:
            raise ValueError("Silhouette bounding box is empty")

        scale = min(self.normalized_size / width, self.normalized_size / height)
        target_width = max(1, round(width * scale))
        target_height = max(1, round(height * scale))
        resized = cropped.resize((target_width, target_height), Image.Resampling.NEAREST)

        canvas = Image.new("L", (self.normalized_size, self.normalized_size), 0)
        offset = (
            (self.normalized_size - target_width) // 2,
            (self.normalized_size - target_height) // 2,
        )
        canvas.paste(resized, offset)
        return canvas

    @staticmethod
    def _iou(first: Image.Image, second: Image.Image) -> float:
        first_values = first.getdata()
        second_values = second.getdata()
        intersection = 0
        union = 0
        for left, right in zip(first_values, second_values):
            left_on = left > 0
            right_on = right > 0
            if left_on or right_on:
                union += 1
                if left_on and right_on:
                    intersection += 1
        if union == 0:
            return 0.0
        return intersection / union

    @staticmethod
    def _proportion_score(
        reference_bbox: tuple[int, int, int, int],
        preview_bbox: tuple[int, int, int, int],
    ) -> float:
        reference_ratio = VisualComparator._bbox_ratio(reference_bbox)
        preview_ratio = VisualComparator._bbox_ratio(preview_bbox)
        if reference_ratio <= 0.0 or preview_ratio <= 0.0:
            return 0.0
        return math.exp(-abs(math.log(preview_ratio / reference_ratio)))

    @staticmethod
    def _bbox_ratio(bbox: tuple[int, int, int, int]) -> float:
        left, top, right, bottom = bbox
        width = max(0, right - left)
        height = max(0, bottom - top)
        return width / height if height else 0.0

    @staticmethod
    def _distance_sq(left: Iterable[int], right: Iterable[int]) -> float:
        return float(sum((a - b) ** 2 for a, b in zip(left, right)))

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

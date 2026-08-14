from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ReferenceAnalysis:
    object_type: str
    overall_style: str
    symmetry_axis: str
    major_parts: list[str]
    priority_order: list[str]
    notes: dict[str, Any] = field(default_factory=dict)


class ReferenceAnalyzer:
    """MVP analyzer contract.

    The first implementation is intentionally conservative: it validates the
    reference and returns the known hot-rod decomposition. A multimodal vision
    backend can replace this class without changing the planner contract.
    """

    def analyze(self, image_path: str | Path) -> ReferenceAnalysis:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(path)

        return ReferenceAnalysis(
            object_type="stylized_hot_rod",
            overall_style="cartoon_meets_mechanical",
            symmetry_axis="x",
            major_parts=[
                "body",
                "cabin",
                "engine",
                "front_grille",
                "front_wheels",
                "rear_wheels",
                "lights",
                "exhaust",
            ],
            priority_order=[
                "blockout",
                "body",
                "wheels",
                "engine",
                "front_details",
                "secondary_details",
                "materials",
            ],
            notes={"source": str(path), "confidence_mode": "seeded-mvp"},
        )

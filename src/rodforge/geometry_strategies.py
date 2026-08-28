from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GeometryStrategy:
    """Declarative identity for a genuinely different construction method."""

    name: str
    family: str
    builder: str
    params: dict[str, Any] = field(default_factory=dict)
    intent: str = ""


STRATEGIES: dict[str, GeometryStrategy] = {
    "chassis_slab": GeometryStrategy(
        name="chassis_slab",
        family="chassis",
        builder="single_box",
        params={"location": (0.0, 0.0, 0.65), "scale": (4.8, 1.7, 0.35)},
        intent="Fast monolithic proportion blockout.",
    ),
    "chassis_rails": GeometryStrategy(
        name="chassis_rails",
        family="chassis",
        builder="rail_frame",
        params={
            "rail_scale": (4.8, 0.22, 0.18),
            "rail_offset": 1.25,
            "z": 0.65,
            "crossmember_scale": (0.16, 1.38, 0.14),
            "crossmember_x": (-3.4, 0.0, 3.4),
        },
        intent="Open ladder-frame silhouette with visible negative space.",
    ),
    "cabin_box": GeometryStrategy(
        name="cabin_box",
        family="cabin",
        builder="single_box",
        params={"location": (0.35, 0.0, 1.55), "scale": (2.1, 1.65, 1.65)},
        intent="Simple compact cab volume.",
    ),
    "cabin_chopped": GeometryStrategy(
        name="cabin_chopped",
        family="cabin",
        builder="stacked_cabin",
        params={
            "lower_location": (0.35, 0.0, 1.28),
            "lower_scale": (2.15, 1.68, 1.10),
            "roof_location": (0.48, 0.0, 2.18),
            "roof_scale": (1.62, 1.58, 0.34),
        },
        intent="Two-mass chopped roof with a lower visual center of gravity.",
    ),
    "wheel_torus": GeometryStrategy(
        name="wheel_torus",
        family="wheel",
        builder="torus_pair",
        params={"segments": 32, "minor_segments": 12},
        intent="Open tire silhouette with a visible inner hole.",
    ),
    "wheel_cylinder": GeometryStrategy(
        name="wheel_cylinder",
        family="wheel",
        builder="cylinder_pair",
        params={"vertices": 32},
        intent="Solid low-cost wheel mass for robust blockout.",
    ),
    "body_box": GeometryStrategy(
        name="body_box",
        family="body",
        builder="single_box",
        params={"location": (0.35, 0.0, 1.45), "scale": (2.25, 1.72, 1.45)},
        intent="Conservative rectangular body envelope.",
    ),
    "body_tapered": GeometryStrategy(
        name="body_tapered",
        family="body",
        builder="tapered_prism",
        params={
            "center": (0.35, 0.0, 1.45),
            "half_length": 2.35,
            "rear_half_width": 1.72,
            "front_half_width": 1.42,
            "bottom_z": -1.25,
            "top_z": 1.45,
        },
        intent="Tapered body envelope that narrows toward the engine/front assembly.",
    ),
    # Combi / Type-2-like stylized van families intentionally stay separate from
    # hot-rod families so cognitive fallbacks do not cross-pollinate silhouettes.
    "van_chassis_floor": GeometryStrategy(
        name="van_chassis_floor",
        family="van_chassis",
        builder="single_box",
        params={"location": (0.0, 0.0, 0.72), "scale": (5.35, 1.78, 0.28)},
        intent="Long flat van floor for a cab-forward microbus silhouette.",
    ),
    "van_chassis_rails": GeometryStrategy(
        name="van_chassis_rails",
        family="van_chassis",
        builder="rail_frame",
        params={
            "rail_scale": (5.25, 0.20, 0.16),
            "rail_offset": 1.32,
            "z": 0.72,
            "crossmember_scale": (0.14, 1.48, 0.13),
            "crossmember_x": (-4.0, -1.4, 1.4, 4.0),
        },
        intent="Long ladder frame alternative for the stylized microbus.",
    ),
    "van_cabin_box": GeometryStrategy(
        name="van_cabin_box",
        family="van_cabin",
        builder="single_box",
        params={"location": (-2.55, 0.0, 2.0), "scale": (2.05, 1.76, 1.55)},
        intent="Cab-forward front cabin mass with upright windshield volume.",
    ),
    "van_cabin_split": GeometryStrategy(
        name="van_cabin_split",
        family="van_cabin",
        builder="stacked_cabin",
        params={
            "lower_location": (-2.35, 0.0, 1.65),
            "lower_scale": (2.20, 1.78, 1.20),
            "roof_location": (-0.25, 0.0, 3.05),
            "roof_scale": (4.85, 1.80, 0.32),
        },
        intent="Split lower/front mass plus long roof to emphasize the microbus profile.",
    ),
    "van_body_box": GeometryStrategy(
        name="van_body_box",
        family="van_body",
        builder="single_box",
        params={"location": (0.0, 0.0, 1.95), "scale": (4.95, 1.78, 1.60)},
        intent="Clean boxy Type-2-like body envelope for topology-first work.",
    ),
    "van_body_tapered": GeometryStrategy(
        name="van_body_tapered",
        family="van_body",
        builder="tapered_prism",
        params={
            "center": (0.0, 0.0, 1.95),
            "half_length": 4.95,
            "rear_half_width": 1.78,
            "front_half_width": 1.64,
            "bottom_z": -1.35,
            "top_z": 1.60,
        },
        intent="Subtle nose taper while preserving the tall compact microbus envelope.",
    ),
}


FAMILY_STRATEGIES: dict[str, tuple[str, ...]] = {
    "chassis": ("chassis_slab", "chassis_rails"),
    "cabin": ("cabin_box", "cabin_chopped"),
    "wheel": ("wheel_torus", "wheel_cylinder"),
    "body": ("body_box", "body_tapered"),
    "van_chassis": ("van_chassis_floor", "van_chassis_rails"),
    "van_cabin": ("van_cabin_box", "van_cabin_split"),
    "van_body": ("van_body_box", "van_body_tapered"),
}


def get_strategy(name: str) -> GeometryStrategy | None:
    return STRATEGIES.get(name)


def candidates_for_family(family: str, current: str) -> list[str]:
    return [name for name in FAMILY_STRATEGIES.get(family, ()) if name != current]

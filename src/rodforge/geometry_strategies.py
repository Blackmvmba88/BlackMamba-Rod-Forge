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
    "front_axle_basic": GeometryStrategy(
        name="front_axle_basic",
        family="front_axle",
        builder="front_axle_assembly",
        params={"x": -1.88, "half_width": 1.72, "z": 0.76},
        intent="Readable beam axle, steering tie rod and kingpins without engineering-level detail.",
    ),
    "transmission_basic": GeometryStrategy(
        name="transmission_basic",
        family="transmission",
        builder="transmission_assembly",
        params={"location": (-0.35, 0.0, 0.82)},
        intent="Simple bell housing and gearbox mass behind the exposed engine.",
    ),
    "wheel_mechanics_basic": GeometryStrategy(
        name="wheel_mechanics_basic",
        family="wheel_mechanics",
        builder="wheel_detail_pass",
        params={"front_x": -1.88, "rear_x": 1.82, "front_z": 0.76, "rear_z": 0.90},
        intent="Large hubs and brake discs that read clearly at tutorial scale.",
    ),
    "driveline_basic": GeometryStrategy(
        name="driveline_basic",
        family="driveline",
        builder="driveline_assembly",
        params={"transmission_x": 0.15, "rear_axle_x": 1.82, "z": 0.68},
        intent="Visible driveshaft and simple rear differential connecting the major masses.",
    ),
}


FAMILY_STRATEGIES: dict[str, tuple[str, ...]] = {
    "chassis": ("chassis_slab", "chassis_rails"),
    "cabin": ("cabin_box", "cabin_chopped"),
    "wheel": ("wheel_torus", "wheel_cylinder"),
    "body": ("body_box", "body_tapered"),
}


def get_strategy(name: str) -> GeometryStrategy | None:
    return STRATEGIES.get(name)


def candidates_for_family(family: str, current: str) -> list[str]:
    return [name for name in FAMILY_STRATEGIES.get(family, ()) if name != current]

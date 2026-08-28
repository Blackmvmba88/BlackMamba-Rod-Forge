from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VehicleProfile:
    """Stable vehicle identity shared by planning, cognition and Blender execution."""

    name: str
    project_name: str
    body_style: str
    reference_asset: str
    reference_dimensions_m: tuple[float, float, float] | None
    required_parts: tuple[str, ...]
    notes: str = ""


PROFILES: dict[str, VehicleProfile] = {
    "hotrod": VehicleProfile(
        name="hotrod",
        project_name="blackmamba_hotrod",
        body_style="1930s_chopped_pickup_hotrod",
        reference_asset="hotrod.blend",
        reference_dimensions_m=(2.710, 1.710, 1.260),
        required_parts=(
            "chassis",
            "chopped_cabin",
            "front_wheels",
            "oversized_rear_wheels",
            "exposed_v8",
            "blower",
            "vertical_grille",
            "round_headlights",
            "side_exhaust",
            "body_shell",
            "materials",
        ),
        notes="Blueprint envelope is authoritative; keep exposed mechanical negative space.",
    ),
    "combi": VehicleProfile(
        name="combi",
        project_name="blackmamba_combi",
        body_style="stylized_type2_microbus",
        reference_asset="COMBI_TOPOLOGIA_PRO.blend",
        reference_dimensions_m=None,
        required_parts=(
            "chassis_floor",
            "cab_forward_cabin",
            "front_wheels",
            "rear_wheels",
            "boxy_body_shell",
            "front_face",
            "windshield",
            "side_windows",
            "sliding_door",
            "bumpers",
            "round_headlights",
            "mirrors",
            "materials",
        ),
        notes="Topology-first profile; dimensions remain reference-driven until the .blend envelope is measured.",
    ),
}

ALIASES = {
    "hot-rod": "hotrod",
    "rod": "hotrod",
    "van": "combi",
    "microbus": "combi",
    "type2": "combi",
    "type-2": "combi",
}


def get_vehicle_profile(name: str) -> VehicleProfile:
    key = str(name).strip().lower()
    key = ALIASES.get(key, key)
    try:
        return PROFILES[key]
    except KeyError as exc:
        available = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unknown vehicle profile {name!r}; available: {available}") from exc

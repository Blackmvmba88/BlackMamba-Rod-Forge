from __future__ import annotations

from .geometry_strategies import candidates_for_family
from .schemas import Criticality, ProjectState, Task
from .vehicle_profiles import VehicleProfile, get_vehicle_profile


DEFAULT_FALLBACKS = [
    "retry_same",
    "split_task",
    "simplify_geometry",
    "alternate_method",
    "rebuild_from_checkpoint",
]


def _task(
    task_id: str,
    name: str,
    objective: str,
    deps: list[str] | None = None,
    criticality: Criticality = Criticality.NORMAL,
    max_attempts: int = 3,
    strategy: str = "primitive_blockout",
    *,
    part_family: str | None = None,
) -> Task:
    candidates = candidates_for_family(part_family, strategy) if part_family else []
    fallbacks = ["retry_same", *candidates]
    fallbacks.extend(item for item in DEFAULT_FALLBACKS if item not in fallbacks)

    metadata = {
        "cognitive_signature": task_id,
        "cognitive_metric": "improvement_score",
    }
    if part_family:
        metadata["part_family"] = part_family
    if candidates:
        metadata["cognitive_candidates"] = candidates

    return Task(
        task_id=task_id,
        name=name,
        objective=objective,
        dependencies=deps or [],
        strategy=strategy,
        success_criteria={"object_exists": True, "named": True},
        fallback_strategies=fallbacks,
        criticality=criticality,
        max_attempts=max_attempts,
        metadata=metadata,
    )


def _bind_profile(state: ProjectState, profile: VehicleProfile) -> ProjectState:
    for task in state.tasks.values():
        task.metadata["vehicle_profile"] = profile.name
        task.metadata["body_style"] = profile.body_style
        task.metadata["reference_asset"] = profile.reference_asset
        if profile.reference_dimensions_m is not None:
            task.metadata["reference_dimensions_m"] = list(profile.reference_dimensions_m)
    return state


def build_hotrod_plan(project_name: str = "blackmamba_hotrod") -> ProjectState:
    tasks = [
        _task(
            "chassis_blockout",
            "Chassis blockout",
            "Create the vehicle base proportions.",
            criticality=Criticality.CRITICAL,
            max_attempts=5,
            strategy="chassis_slab",
            part_family="chassis",
        ),
        _task(
            "cabin_blockout",
            "Cabin blockout",
            "Create compact chopped-cab volume.",
            ["chassis_blockout"],
            Criticality.CRITICAL,
            5,
            "cabin_box",
            part_family="cabin",
        ),
        _task(
            "engine_volume",
            "Engine volume",
            "Place the exposed engine primary mass.",
            ["chassis_blockout"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "front_wheels",
            "Front wheels",
            "Create and position front wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
        ),
        _task(
            "rear_wheels",
            "Rear wheels",
            "Create oversized rear wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
        ),
        _task(
            "body_shell",
            "Body shell",
            "Refine cabin, roof and side panels.",
            ["cabin_blockout", "front_wheels", "rear_wheels"],
            Criticality.CRITICAL,
            5,
            "body_box",
            part_family="body",
        ),
        _task(
            "front_grille",
            "Front grille",
            "Construct tall vertical grille and support.",
            ["engine_volume", "front_wheels"],
            strategy="front_assembly",
        ),
        _task(
            "headlights",
            "Headlights",
            "Create symmetric round headlights.",
            ["front_grille"],
            strategy="front_assembly",
        ),
        _task(
            "engine_block",
            "Engine block",
            "Refine exposed V8-inspired engine block.",
            ["engine_volume", "body_shell"],
            Criticality.HIGH,
            4,
            "engine_detail",
        ),
        _task(
            "blower",
            "Blower",
            "Create supercharger and intake scoop.",
            ["engine_block"],
            strategy="engine_detail",
        ),
        _task(
            "exhaust",
            "Exhaust",
            "Create exposed exhaust/header forms.",
            ["engine_block"],
            strategy="engine_detail",
        ),
        _task(
            "secondary_details",
            "Secondary details",
            "Add mirrors, handles, trim and mechanical accents.",
            ["body_shell", "headlights", "blower", "exhaust"],
            strategy="detail_pass",
        ),
        _task(
            "materials",
            "Base materials",
            "Assign orange paint, exposed metal and tire materials.",
            ["secondary_details"],
            strategy="materials",
        ),
        _task(
            "preview",
            "Preview render",
            "Produce evidence render of the assembled vehicle.",
            ["materials"],
            strategy="preview",
        ),
    ]
    profile = get_vehicle_profile("hotrod")
    return _bind_profile(
        ProjectState(project_name=project_name, tasks={task.task_id: task for task in tasks}),
        profile,
    )


def build_combi_plan(project_name: str = "blackmamba_combi") -> ProjectState:
    """Build a topology-first plan for the stylized Combi / Type-2-like microbus."""

    tasks = [
        _task(
            "chassis_blockout",
            "Combi chassis floor",
            "Establish the long flat floor and wheelbase envelope.",
            criticality=Criticality.CRITICAL,
            max_attempts=5,
            strategy="van_chassis_floor",
            part_family="van_chassis",
        ),
        _task(
            "cabin_blockout",
            "Cab-forward cabin",
            "Establish the upright front cabin and roofline mass.",
            ["chassis_blockout"],
            Criticality.CRITICAL,
            5,
            "van_cabin_box",
            part_family="van_cabin",
        ),
        _task(
            "front_wheels",
            "Front wheels",
            "Create and position the front wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
        ),
        _task(
            "rear_wheels",
            "Rear wheels",
            "Create and position the rear wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
        ),
        _task(
            "body_shell",
            "Combi body shell",
            "Create the clean boxy shell before openings and trim.",
            ["cabin_blockout", "front_wheels", "rear_wheels"],
            Criticality.CRITICAL,
            5,
            "van_body_box",
            part_family="van_body",
        ),
        _task(
            "front_face",
            "Front face",
            "Build the flat nose, center emblem area and bumper relationship.",
            ["body_shell"],
            Criticality.HIGH,
            4,
            "front_assembly",
        ),
        _task(
            "windshield",
            "Windshield",
            "Define the split/upright windshield opening and border.",
            ["front_face"],
            Criticality.HIGH,
            4,
            "detail_pass",
        ),
        _task(
            "side_windows",
            "Side windows",
            "Lay out the side glazing rhythm while preserving topology loops.",
            ["body_shell"],
            Criticality.HIGH,
            4,
            "detail_pass",
        ),
        _task(
            "sliding_door",
            "Sliding door",
            "Define the side sliding-door seam and handle region.",
            ["body_shell", "side_windows"],
            Criticality.HIGH,
            4,
            "detail_pass",
        ),
        _task(
            "bumpers",
            "Bumpers",
            "Create front and rear bumper masses with clean separation.",
            ["body_shell"],
            strategy="front_assembly",
        ),
        _task(
            "headlights",
            "Round headlights",
            "Create symmetric circular front lamps and bezels.",
            ["front_face"],
            strategy="front_assembly",
        ),
        _task(
            "mirrors",
            "Mirrors",
            "Add compact side mirrors after glazing and front proportions are stable.",
            ["windshield", "side_windows", "headlights"],
            strategy="detail_pass",
        ),
        _task(
            "secondary_details",
            "Secondary details",
            "Add handles, trim, panel seams and simplified underbody accents.",
            ["sliding_door", "bumpers", "mirrors"],
            strategy="detail_pass",
        ),
        _task(
            "materials",
            "Base materials",
            "Assign body paint, glass, chrome/metal and tire materials.",
            ["secondary_details"],
            strategy="materials",
        ),
        _task(
            "preview",
            "Preview render",
            "Produce evidence render of the assembled Combi.",
            ["materials"],
            strategy="preview",
        ),
    ]
    profile = get_vehicle_profile("combi")
    return _bind_profile(
        ProjectState(project_name=project_name, tasks={task.task_id: task for task in tasks}),
        profile,
    )


def build_vehicle_plan(profile_name: str, project_name: str | None = None) -> ProjectState:
    """Dispatch a plan from a stable vehicle profile name or alias."""

    profile = get_vehicle_profile(profile_name)
    resolved_project_name = project_name or profile.project_name
    if profile.name == "hotrod":
        return build_hotrod_plan(resolved_project_name)
    if profile.name == "combi":
        return build_combi_plan(resolved_project_name)
    raise AssertionError(f"Unhandled registered vehicle profile: {profile.name}")

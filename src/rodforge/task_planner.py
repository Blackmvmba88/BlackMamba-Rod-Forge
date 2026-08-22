from __future__ import annotations

from .geometry_strategies import candidates_for_family
from .schemas import Criticality, ProjectState, Task


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
            "mechanical_systems",
            "Mechanical systems",
            "Derive brakes, hubs, suspension, steering, axle, driveshaft and engine mounts from generated wheel geometry.",
            ["chassis_blockout", "engine_volume", "front_wheels", "rear_wheels"],
            Criticality.HIGH,
            4,
            "mechanical_systems",
        ),
        _task(
            "body_shell",
            "Body shell",
            "Refine cabin, roof and side panels around the established rolling and mechanical package.",
            ["cabin_blockout", "front_wheels", "rear_wheels", "mechanical_systems"],
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
    return ProjectState(project_name=project_name, tasks={task.task_id: task for task in tasks})

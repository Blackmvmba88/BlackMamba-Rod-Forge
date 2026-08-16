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
    pipeline_stage: str = "details",
    checkpoint: bool = False,
) -> Task:
    candidates = candidates_for_family(part_family, strategy) if part_family else []
    fallbacks = ["retry_same", *candidates]
    fallbacks.extend(item for item in DEFAULT_FALLBACKS if item not in fallbacks)

    metadata = {
        "cognitive_signature": task_id,
        "cognitive_metric": "improvement_score",
        "pipeline_stage": pipeline_stage,
        "tutorial_step": task_id,
    }
    if checkpoint:
        metadata["checkpoint"] = True
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
            pipeline_stage="blockout",
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
            pipeline_stage="blockout",
        ),
        _task(
            "engine_volume",
            "Engine volume",
            "Place the exposed engine primary mass.",
            ["chassis_blockout"],
            Criticality.HIGH,
            4,
            pipeline_stage="blockout",
        ),
        _task(
            "front_wheels",
            "Front wheels",
            "Create and position front wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
            pipeline_stage="blockout",
        ),
        _task(
            "rear_wheels",
            "Rear wheels",
            "Create oversized rear wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
            pipeline_stage="blockout",
            checkpoint=True,
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
            pipeline_stage="chassis_body",
        ),
        _task(
            "front_axle",
            "Simplified front axle",
            "Add a readable front beam, steering link and simple suspension.",
            ["chassis_blockout", "front_wheels"],
            Criticality.HIGH,
            4,
            "front_axle_basic",
            pipeline_stage="chassis_body",
            checkpoint=True,
        ),
        _task(
            "front_grille",
            "Front grille",
            "Construct tall vertical grille and support.",
            ["engine_volume", "front_wheels"],
            strategy="front_assembly",
            pipeline_stage="chassis_body",
        ),
        _task(
            "headlights",
            "Headlights",
            "Create symmetric round headlights.",
            ["front_grille"],
            strategy="front_assembly",
            pipeline_stage="chassis_body",
        ),
        _task(
            "engine_block",
            "Engine block",
            "Refine exposed V8-inspired engine block.",
            ["engine_volume", "body_shell"],
            Criticality.HIGH,
            4,
            "engine_detail",
            pipeline_stage="engine",
        ),
        _task(
            "blower",
            "Blower",
            "Create supercharger and intake scoop.",
            ["engine_block"],
            strategy="engine_detail",
            pipeline_stage="engine",
        ),
        _task(
            "exhaust",
            "Exhaust",
            "Create exposed exhaust/header forms.",
            ["engine_block"],
            strategy="engine_detail",
            pipeline_stage="engine",
        ),
        _task(
            "simple_transmission",
            "Simplified transmission",
            "Add a family-friendly gearbox mass behind and below the engine.",
            ["engine_block", "chassis_blockout"],
            strategy="transmission_basic",
            pipeline_stage="engine",
            checkpoint=True,
        ),
        _task(
            "wheel_mechanics",
            "Wheel mechanical pass",
            "Add readable rims, hubs, brakes and a simple tire pattern.",
            ["front_axle", "front_wheels", "rear_wheels"],
            Criticality.HIGH,
            4,
            "wheel_mechanics_basic",
            pipeline_stage="wheels",
            checkpoint=True,
        ),
        _task(
            "simple_driveline",
            "Simplified driveline",
            "Connect transmission to a basic rear differential with a visible driveshaft.",
            ["simple_transmission", "rear_wheels"],
            strategy="driveline_basic",
            pipeline_stage="details",
        ),
        _task(
            "secondary_details",
            "Secondary details",
            "Add mirrors, handles, trim and mechanical accents.",
            ["body_shell", "headlights", "blower", "exhaust", "wheel_mechanics", "simple_driveline"],
            strategy="detail_pass",
            pipeline_stage="details",
            checkpoint=True,
        ),
        _task(
            "materials",
            "Base materials",
            "Assign orange paint, exposed metal and tire materials.",
            ["secondary_details"],
            strategy="materials",
            pipeline_stage="details",
        ),
        _task(
            "preview",
            "Preview render",
            "Produce evidence render of the assembled vehicle.",
            ["materials"],
            strategy="preview",
            pipeline_stage="details",
            checkpoint=True,
        ),
    ]
    return ProjectState(
        project_name=project_name,
        tasks={task.task_id: task for task in tasks},
        metadata={
            "pipeline_stages": ["blockout", "chassis_body", "engine", "wheels", "details"],
            "tutorial_capture": True,
        },
    )

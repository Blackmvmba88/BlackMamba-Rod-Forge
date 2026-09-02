from __future__ import annotations

from typing import Any

from .geometry_strategies import candidates_for_family
from .schemas import Criticality, ProjectState, Task
from .vehicle_geometry import VehicleGeometry


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
    geometry_constraints: dict[str, Any] | None = None,
) -> Task:
    candidates = candidates_for_family(part_family, strategy) if part_family else []
    fallbacks = ["retry_same", *candidates]
    fallbacks.extend(item for item in DEFAULT_FALLBACKS if item not in fallbacks)

    metadata: dict[str, Any] = {
        "cognitive_signature": task_id,
        "cognitive_metric": "improvement_score",
    }
    if part_family:
        metadata["part_family"] = part_family
    if candidates:
        metadata["cognitive_candidates"] = candidates
    if geometry_constraints:
        metadata["geometry_constraints"] = geometry_constraints

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


def _constraints(geometry: VehicleGeometry | None, task_id: str) -> dict[str, Any]:
    return geometry.constraints_for(task_id) if geometry is not None else {}


def build_hotrod_plan(
    project_name: str = "blackmamba_hotrod",
    *,
    vehicle_geometry: VehicleGeometry | None = None,
) -> ProjectState:
    tasks = [
        _task(
            "chassis_blockout",
            "Chassis blockout",
            "Create the vehicle base proportions.",
            criticality=Criticality.CRITICAL,
            max_attempts=5,
            strategy="chassis_slab",
            part_family="chassis",
            geometry_constraints=_constraints(vehicle_geometry, "chassis_blockout"),
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
            geometry_constraints=_constraints(vehicle_geometry, "cabin_blockout"),
        ),
        _task(
            "engine_volume",
            "Engine volume",
            "Place the exposed engine primary mass.",
            ["chassis_blockout"],
            Criticality.HIGH,
            4,
            geometry_constraints=_constraints(vehicle_geometry, "engine_volume"),
        ),
        _task(
            "front_wheels",
            "Front wheels",
            "Create and position front wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
            geometry_constraints=_constraints(vehicle_geometry, "front_wheels"),
        ),
        _task(
            "rear_wheels",
            "Rear wheels",
            "Create oversized rear wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
            geometry_constraints=_constraints(vehicle_geometry, "rear_wheels"),
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
            geometry_constraints=_constraints(vehicle_geometry, "body_shell"),
        ),
        _task(
            "front_hubs_brakes",
            "Front hubs and brakes",
            "Create front hubs, brake interfaces and wheel attachment geometry.",
            ["chassis_blockout", "front_wheels"],
            Criticality.HIGH,
            4,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "front_hubs_brakes"),
        ),
        _task(
            "front_suspension",
            "Front suspension",
            "Build the double-wishbone front suspension around the wheel hubs.",
            ["chassis_blockout", "front_hubs_brakes"],
            Criticality.HIGH,
            5,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "front_suspension"),
        ),
        _task(
            "steering",
            "Steering system",
            "Place rack-and-pinion steering and preserve Ackermann intent.",
            ["front_suspension"],
            Criticality.HIGH,
            4,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "steering"),
        ),
        _task(
            "rear_axle",
            "Rear axle and differential",
            "Create the driven rear axle and differential between the rear wheels.",
            ["chassis_blockout", "rear_wheels"],
            Criticality.HIGH,
            4,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "rear_axle"),
        ),
        _task(
            "rear_links",
            "Rear locating links",
            "Locate the rear axle while preserving driveshaft clearance.",
            ["chassis_blockout", "rear_axle"],
            Criticality.HIGH,
            4,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "rear_links"),
        ),
        _task(
            "front_grille",
            "Front grille",
            "Construct tall vertical grille and support.",
            ["engine_volume", "front_wheels"],
            strategy="front_assembly",
            geometry_constraints=_constraints(vehicle_geometry, "front_grille"),
        ),
        _task(
            "headlights",
            "Headlights",
            "Create symmetric round headlights.",
            ["front_grille"],
            strategy="front_assembly",
            geometry_constraints=_constraints(vehicle_geometry, "headlights"),
        ),
        _task(
            "engine_block",
            "Engine block",
            "Refine exposed V8-inspired engine block.",
            ["engine_volume", "body_shell"],
            Criticality.HIGH,
            4,
            "engine_detail",
            geometry_constraints=_constraints(vehicle_geometry, "engine_block"),
        ),
        _task(
            "engine_mounts",
            "Engine mounts",
            "Anchor the engine block to the chassis with explicit mount geometry.",
            ["chassis_blockout", "engine_block"],
            Criticality.HIGH,
            4,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "engine_mounts"),
        ),
        _task(
            "blower",
            "Blower",
            "Create supercharger and intake scoop.",
            ["engine_block"],
            strategy="engine_detail",
            geometry_constraints=_constraints(vehicle_geometry, "blower"),
        ),
        _task(
            "exhaust",
            "Exhaust",
            "Create exposed exhaust/header forms.",
            ["engine_block"],
            strategy="engine_detail",
            geometry_constraints=_constraints(vehicle_geometry, "exhaust"),
        ),
        _task(
            "driveshaft",
            "Driveshaft",
            "Connect the engine/transmission axis to the rear differential.",
            ["engine_block", "engine_mounts", "rear_axle"],
            Criticality.HIGH,
            4,
            "detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "driveshaft"),
        ),
        _task(
            "secondary_details",
            "Secondary details",
            "Add mirrors, handles, trim and remaining mechanical accents.",
            [
                "body_shell",
                "headlights",
                "blower",
                "exhaust",
                "steering",
                "rear_links",
                "driveshaft",
            ],
            strategy="detail_pass",
            geometry_constraints=_constraints(vehicle_geometry, "secondary_details"),
        ),
        _task(
            "materials",
            "Base materials",
            "Assign orange paint, exposed metal and tire materials.",
            ["secondary_details"],
            strategy="materials",
            geometry_constraints=_constraints(vehicle_geometry, "materials"),
        ),
        _task(
            "preview",
            "Preview render",
            "Produce evidence render of the assembled vehicle.",
            ["materials"],
            strategy="preview",
            geometry_constraints=_constraints(vehicle_geometry, "preview"),
        ),
    ]
    state = ProjectState(project_name=project_name, tasks={task.task_id: task for task in tasks})
    if vehicle_geometry is not None:
        state.metadata["vehicle_geometry"] = vehicle_geometry.to_metadata()
    return state

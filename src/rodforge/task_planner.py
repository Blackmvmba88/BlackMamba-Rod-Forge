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
            "Create the 2710 x 1710 x 1260 mm vehicle envelope and primary frame proportions.",
            criticality=Criticality.CRITICAL,
            max_attempts=5,
            strategy="chassis_slab",
            part_family="chassis",
        ),
        _task(
            "cabin_blockout",
            "Cabin blockout",
            "Create the compact chopped 1930s pickup cabin volume.",
            ["chassis_blockout"],
            Criticality.CRITICAL,
            5,
            "cabin_box",
            part_family="cabin",
        ),
        _task(
            "engine_volume",
            "Front-mid engine volume",
            "Reserve the exposed longitudinal V8 mass as far rearward as practical while preserving the hot-rod silhouette.",
            ["chassis_blockout"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "front_wheels",
            "Front wheel package",
            "Create and position the 580 x 200 mm, 17-inch, 5-lug front wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
        ),
        _task(
            "rear_wheels",
            "Rear wheel package",
            "Create and position the 680 x 320 mm, 20-inch, three-piece deep-dish rear wheel pair.",
            ["chassis_blockout"],
            Criticality.HIGH,
            strategy="wheel_torus",
            part_family="wheel",
        ),
        _task(
            "front_hubs_brakes",
            "Front hubs and brakes",
            "Model hub-centric 5-lug front hubs with a 330 mm ventilated two-piece rotor envelope and 4-piston caliper envelope.",
            ["front_wheels"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "rear_hubs_brakes",
            "Rear hubs and brakes",
            "Model hub-centric 5-lug rear hubs with a 355 x 28 mm ventilated rotor, 4-piston caliper and parking-brake envelope.",
            ["rear_wheels"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "front_uprights_wishbones",
            "Front uprights and wishbones",
            "Build independent double-wishbone front suspension around the hub, including adjustable track-width architecture.",
            ["chassis_blockout", "front_hubs_brakes"],
            Criticality.CRITICAL,
            5,
        ),
        _task(
            "front_steering",
            "Rack steering geometry",
            "Place rack-and-pinion steering, tie rods and steering arms for Ackermann intent with minimized bump steer.",
            ["front_uprights_wishbones"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "front_pushrod",
            "Front pushrod and rocker",
            "Package pushrods, rockers and inboard dampers around a 0.75 target motion ratio.",
            ["front_uprights_wishbones"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "rear_uprights_wishbones",
            "Rear uprights and wishbones",
            "Build independent rear double-wishbone suspension around the rear hub and CV half-shaft envelope.",
            ["chassis_blockout", "rear_hubs_brakes"],
            Criticality.CRITICAL,
            5,
        ),
        _task(
            "rear_toe_links",
            "Rear toe links",
            "Add independently adjustable rear toe links and preserve a 20-40 percent anti-squat exploration range.",
            ["rear_uprights_wishbones"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "rear_pushrod",
            "Rear pushrod and rocker",
            "Package rear pushrods, rockers and inboard dampers while keeping the rear roll center above the front target.",
            ["rear_uprights_wishbones"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "engine_block",
            "Engine block",
            "Refine the exposed longitudinal V8-inspired engine block inside the front-mid package.",
            ["engine_volume", "front_uprights_wishbones"],
            Criticality.HIGH,
            4,
            "engine_detail",
        ),
        _task(
            "blower",
            "Three-intake blower",
            "Create the exposed supercharger and three-intake scoop visual signature.",
            ["engine_block"],
            strategy="engine_detail",
        ),
        _task(
            "exhaust",
            "Exhaust",
            "Create exposed exhaust/header forms around the validated suspension and frame envelopes.",
            ["engine_block"],
            strategy="engine_detail",
        ),
        _task(
            "rear_transaxle",
            "Rear transaxle and LSD",
            "Package the rear transaxle and LSD with provisional 3.73 final-drive target and 3.55/3.91 alternatives retained.",
            ["engine_block", "rear_uprights_wishbones"],
            Criticality.CRITICAL,
            5,
        ),
        _task(
            "half_shafts",
            "Rear CV half-shafts",
            "Connect the transaxle to each rear hub with independent CV half-shaft envelopes and viable articulation angles.",
            ["rear_transaxle", "rear_hubs_brakes"],
            Criticality.HIGH,
            4,
        ),
        _task(
            "modular_subframes",
            "Modular front and rear structures",
            "Create removable front module and rear transaxle/suspension subframe with triangulated pickup load paths.",
            ["front_uprights_wishbones", "front_steering", "rear_uprights_wishbones", "rear_transaxle"],
            Criticality.CRITICAL,
            5,
        ),
        _task(
            "body_shell",
            "Body shell",
            "Fit chopped roof, side panels, hood and rear box around the mechanical envelopes instead of inventing the mechanics from bodywork.",
            ["cabin_blockout", "front_wheels", "rear_wheels", "modular_subframes", "engine_block"],
            Criticality.CRITICAL,
            5,
            "body_box",
            part_family="body",
        ),
        _task(
            "front_grille",
            "Front grille",
            "Construct the tall vertical grille and supports around the front module and engine package.",
            ["body_shell", "front_steering"],
            strategy="front_assembly",
        ),
        _task(
            "headlights",
            "Headlights",
            "Create symmetric round headlights without interfering with steering or suspension travel envelopes.",
            ["front_grille"],
            strategy="front_assembly",
        ),
        _task(
            "telemetry_packaging",
            "Telemetry packaging",
            "Reserve sensor locations for wheel speed, suspension travel, steering angle, temperatures and vehicle acceleration.",
            ["front_hubs_brakes", "rear_hubs_brakes", "modular_subframes"],
            Criticality.NORMAL,
            3,
        ),
        _task(
            "secondary_details",
            "Secondary details",
            "Add mirrors, handles, trim and mechanical accents without violating the mechanical envelopes.",
            ["body_shell", "headlights", "blower", "exhaust", "half_shafts", "telemetry_packaging"],
            strategy="detail_pass",
        ),
        _task(
            "materials",
            "Base materials",
            "Assign burnt-orange paint, aged silver, exposed metal, brake and tire materials.",
            ["secondary_details"],
            strategy="materials",
        ),
        _task(
            "preview",
            "Preview render",
            "Produce evidence render of the assembled vehicle with the complete mechanical package represented.",
            ["materials"],
            strategy="preview",
        ),
    ]
    state = ProjectState(project_name=project_name, tasks={task.task_id: task for task in tasks})
    state.metadata["mechanical_architecture"] = "hotrod_mechanical_v1"
    state.metadata["mass_distribution_target"] = {"front_percent": 48, "rear_percent": 52}
    state.metadata["design_rule"] = "mechanics_define_envelopes_body_fits_around_them"
    return state

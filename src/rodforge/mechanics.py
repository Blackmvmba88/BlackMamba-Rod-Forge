from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from typing import Any, Sequence


Point3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class MechanicalDimensions:
    front_axle_x: float
    rear_axle_x: float
    center_y: float
    front_z: float
    rear_z: float
    front_half_track: float
    rear_half_track: float
    wheelbase: float


def derive_mechanical_dimensions(
    front_left: Sequence[float],
    front_right: Sequence[float],
    rear_left: Sequence[float],
    rear_right: Sequence[float],
) -> MechanicalDimensions:
    """Derive the core mechanical envelope from four wheel centers.

    Rod Forge uses X as longitudinal, Y as lateral and Z as vertical in the
    procedural executor. No dimensions are copied from the source `.blend`.
    """

    fl = tuple(float(v) for v in front_left)
    fr = tuple(float(v) for v in front_right)
    rl = tuple(float(v) for v in rear_left)
    rr = tuple(float(v) for v in rear_right)

    front_x = (fl[0] + fr[0]) * 0.5
    rear_x = (rl[0] + rr[0]) * 0.5
    center_y = (fl[1] + fr[1] + rl[1] + rr[1]) * 0.25
    front_z = (fl[2] + fr[2]) * 0.5
    rear_z = (rl[2] + rr[2]) * 0.5
    front_half_track = abs(fr[1] - fl[1]) * 0.5
    rear_half_track = abs(rr[1] - rl[1]) * 0.5
    wheelbase = abs(rear_x - front_x)

    if wheelbase <= 1e-6:
        raise ValueError("Mechanical layout requires distinct front and rear axle positions")
    if front_half_track <= 1e-6 or rear_half_track <= 1e-6:
        raise ValueError("Mechanical layout requires non-zero front and rear track width")

    return MechanicalDimensions(
        front_axle_x=front_x,
        rear_axle_x=rear_x,
        center_y=center_y,
        front_z=front_z,
        rear_z=rear_z,
        front_half_track=front_half_track,
        rear_half_track=rear_half_track,
        wheelbase=wheelbase,
    )


def _wheel_center(bpy: Any, name: str) -> Point3:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Mechanical systems require wheel object {name!r}")
    p = obj.matrix_world.translation
    return (float(p.x), float(p.y), float(p.z))


def build_mechanical_systems(bpy: Any, task_id: str = "mechanical_systems") -> Any:
    """Build procedural suspension, steering, brakes and drivetrain from RF wheels.

    All generated objects share the executor task prefix so `_clear_task_objects`
    can remove the complete pass before a retry or counterfactual rebuild.
    """

    from mathutils import Vector  # type: ignore

    prefix = f"RF_{task_id}"
    fl = _wheel_center(bpy, "RF_front_wheels")
    fr = _wheel_center(bpy, "RF_front_wheels__R")
    rl = _wheel_center(bpy, "RF_rear_wheels")
    rr = _wheel_center(bpy, "RF_rear_wheels__R")
    dims = derive_mechanical_dimensions(fl, fr, rl, rr)

    created: list[Any] = []

    def add_cylinder(name: str, p1: Sequence[float], p2: Sequence[float], radius: float, vertices: int = 20) -> Any:
        a = Vector(tuple(float(v) for v in p1))
        b = Vector(tuple(float(v) for v in p2))
        vec = b - a
        if vec.length <= 1e-6:
            raise ValueError(f"Zero-length mechanical member: {name}")
        mid = (a + b) * 0.5
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=vec.length, location=mid)
        obj = bpy.context.active_object
        obj.name = f"{prefix}__{name}"
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(vec.normalized())
        obj.rotation_mode = "XYZ"
        created.append(obj)
        return obj

    def add_box(name: str, location: Sequence[float], scale: Sequence[float]) -> Any:
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=tuple(float(v) for v in location))
        obj = bpy.context.active_object
        obj.name = f"{prefix}__{name}"
        obj.scale = tuple(float(v) for v in scale)
        created.append(obj)
        return obj

    def add_sphere(name: str, location: Sequence[float], scale: Sequence[float]) -> Any:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=tuple(float(v) for v in location))
        obj = bpy.context.active_object
        obj.name = f"{prefix}__{name}"
        obj.scale = tuple(float(v) for v in scale)
        created.append(obj)
        return obj

    # A small invisible-looking structural marker is the task's representative object.
    primary = add_box("root", (dims.front_axle_x, dims.center_y, dims.front_z - 0.28), (0.10, 0.10, 0.10))
    primary.name = prefix

    wheel_centers = {
        "Front_L": Vector(fl),
        "Front_R": Vector(fr),
        "Rear_L": Vector(rl),
        "Rear_R": Vector(rr),
    }

    # Brakes, hubs and 5-lug hardware. Wheel plane is X/Z; axle axis is Y.
    for label, center in wheel_centers.items():
        side_sign = -1.0 if center.y < dims.center_y else 1.0
        disc_radius = 0.46 if label.startswith("Front") else 0.56
        add_cylinder(f"{label}_BrakeDisc", center + Vector((0.0, -0.055, 0.0)), center + Vector((0.0, 0.055, 0.0)), disc_radius, 36)
        add_cylinder(f"{label}_Hub", center + Vector((0.0, -0.12, 0.0)), center + Vector((0.0, 0.12, 0.0)), 0.20, 28)
        bolt_circle = disc_radius * 0.30
        axial = side_sign * 0.13
        for index in range(5):
            angle = pi * 0.5 + index * (2.0 * pi / 5.0)
            lug = center + Vector((cos(angle) * bolt_circle, axial, sin(angle) * bolt_circle))
            add_cylinder(
                f"{label}_Lug_{index + 1}",
                lug + Vector((0.0, -0.055, 0.0)),
                lug + Vector((0.0, 0.055, 0.0)),
                0.038,
                12,
            )
        add_box(
            f"{label}_Caliper",
            center + Vector((0.18, -side_sign * 0.15, 0.16)),
            (0.10, 0.10, 0.20),
        )

    # Front double wishbones, knuckles, coilovers and rack/tie rods.
    rack_x = dims.front_axle_x + dims.wheelbase * 0.08
    rack_z = dims.front_z + 0.02
    rack_half = dims.front_half_track * 0.42
    add_cylinder(
        "SteeringRack",
        (rack_x, dims.center_y - rack_half, rack_z),
        (rack_x, dims.center_y + rack_half, rack_z),
        0.055,
        24,
    )
    cross_x = dims.front_axle_x + dims.wheelbase * 0.11
    add_cylinder(
        "FrontCrossmember",
        (cross_x, dims.center_y - dims.front_half_track * 0.62, dims.front_z - 0.28),
        (cross_x, dims.center_y + dims.front_half_track * 0.62, dims.front_z - 0.28),
        0.085,
        24,
    )

    for side_name, center in (("L", Vector(fl)), ("R", Vector(fr))):
        side_sign = -1.0 if center.y < dims.center_y else 1.0
        knuckle_low = center + Vector((0.0, 0.0, -0.32))
        knuckle_high = center + Vector((0.0, 0.0, 0.32))
        add_cylinder(f"Front_{side_name}_Knuckle", knuckle_low, knuckle_high, 0.065)

        inner_y_upper = dims.center_y + side_sign * dims.front_half_track * 0.44
        inner_y_lower = dims.center_y + side_sign * dims.front_half_track * 0.48
        upper_outer = center + Vector((0.0, -side_sign * 0.08, 0.24))
        lower_outer = center + Vector((0.0, -side_sign * 0.08, -0.24))

        for suffix, x_shift in (("A", -0.16), ("B", 0.18)):
            add_cylinder(
                f"Front_{side_name}_UpperArm_{suffix}",
                upper_outer,
                (dims.front_axle_x + x_shift, inner_y_upper, dims.front_z + 0.26),
                0.050,
            )
            add_cylinder(
                f"Front_{side_name}_LowerArm_{suffix}",
                lower_outer,
                (dims.front_axle_x + x_shift, inner_y_lower, dims.front_z - 0.20),
                0.060,
            )

        coil_top = Vector((cross_x + 0.10, dims.center_y + side_sign * dims.front_half_track * 0.46, dims.front_z + 0.62))
        add_cylinder(f"Front_{side_name}_Coilover", lower_outer, coil_top, 0.070)
        rack_end = Vector((rack_x, dims.center_y + side_sign * rack_half, rack_z))
        add_cylinder(f"Front_{side_name}_TieRod", center + Vector((0.05, -side_sign * 0.10, 0.02)), rack_end, 0.040, 16)

    # Rear solid axle, differential and longitudinal driveshaft.
    rear_outer = dims.rear_half_track * 0.92
    add_cylinder(
        "RearAxleTube",
        (dims.rear_axle_x, dims.center_y - rear_outer, dims.rear_z),
        (dims.rear_axle_x, dims.center_y + rear_outer, dims.rear_z),
        0.105,
        28,
    )
    diff_scale = max(0.28, dims.rear_half_track * 0.18)
    add_sphere("RearDifferential", (dims.rear_axle_x, dims.center_y, dims.rear_z), (diff_scale * 1.15, diff_scale, diff_scale))

    transmission_x = dims.front_axle_x + dims.wheelbase * 0.43
    add_cylinder(
        "DriveShaft",
        (dims.rear_axle_x - dims.wheelbase * 0.04, dims.center_y, dims.rear_z + 0.02),
        (transmission_x, dims.center_y, dims.front_z - 0.05),
        0.060,
        20,
    )

    # Rear links, coilovers and Panhard bar.
    for side_name, center in (("L", Vector(rl)), ("R", Vector(rr))):
        side_sign = -1.0 if center.y < dims.center_y else 1.0
        axle_pick = Vector((dims.rear_axle_x, dims.center_y + side_sign * dims.rear_half_track * 0.78, dims.rear_z - 0.05))
        lower_chassis = Vector((dims.rear_axle_x - dims.wheelbase * 0.28, dims.center_y + side_sign * dims.rear_half_track * 0.48, dims.rear_z - 0.02))
        upper_chassis = Vector((dims.rear_axle_x - dims.wheelbase * 0.22, dims.center_y + side_sign * dims.rear_half_track * 0.32, dims.rear_z + 0.28))
        add_cylinder(f"Rear_{side_name}_TrailingArm", axle_pick, lower_chassis, 0.060)
        add_cylinder(
            f"Rear_{side_name}_UpperLink",
            Vector((dims.rear_axle_x, dims.center_y + side_sign * dims.rear_half_track * 0.44, dims.rear_z + 0.18)),
            upper_chassis,
            0.048,
        )
        add_cylinder(
            f"Rear_{side_name}_Coilover",
            Vector((dims.rear_axle_x, dims.center_y + side_sign * dims.rear_half_track * 0.82, dims.rear_z + 0.04)),
            Vector((dims.rear_axle_x - dims.wheelbase * 0.12, dims.center_y + side_sign * dims.rear_half_track * 0.54, dims.rear_z + 0.70)),
            0.068,
        )

    add_cylinder(
        "RearPanhard",
        (dims.rear_axle_x, dims.center_y - dims.rear_half_track * 0.78, dims.rear_z + 0.18),
        (dims.rear_axle_x - dims.wheelbase * 0.05, dims.center_y + dims.rear_half_track * 0.58, dims.rear_z + 0.32),
        0.042,
        18,
    )

    # Engine mounting hard-points derived from the front axle/wheelbase envelope.
    engine_x = dims.front_axle_x + dims.wheelbase * 0.08
    mount_half = dims.front_half_track * 0.36
    mount_z = dims.front_z - 0.02
    add_cylinder(
        "EngineMountCrossbar",
        (engine_x, dims.center_y - mount_half, mount_z),
        (engine_x, dims.center_y + mount_half, mount_z),
        0.075,
        22,
    )
    add_cylinder(
        "EngineMount_L",
        (engine_x, dims.center_y - mount_half, mount_z),
        (engine_x - 0.12, dims.center_y - mount_half * 0.62, mount_z + 0.28),
        0.050,
        18,
    )
    add_cylinder(
        "EngineMount_R",
        (engine_x, dims.center_y + mount_half, mount_z),
        (engine_x - 0.12, dims.center_y + mount_half * 0.62, mount_z + 0.28),
        0.050,
        18,
    )

    bpy.context.scene["RF_MECHANICAL_SYSTEMS"] = "v1-procedural"
    bpy.context.scene["RF_WHEEL_PATTERN"] = "5-lug"
    bpy.context.scene["RF_MECHANICAL_COMPONENTS"] = len(created)
    bpy.context.scene["RF_WHEELBASE"] = dims.wheelbase

    return primary

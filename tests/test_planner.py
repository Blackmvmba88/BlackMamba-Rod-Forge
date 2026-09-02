from rodforge.schemas import Criticality
from rodforge.task_planner import build_hotrod_plan
from rodforge.vehicle_geometry import load_vehicle_geometry


def test_hotrod_plan_has_critical_backbone():
    state = build_hotrod_plan()
    assert "chassis_blockout" in state.tasks
    assert "body_shell" in state.tasks
    assert state.tasks["chassis_blockout"].criticality == Criticality.CRITICAL
    assert "chassis_blockout" in state.tasks["cabin_blockout"].dependencies
    assert "materials" in state.tasks["preview"].dependencies


def test_hotrod_v2_adds_mechanical_dependency_backbone():
    geometry = load_vehicle_geometry("configs/vehicle_geometry.yaml")
    state = build_hotrod_plan(vehicle_geometry=geometry)

    assert "front_hubs_brakes" in state.tasks["front_suspension"].dependencies
    assert "front_suspension" in state.tasks["steering"].dependencies
    assert "rear_axle" in state.tasks["rear_links"].dependencies
    assert "rear_axle" in state.tasks["driveshaft"].dependencies
    assert "engine_mounts" in state.tasks["driveshaft"].dependencies
    assert "steering" in state.tasks["secondary_details"].dependencies
    assert "driveshaft" in state.tasks["secondary_details"].dependencies


def test_geometry_constraints_are_attached_to_relevant_tasks():
    geometry = load_vehicle_geometry("configs/vehicle_geometry.yaml")
    state = build_hotrod_plan(vehicle_geometry=geometry)

    suspension = state.tasks["front_suspension"].metadata["geometry_constraints"]
    wheels = state.tasks["rear_wheels"].metadata["geometry_constraints"]

    assert suspension["type"] == "double_wishbone"
    assert suspension["scrub_radius_mm"] == {"min": 10, "max": 25}
    assert wheels["outer_diameter_mm"] == 680
    assert state.metadata["vehicle_geometry"]["variant"] == "hotrod_04"

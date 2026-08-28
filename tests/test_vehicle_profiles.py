import pytest

from rodforge.geometry_strategies import get_strategy
from rodforge.task_planner import build_combi_plan, build_hotrod_plan, build_vehicle_plan
from rodforge.vehicle_profiles import get_vehicle_profile


def test_profiles_resolve_names_and_aliases():
    assert get_vehicle_profile("hotrod").name == "hotrod"
    assert get_vehicle_profile("hot-rod").name == "hotrod"
    assert get_vehicle_profile("combi").name == "combi"
    assert get_vehicle_profile("type2").name == "combi"

    with pytest.raises(ValueError):
        get_vehicle_profile("spaceship")


def test_hotrod_profile_keeps_blueprint_envelope_metadata():
    state = build_hotrod_plan("hotrod_profile_probe")
    task = state.tasks["chassis_blockout"]

    assert task.metadata["vehicle_profile"] == "hotrod"
    assert task.metadata["reference_asset"] == "hotrod.blend"
    assert task.metadata["reference_dimensions_m"] == [2.710, 1.710, 1.260]


def test_combi_plan_uses_isolated_van_geometry_families():
    state = build_combi_plan("combi_profile_probe")

    chassis = state.tasks["chassis_blockout"]
    cabin = state.tasks["cabin_blockout"]
    body = state.tasks["body_shell"]

    assert chassis.strategy == "van_chassis_floor"
    assert chassis.metadata["part_family"] == "van_chassis"
    assert chassis.metadata["cognitive_candidates"] == ["van_chassis_rails"]

    assert cabin.strategy == "van_cabin_box"
    assert cabin.metadata["cognitive_candidates"] == ["van_cabin_split"]

    assert body.strategy == "van_body_box"
    assert body.metadata["cognitive_candidates"] == ["van_body_tapered"]
    assert body.metadata["vehicle_profile"] == "combi"
    assert body.metadata["reference_asset"] == "COMBI_TOPOLOGIA_PRO.blend"
    assert "reference_dimensions_m" not in body.metadata


def test_combi_plan_contains_topology_first_vehicle_parts():
    state = build_vehicle_plan("van")

    expected = {
        "chassis_blockout",
        "cabin_blockout",
        "front_wheels",
        "rear_wheels",
        "body_shell",
        "front_face",
        "windshield",
        "side_windows",
        "sliding_door",
        "bumpers",
        "headlights",
        "mirrors",
        "secondary_details",
        "materials",
        "preview",
    }

    assert expected.issubset(state.tasks)
    assert state.project_name == "blackmamba_combi"
    assert state.tasks["sliding_door"].dependencies == ["body_shell", "side_windows"]


def test_registered_combi_strategies_are_executable_by_existing_builders():
    for name in (
        "van_chassis_floor",
        "van_chassis_rails",
        "van_cabin_box",
        "van_cabin_split",
        "van_body_box",
        "van_body_tapered",
    ):
        spec = get_strategy(name)
        assert spec is not None
        assert spec.builder in {"single_box", "rail_frame", "stacked_cabin", "tapered_prism"}

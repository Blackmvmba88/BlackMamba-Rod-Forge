from rodforge.schemas import Criticality
from rodforge.task_planner import build_hotrod_plan


def test_hotrod_plan_has_critical_backbone():
    state = build_hotrod_plan()
    assert "chassis_blockout" in state.tasks
    assert "body_shell" in state.tasks
    assert state.tasks["chassis_blockout"].criticality == Criticality.CRITICAL
    assert "chassis_blockout" in state.tasks["cabin_blockout"].dependencies
    assert "materials" in state.tasks["preview"].dependencies


def test_hotrod_plan_models_mechanics_before_body():
    state = build_hotrod_plan()

    required = {
        "front_hubs_brakes",
        "rear_hubs_brakes",
        "front_uprights_wishbones",
        "front_steering",
        "front_pushrod",
        "rear_uprights_wishbones",
        "rear_toe_links",
        "rear_pushrod",
        "rear_transaxle",
        "half_shafts",
        "modular_subframes",
        "telemetry_packaging",
    }
    assert required.issubset(state.tasks)
    assert "front_hubs_brakes" in state.tasks["front_uprights_wishbones"].dependencies
    assert "rear_hubs_brakes" in state.tasks["rear_uprights_wishbones"].dependencies
    assert "rear_transaxle" in state.tasks["half_shafts"].dependencies
    assert "modular_subframes" in state.tasks["body_shell"].dependencies
    assert state.metadata["mechanical_architecture"] == "hotrod_mechanical_v1"
    assert state.metadata["mass_distribution_target"] == {
        "front_percent": 48,
        "rear_percent": 52,
    }

from rodforge.schemas import Criticality
from rodforge.task_planner import build_hotrod_plan


def test_hotrod_plan_has_critical_backbone():
    state = build_hotrod_plan()
    assert "chassis_blockout" in state.tasks
    assert "body_shell" in state.tasks
    assert state.tasks["chassis_blockout"].criticality == Criticality.CRITICAL
    assert "chassis_blockout" in state.tasks["cabin_blockout"].dependencies
    assert "materials" in state.tasks["preview"].dependencies


def test_hotrod_plan_establishes_mechanics_before_body_shell():
    state = build_hotrod_plan()
    mechanics = state.tasks["mechanical_systems"]

    assert mechanics.strategy == "mechanical_systems"
    assert mechanics.criticality == Criticality.HIGH
    assert set(mechanics.dependencies) == {
        "chassis_blockout",
        "engine_volume",
        "front_wheels",
        "rear_wheels",
    }
    assert "mechanical_systems" in state.tasks["body_shell"].dependencies

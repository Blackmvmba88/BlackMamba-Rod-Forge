from rodforge.schemas import Criticality
from rodforge.task_planner import build_hotrod_plan


def test_hotrod_plan_has_critical_backbone():
    state = build_hotrod_plan()
    assert "chassis_blockout" in state.tasks
    assert "body_shell" in state.tasks
    assert state.tasks["chassis_blockout"].criticality == Criticality.CRITICAL
    assert "chassis_blockout" in state.tasks["cabin_blockout"].dependencies
    assert "materials" in state.tasks["preview"].dependencies
    assert state.tasks["front_axle"].metadata["pipeline_stage"] == "chassis_body"
    assert state.tasks["simple_transmission"].metadata["pipeline_stage"] == "engine"
    assert state.tasks["wheel_mechanics"].metadata["pipeline_stage"] == "wheels"
    assert "simple_driveline" in state.tasks["secondary_details"].dependencies
    assert state.metadata["tutorial_capture"] is True

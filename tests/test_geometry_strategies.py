from rodforge.blender_executor import DryRunExecutor
from rodforge.geometry_strategies import FAMILY_STRATEGIES, get_strategy
from rodforge.repair_engine import RepairEngine
from rodforge.task_planner import build_hotrod_plan


def test_each_cognitive_family_has_genuinely_distinct_builders():
    for family, names in FAMILY_STRATEGIES.items():
        assert len(names) >= 2
        specs = [get_strategy(name) for name in names]
        assert all(spec is not None for spec in specs)
        assert len({spec.builder for spec in specs if spec is not None}) >= 2, family


def test_hotrod_plan_exposes_real_geometry_candidates():
    state = build_hotrod_plan("strategy_probe")

    chassis = state.tasks["chassis_blockout"]
    cabin = state.tasks["cabin_blockout"]
    front_wheels = state.tasks["front_wheels"]
    body = state.tasks["body_shell"]

    assert chassis.strategy == "chassis_slab"
    assert chassis.metadata["cognitive_candidates"] == ["chassis_rails"]
    assert cabin.metadata["cognitive_candidates"] == ["cabin_chopped"]
    assert front_wheels.metadata["cognitive_candidates"] == ["wheel_cylinder"]
    assert body.metadata["cognitive_candidates"] == ["body_tapered"]


def test_real_alternative_is_available_before_generic_fallbacks():
    task = build_hotrod_plan("repair_probe").tasks["front_wheels"]
    task.metadata["attempted_repairs"] = ["retry_same"]

    decision = RepairEngine().decide(task)

    assert decision.action == "wheel_cylinder"


def test_dry_run_reports_strategy_family_and_builder():
    task = build_hotrod_plan("dry_strategy").tasks["rear_wheels"]

    result = DryRunExecutor().execute(task)

    assert result.success is True
    assert result.evidence["strategy"] == "wheel_torus"
    assert result.evidence["geometry_family"] == "wheel"
    assert result.evidence["geometry_builder"] == "torus_pair"


def test_mechanical_tasks_use_recognizable_geometry_builders():
    state = build_hotrod_plan("mechanical_builders")
    expected = {
        "front_axle": ("front_axle_basic", "front_axle_assembly"),
        "simple_transmission": ("transmission_basic", "transmission_assembly"),
        "wheel_mechanics": ("wheel_mechanics_basic", "wheel_detail_pass"),
        "simple_driveline": ("driveline_basic", "driveline_assembly"),
    }

    for task_id, (strategy, builder) in expected.items():
        task = state.tasks[task_id]
        result = DryRunExecutor().execute(task)
        assert task.strategy == strategy
        assert result.evidence["geometry_builder"] == builder

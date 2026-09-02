import pytest

from rodforge.part_graph import DependencyError, PartGraph
from rodforge.schemas import Task
from rodforge.task_planner import build_hotrod_plan


def test_rejects_unknown_dependency():
    tasks = {"a": Task("a", "A", "A", dependencies=["missing"])}
    with pytest.raises(DependencyError):
        PartGraph(tasks)


def test_rejects_cycle():
    tasks = {
        "a": Task("a", "A", "A", dependencies=["b"]),
        "b": Task("b", "B", "B", dependencies=["a"]),
    }
    with pytest.raises(DependencyError):
        PartGraph(tasks)


def test_execution_layers_are_deterministic_and_complete():
    state = build_hotrod_plan()
    graph = PartGraph(state.tasks)
    layers = graph.execution_layers()

    flattened = [task_id for layer in layers for task_id in layer]
    assert len(flattened) == len(state.tasks)
    assert set(flattened) == set(state.tasks)
    assert layers[0] == ["chassis_blockout"]


def test_dependency_closure_exposes_full_mechanical_chain():
    state = build_hotrod_plan()
    graph = PartGraph(state.tasks)
    closure = graph.dependency_closure("secondary_details")

    assert "chassis_blockout" in closure
    assert "front_hubs_brakes" in closure
    assert "front_suspension" in closure
    assert "steering" in closure
    assert "rear_axle" in closure
    assert "driveshaft" in closure
    assert closure.index("front_suspension") < closure.index("steering")

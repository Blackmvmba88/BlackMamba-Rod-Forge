import pytest

from rodforge.part_graph import DependencyError, PartGraph
from rodforge.schemas import Task


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

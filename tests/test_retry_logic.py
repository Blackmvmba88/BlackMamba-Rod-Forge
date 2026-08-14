from rodforge.repair_engine import RepairEngine
from rodforge.schemas import Criticality, Task, TaskStatus


def test_repair_progresses_without_infinite_retry():
    task = Task(
        "critical",
        "Critical",
        "Critical task",
        fallback_strategies=["retry_same", "simplify_geometry"],
        criticality=Criticality.CRITICAL,
        attempts=1,
        max_attempts=1,
    )
    engine = RepairEngine()

    first = engine.decide(task)
    engine.apply(task, first)
    assert first.action == "retry_same"
    assert task.status == TaskStatus.NEEDS_REPAIR

    second = engine.decide(task)
    engine.apply(task, second)
    assert second.action == "simplify_geometry"

    third = engine.decide(task)
    engine.apply(task, third)
    assert third.action == "block"
    assert task.status == TaskStatus.BLOCKED

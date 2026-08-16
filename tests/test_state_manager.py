from rodforge.schemas import ProjectState, Task, TaskStatus
from rodforge.state_manager import StateManager


def test_state_round_trip(tmp_path):
    state = ProjectState(project_name="test", tasks={"a": Task("a", "A", "A")})
    manager = StateManager(tmp_path / "state.json")
    manager.save(state)
    loaded = manager.load()
    assert loaded.project_name == "test"
    assert "a" in loaded.tasks


def test_load_recovers_interrupted_running_task(tmp_path):
    task = Task("a", "A", "A", status=TaskStatus.RUNNING, attempts=1)
    state = ProjectState(project_name="test", tasks={"a": task}, active_task_id="a")
    manager = StateManager(tmp_path / "state.json")
    manager.save(state)

    loaded = manager.load()

    assert loaded.active_task_id is None
    assert loaded.tasks["a"].status == TaskStatus.NEEDS_REPAIR
    assert loaded.tasks["a"].metadata["recovery_events"][0]["attempt"] == 1

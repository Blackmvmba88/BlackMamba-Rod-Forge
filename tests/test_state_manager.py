from rodforge.schemas import ProjectState, Task
from rodforge.state_manager import StateManager


def test_state_round_trip(tmp_path):
    state = ProjectState(project_name="test", tasks={"a": Task("a", "A", "A")})
    manager = StateManager(tmp_path / "state.json")
    manager.save(state)
    loaded = manager.load()
    assert loaded.project_name == "test"
    assert "a" in loaded.tasks

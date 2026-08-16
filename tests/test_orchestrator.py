from rodforge.blender_executor import DryRunExecutor
from rodforge.checkpointing import CheckpointManager
from rodforge.orchestrator import Orchestrator
from rodforge.state_manager import StateManager
from rodforge.task_planner import build_hotrod_plan


def test_dry_run_completes_entire_plan(tmp_path):
    state = build_hotrod_plan("test_hotrod")
    orchestrator = Orchestrator(
        state_manager=StateManager(tmp_path / "state.json"),
        checkpoint_manager=CheckpointManager(tmp_path / "checkpoints"),
        executor=DryRunExecutor(),
        checkpoint_every=2,
    )

    summary = orchestrator.run(state)
    assert summary.done is True
    assert summary.completed == len(state.tasks)
    assert summary.blocked == 0
    assert (tmp_path / "state.json").exists()
    checkpoints = sorted((tmp_path / "checkpoints").glob("checkpoint_*.json"))
    assert checkpoints
    assert state.metadata["final_checkpoint_completed_count"] == len(state.tasks)

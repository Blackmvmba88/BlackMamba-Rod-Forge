from rodforge.blender_executor import DryRunExecutor
from rodforge.checkpointing import CheckpointManager
from rodforge.cognition import CognitiveEngine, ExperienceEpisode, ExperienceMemory
from rodforge.orchestrator import Orchestrator
from rodforge.schemas import Task
from rodforge.state_manager import StateManager
from rodforge.task_planner import build_hotrod_plan


def _episode(signature: str, strategy: str, score: float) -> ExperienceEpisode:
    return ExperienceEpisode(
        timestamp="2026-08-14T00:00:00+00:00",
        project_name="training",
        task_id="wheel",
        signature=signature,
        strategy=strategy,
        metric="quality_score",
        predicted_score=None,
        observed_score=score,
        prediction_error=None,
        accepted=True,
    )


def test_prediction_updates_from_experience(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    engine = CognitiveEngine(memory, mode="shadow")
    task = Task(
        task_id="wheel",
        name="Wheel",
        objective="Build a wheel",
        strategy="method_a",
        metadata={"cognitive_signature": "wheel", "cognitive_metric": "quality_score"},
    )

    first = engine.imagine(task)
    assert first.candidates[0].expected_score == 0.5
    assert first.candidates[0].confidence == 0.0

    engine.learn(
        project_name="figure_001",
        task=task,
        accepted=True,
        metrics={"quality_score": 0.82},
        hypothesis=first,
    )

    second = engine.imagine(task)
    prediction = second.candidates[0]
    assert prediction.samples == 1
    assert prediction.scope == "signature"
    assert prediction.expected_score == 0.82
    assert prediction.confidence > 0.0


def test_shadow_mode_imagines_better_option_without_changing_execution(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    for _ in range(4):
        memory.append(_episode("wheel", "method_a", 0.25))
        memory.append(_episode("wheel", "method_b", 0.90))

    engine = CognitiveEngine(memory, mode="shadow", min_samples=2)
    task = Task(
        task_id="wheel",
        name="Wheel",
        objective="Build a wheel",
        strategy="method_a",
        metadata={
            "cognitive_signature": "wheel",
            "cognitive_metric": "quality_score",
            "cognitive_candidates": ["method_b"],
        },
    )

    hypothesis = engine.imagine(task)
    engine.apply(task, hypothesis)

    assert hypothesis.candidates[1].expected_score > hypothesis.candidates[0].expected_score
    assert hypothesis.recommended_strategy == "method_a"
    assert task.strategy == "method_a"


def test_active_mode_requires_evidence_before_strategy_change(tmp_path):
    memory = ExperienceMemory(tmp_path / "experience.json")
    for _ in range(4):
        memory.append(_episode("wheel", "method_a", 0.20))
        memory.append(_episode("wheel", "method_b", 0.92))

    engine = CognitiveEngine(
        memory,
        mode="active",
        min_samples=2,
        activation_confidence=0.40,
        activation_margin=0.10,
    )
    task = Task(
        task_id="wheel",
        name="Wheel",
        objective="Build a wheel",
        strategy="method_a",
        metadata={
            "cognitive_signature": "wheel",
            "cognitive_metric": "quality_score",
            "cognitive_candidates": ["method_b"],
        },
    )

    hypothesis = engine.imagine(task)
    engine.apply(task, hypothesis)

    assert hypothesis.recommended_strategy == "method_b"
    assert task.strategy == "method_b"
    assert task.metadata["cognition"]["strategy_changed"] is True


def test_orchestrator_records_an_episode_for_each_completed_task(tmp_path):
    state = build_hotrod_plan("cognitive_hotrod")
    memory = ExperienceMemory(tmp_path / "cognition" / "experience.json")
    orchestrator = Orchestrator(
        state_manager=StateManager(tmp_path / "state.json"),
        checkpoint_manager=CheckpointManager(tmp_path / "checkpoints"),
        executor=DryRunExecutor(),
        cognitive_engine=CognitiveEngine(memory, mode="shadow"),
        checkpoint_every=2,
    )

    summary = orchestrator.run(state)

    assert summary.done is True
    assert len(memory.episodes) == len(state.tasks)
    assert all("cognition" in task.metadata for task in state.tasks.values())

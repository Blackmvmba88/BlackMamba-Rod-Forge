from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from .blender_executor import BlenderExecutor, DryRunExecutor
from .checkpointing import CheckpointManager
from .cognition import CognitiveEngine, ExperienceMemory
from .cognitive_report import build_cognitive_report
from .config import CognitionConfig, ProjectConfig, VisualFeedbackConfig
from .critic import Critic
from .orchestrator import Orchestrator
from .reference_inspector import inspect_reference
from .state_manager import StateManager
from .task_planner import build_hotrod_plan
from .visual_feedback import VisualComparator


@dataclass(slots=True)
class CurriculumRunResult:
    run_id: str
    reference_image: str
    reference_sha256: str | None
    status: str
    done: bool
    completed_tasks: int
    global_failures: int
    output_dir: str
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_curriculum(
    base_config: ProjectConfig,
    manifest_path: str | Path,
    *,
    executor_kind: str = "dry-run",
) -> dict[str, Any]:
    """Run multiple references sequentially against one shared cognitive memory.

    Each figure gets isolated state/checkpoints/previews/.blend outputs, while
    cognitive episodes accumulate in the same experience store. This creates a
    measurable learning sequence instead of unrelated one-off runs.
    """
    if executor_kind not in {"dry-run", "blender"}:
        raise ValueError("executor_kind must be 'dry-run' or 'blender'")

    manifest = _load_manifest(manifest_path)
    curriculum_name = str(manifest.get("name", "rodforge_curriculum"))
    output_root = Path(str(manifest.get("output_root", "data/outputs/curriculum")))
    output_root.mkdir(parents=True, exist_ok=True)
    continue_on_error = bool(manifest.get("continue_on_error", True))
    window = max(1, int(manifest.get("report_window", 10)))

    cognition_config = base_config.cognition
    memory_path = str(
        manifest.get(
            "memory_file",
            cognition_config.memory_file
            if cognition_config is not None
            else "data/outputs/cognition/experience.json",
        )
    )
    shared_memory = ExperienceMemory(memory_path)

    items = manifest.get("runs", [])
    if not isinstance(items, list) or not items:
        raise ValueError("curriculum manifest must contain a non-empty 'runs' list")

    results: list[CurriculumRunResult] = []
    for index, raw_item in enumerate(items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"curriculum run #{index} must be a mapping")
        run_id = str(raw_item.get("id", f"figure_{index:03d}"))
        reference_image = str(raw_item.get("reference_image", "")).strip()
        run_dir = output_root / _safe_name(run_id)

        if not reference_image:
            result = CurriculumRunResult(
                run_id=run_id,
                reference_image="",
                reference_sha256=None,
                status="blocked_reference",
                done=False,
                completed_tasks=0,
                global_failures=0,
                output_dir=str(run_dir),
                errors=["reference_image is required"],
            )
            results.append(result)
            if not continue_on_error:
                break
            continue

        reference_report = inspect_reference(reference_image)
        if not reference_report.get("ready"):
            result = CurriculumRunResult(
                run_id=run_id,
                reference_image=reference_image,
                reference_sha256=None,
                status="blocked_reference",
                done=False,
                completed_tasks=0,
                global_failures=0,
                output_dir=str(run_dir),
                errors=[str(error) for error in reference_report.get("errors", [])],
            )
            results.append(result)
            if not continue_on_error:
                break
            continue

        reference_sha256 = str(reference_report["sha256"])
        run_config = _run_config(
            base_config,
            run_id=run_id,
            reference_image=reference_image,
            reference_sha256=reference_sha256,
            run_dir=run_dir,
            memory_path=memory_path,
        )

        try:
            if executor_kind == "blender":
                _reset_generated_blender_scene()
            summary = _run_single(
                run_config,
                shared_memory=shared_memory,
                reference_sha256=reference_sha256,
                executor_kind=executor_kind,
            )
            result = CurriculumRunResult(
                run_id=run_id,
                reference_image=reference_image,
                reference_sha256=reference_sha256,
                status="completed" if summary.done else "blocked",
                done=summary.done,
                completed_tasks=summary.completed,
                global_failures=summary.global_failures,
                output_dir=str(run_dir),
                errors=[],
            )
        except Exception as exc:
            result = CurriculumRunResult(
                run_id=run_id,
                reference_image=reference_image,
                reference_sha256=reference_sha256,
                status="error",
                done=False,
                completed_tasks=0,
                global_failures=0,
                output_dir=str(run_dir),
                errors=[str(exc)],
            )
            results.append(result)
            if not continue_on_error:
                break
            continue

        results.append(result)
        if not result.done and not continue_on_error:
            break

    cognition_report = build_cognitive_report(shared_memory, window=window)
    payload = {
        "name": curriculum_name,
        "executor": executor_kind,
        "memory_file": memory_path,
        "runs_total": len(items),
        "runs_attempted": len(results),
        "runs_completed": sum(result.status == "completed" for result in results),
        "runs_blocked": sum(result.status.startswith("blocked") for result in results),
        "runs_error": sum(result.status == "error" for result in results),
        "runs": [result.to_dict() for result in results],
        "cognition": cognition_report,
    }

    report_path = output_root / "curriculum_report.json"
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    payload["report_path"] = str(report_path)
    return payload


def _load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("curriculum manifest root must be a mapping")
    return data


def _run_config(
    base: ProjectConfig,
    *,
    run_id: str,
    reference_image: str,
    reference_sha256: str,
    run_dir: Path,
    memory_path: str,
) -> ProjectConfig:
    cognition = _cognition_config(base.cognition, memory_path)
    visual = _visual_config(base.visual_feedback, run_dir)
    return replace(
        base,
        project_name=run_id,
        reference_image=reference_image,
        output_blend=str(run_dir / "model.blend"),
        state_file=str(run_dir / "state.json"),
        checkpoint_dir=str(run_dir / "checkpoints"),
        cognition=cognition,
        visual_feedback=visual,
    )


def _cognition_config(
    cognition: CognitionConfig | None,
    memory_path: str,
) -> CognitionConfig | None:
    if cognition is None:
        return None
    return replace(cognition, memory_file=memory_path)


def _visual_config(
    visual: VisualFeedbackConfig | None,
    run_dir: Path,
) -> VisualFeedbackConfig | None:
    if visual is None:
        return None
    return replace(visual, preview_dir=str(run_dir / "previews"))


def _run_single(
    config: ProjectConfig,
    *,
    shared_memory: ExperienceMemory,
    reference_sha256: str,
    executor_kind: str,
):
    state = build_hotrod_plan(config.project_name)
    state.metadata["reference_image"] = config.reference_image
    state.metadata["reference_sha256"] = reference_sha256
    state.metadata["curriculum_run"] = True

    orchestrator = Orchestrator(
        state_manager=StateManager(config.state_file),
        checkpoint_manager=CheckpointManager(config.checkpoint_dir),
        executor=_executor(executor_kind, config),
        critic=_critic(config),
        cognitive_engine=_cognitive_engine(
            config,
            shared_memory=shared_memory,
            reference_sha256=reference_sha256,
        ),
        checkpoint_every=config.checkpoint_every_completed_tasks,
        max_global_failures=config.max_global_failures_before_pause,
    )
    return orchestrator.run(state)


def _executor(kind: str, config: ProjectConfig):
    if kind == "blender":
        visual = config.visual_feedback
        return BlenderExecutor(
            config.output_blend,
            preview_dir=visual.preview_dir if visual and visual.enabled else None,
            render_every_task=bool(visual and visual.enabled and visual.render_every_task),
            preview_resolution=visual.preview_resolution if visual else 256,
        )
    return DryRunExecutor()


def _critic(config: ProjectConfig) -> Critic:
    visual = config.visual_feedback
    if visual is None or not visual.enabled:
        return Critic()
    return Critic(
        reference_image=config.reference_image,
        visual_comparator=VisualComparator(
            normalized_size=visual.normalized_size,
            background_distance=visual.background_distance,
        ),
    )


def _cognitive_engine(
    config: ProjectConfig,
    *,
    shared_memory: ExperienceMemory,
    reference_sha256: str,
) -> CognitiveEngine | None:
    cognition = config.cognition
    if cognition is None or not cognition.enabled:
        return None
    return CognitiveEngine(
        shared_memory,
        mode=cognition.mode,
        min_samples=cognition.min_samples,
        activation_confidence=cognition.activation_confidence,
        activation_margin=cognition.activation_margin,
        counterfactual_probes=cognition.counterfactual_probes,
        max_probes_per_task=cognition.max_probes_per_task,
        probe_sample_target=cognition.probe_sample_target,
        reference_sha256=reference_sha256,
    )


def _reset_generated_blender_scene() -> None:
    """Remove only Rod Forge-owned Blender objects between curriculum figures."""
    try:
        import bpy  # type: ignore
    except ImportError:
        return

    for obj in list(bpy.data.objects):
        if obj.name.startswith("RF_"):
            bpy.data.objects.remove(obj, do_unlink=True)


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._-") or "figure"

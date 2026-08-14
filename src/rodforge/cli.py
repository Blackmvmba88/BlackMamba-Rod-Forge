from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .blender_executor import BlenderExecutor, DryRunExecutor
from .checkpointing import CheckpointManager
from .cognition import CognitiveEngine, ExperienceMemory
from .cognitive_report import build_cognitive_report
from .config import ProjectConfig, load_config
from .critic import Critic
from .curriculum import run_curriculum
from .orchestrator import Orchestrator
from .reference_inspector import inspect_reference
from .state_manager import StateManager
from .task_planner import build_hotrod_plan
from .visual_feedback import VisualComparator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rodforge")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Start a new Rod Forge run")
    run.add_argument("--config", default="configs/project.yaml")
    run.add_argument("--executor", choices=["dry-run", "blender"], default="dry-run")

    resume = sub.add_parser("resume", help="Resume persisted state")
    resume.add_argument("--config", default="configs/project.yaml")
    resume.add_argument("--executor", choices=["dry-run", "blender"], default="dry-run")

    report = sub.add_parser(
        "cognition-report",
        help="Measure how accurately cognitive predictions match observed outcomes",
    )
    report.add_argument("--config", default="configs/project.yaml")
    report.add_argument("--window", type=int, default=10)

    reference = sub.add_parser(
        "reference-check",
        help="Validate and fingerprint the configured visual reference",
    )
    reference.add_argument("--config", default="configs/project.yaml")

    curriculum = sub.add_parser(
        "curriculum-run",
        help="Run a sequence of references against one shared cognitive memory",
    )
    curriculum.add_argument("--config", default="configs/project.yaml")
    curriculum.add_argument("--manifest", required=True)
    curriculum.add_argument("--executor", choices=["dry-run", "blender"], default="dry-run")

    return parser


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
    reference_sha256: str | None = None,
) -> CognitiveEngine | None:
    cognition = config.cognition
    if cognition is None or not cognition.enabled:
        return None
    return CognitiveEngine(
        ExperienceMemory(cognition.memory_file),
        mode=cognition.mode,
        min_samples=cognition.min_samples,
        activation_confidence=cognition.activation_confidence,
        activation_margin=cognition.activation_margin,
        counterfactual_probes=cognition.counterfactual_probes,
        max_probes_per_task=cognition.max_probes_per_task,
        probe_sample_target=cognition.probe_sample_target,
        reference_sha256=reference_sha256,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)

    if args.command == "cognition-report":
        cognition = config.cognition
        memory_file = (
            cognition.memory_file
            if cognition is not None
            else "data/outputs/cognition/experience.json"
        )
        report = build_cognitive_report(
            ExperienceMemory(memory_file),
            window=max(1, int(args.window)),
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.command == "reference-check":
        report = inspect_reference(config.reference_image)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ready"] else 2

    if args.command == "curriculum-run":
        report = run_curriculum(
            config,
            args.manifest,
            executor_kind=args.executor,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        complete = (
            report["runs_completed"] == report["runs_total"]
            and report["runs_blocked"] == 0
            and report["runs_error"] == 0
        )
        return 0 if complete else 2

    reference_report = inspect_reference(config.reference_image)
    reference_sha256 = (
        str(reference_report["sha256"])
        if reference_report.get("ready") and reference_report.get("sha256")
        else None
    )

    state_manager = StateManager(config.state_file)
    checkpoint_manager = CheckpointManager(config.checkpoint_dir)

    if args.command == "resume":
        state = state_manager.load()
    else:
        state = build_hotrod_plan(config.project_name)
        state.metadata["reference_image"] = config.reference_image

    if reference_sha256 is not None:
        state.metadata["reference_sha256"] = reference_sha256

    orchestrator = Orchestrator(
        state_manager=state_manager,
        checkpoint_manager=checkpoint_manager,
        executor=_executor(args.executor, config),
        critic=_critic(config),
        cognitive_engine=_cognitive_engine(
            config,
            reference_sha256=reference_sha256,
        ),
        checkpoint_every=config.checkpoint_every_completed_tasks,
        max_global_failures=config.max_global_failures_before_pause,
    )
    summary = orchestrator.run(state)
    print(json.dumps(asdict(summary), indent=2))
    return 0 if summary.done else 2


if __name__ == "__main__":
    raise SystemExit(main())

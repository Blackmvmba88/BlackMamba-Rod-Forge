from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .blender_executor import BlenderExecutor, DryRunExecutor
from .checkpointing import CheckpointManager
from .cognition import CognitiveEngine, ExperienceMemory
from .config import ProjectConfig, load_config
from .orchestrator import Orchestrator
from .state_manager import StateManager
from .task_planner import build_hotrod_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rodforge")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Start a new Rod Forge run")
    run.add_argument("--config", default="configs/project.yaml")
    run.add_argument("--executor", choices=["dry-run", "blender"], default="dry-run")

    resume = sub.add_parser("resume", help="Resume persisted state")
    resume.add_argument("--config", default="configs/project.yaml")
    resume.add_argument("--executor", choices=["dry-run", "blender"], default="dry-run")

    return parser


def _executor(kind: str, output_blend: str):
    if kind == "blender":
        return BlenderExecutor(output_blend)
    return DryRunExecutor()


def _cognitive_engine(config: ProjectConfig) -> CognitiveEngine | None:
    cognition = config.cognition
    if cognition is None or not cognition.enabled:
        return None
    return CognitiveEngine(
        ExperienceMemory(cognition.memory_file),
        mode=cognition.mode,
        min_samples=cognition.min_samples,
        activation_confidence=cognition.activation_confidence,
        activation_margin=cognition.activation_margin,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    state_manager = StateManager(config.state_file)
    checkpoint_manager = CheckpointManager(config.checkpoint_dir)

    if args.command == "resume":
        state = state_manager.load()
    else:
        state = build_hotrod_plan(config.project_name)
        state.metadata["reference_image"] = config.reference_image

    orchestrator = Orchestrator(
        state_manager=state_manager,
        checkpoint_manager=checkpoint_manager,
        executor=_executor(args.executor, config.output_blend),
        cognitive_engine=_cognitive_engine(config),
        checkpoint_every=config.checkpoint_every_completed_tasks,
        max_global_failures=config.max_global_failures_before_pause,
    )
    summary = orchestrator.run(state)
    print(json.dumps(asdict(summary), indent=2))
    return 0 if summary.done else 2


if __name__ == "__main__":
    raise SystemExit(main())

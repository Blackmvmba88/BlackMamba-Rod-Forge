from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class ProjectConfig:
    project_name: str
    reference_image: str
    output_blend: str
    state_file: str
    checkpoint_dir: str
    checkpoint_every_completed_tasks: int = 2
    max_global_failures_before_pause: int = 20


def load_config(path: str | Path) -> ProjectConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    outputs = data.get("outputs", {})
    return ProjectConfig(
        project_name=data.get("project_name", "blackmamba_hotrod"),
        reference_image=data.get("reference_image", "data/references/hotrod_reference.png"),
        output_blend=outputs.get("blend", "data/outputs/blend/hotrod.blend"),
        state_file=outputs.get("state", "data/outputs/state/project_state.json"),
        checkpoint_dir=outputs.get("checkpoints", "data/outputs/checkpoints"),
        checkpoint_every_completed_tasks=int(data.get("checkpoint_every_completed_tasks", 2)),
        max_global_failures_before_pause=int(data.get("max_global_failures_before_pause", 20)),
    )

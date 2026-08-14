from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class CognitionConfig:
    enabled: bool = True
    mode: str = "shadow"
    memory_file: str = "data/outputs/cognition/experience.json"
    min_samples: int = 3
    activation_confidence: float = 0.70
    activation_margin: float = 0.05


@dataclass(slots=True)
class ProjectConfig:
    project_name: str
    reference_image: str
    output_blend: str
    state_file: str
    checkpoint_dir: str
    checkpoint_every_completed_tasks: int = 2
    max_global_failures_before_pause: int = 20
    cognition: CognitionConfig | None = None


def load_config(path: str | Path) -> ProjectConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    outputs = data.get("outputs", {})
    cognition_data = data.get("cognition", {})
    cognition = CognitionConfig(
        enabled=bool(cognition_data.get("enabled", True)),
        mode=str(cognition_data.get("mode", "shadow")),
        memory_file=str(cognition_data.get("memory_file", "data/outputs/cognition/experience.json")),
        min_samples=int(cognition_data.get("min_samples", 3)),
        activation_confidence=float(cognition_data.get("activation_confidence", 0.70)),
        activation_margin=float(cognition_data.get("activation_margin", 0.05)),
    )
    return ProjectConfig(
        project_name=data.get("project_name", "blackmamba_hotrod"),
        reference_image=data.get("reference_image", "data/references/hotrod_reference.png"),
        output_blend=outputs.get("blend", "data/outputs/blend/hotrod.blend"),
        state_file=outputs.get("state", "data/outputs/state/project_state.json"),
        checkpoint_dir=outputs.get("checkpoints", "data/outputs/checkpoints"),
        checkpoint_every_completed_tasks=int(data.get("checkpoint_every_completed_tasks", 2)),
        max_global_failures_before_pause=int(data.get("max_global_failures_before_pause", 20)),
        cognition=cognition,
    )

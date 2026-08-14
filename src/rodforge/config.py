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
    counterfactual_probes: bool = True
    max_probes_per_task: int = 1
    probe_sample_target: int = 3
    min_transfer_references: int = 3
    max_transfer_spread: float = 0.10


@dataclass(slots=True)
class VisualFeedbackConfig:
    enabled: bool = True
    preview_dir: str = "data/outputs/previews"
    render_every_task: bool = True
    preview_resolution: int = 256
    normalized_size: int = 128
    background_distance: float = 42.0


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
    visual_feedback: VisualFeedbackConfig | None = None


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
        counterfactual_probes=bool(cognition_data.get("counterfactual_probes", True)),
        max_probes_per_task=int(cognition_data.get("max_probes_per_task", 1)),
        probe_sample_target=int(cognition_data.get("probe_sample_target", cognition_data.get("min_samples", 3))),
        min_transfer_references=int(cognition_data.get("min_transfer_references", 3)),
        max_transfer_spread=float(cognition_data.get("max_transfer_spread", 0.10)),
    )

    visual_data = data.get("visual_feedback", {})
    visual_feedback = VisualFeedbackConfig(
        enabled=bool(visual_data.get("enabled", True)),
        preview_dir=str(visual_data.get("preview_dir", "data/outputs/previews")),
        render_every_task=bool(visual_data.get("render_every_task", True)),
        preview_resolution=int(visual_data.get("preview_resolution", 256)),
        normalized_size=int(visual_data.get("normalized_size", 128)),
        background_distance=float(visual_data.get("background_distance", 42.0)),
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
        visual_feedback=visual_feedback,
    )

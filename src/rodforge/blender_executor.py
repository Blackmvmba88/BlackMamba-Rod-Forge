from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import Task


@dataclass(slots=True)
class ExecutionResult:
    success: bool
    evidence: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"success": self.success, "evidence": self.evidence, "error": self.error}


class DryRunExecutor:
    """Exercises orchestration without requiring Blender."""

    def execute(self, task: Task) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            evidence={
                "object_exists": True,
                "object_name": f"RF_{task.task_id}",
                "executor": "dry-run",
                "strategy": task.strategy,
            },
        )


class BlenderExecutor:
    """Minimal bpy bridge. Import is delayed so the package works outside Blender."""

    def __init__(self, output_blend: str | Path | None = None):
        self.output_blend = Path(output_blend) if output_blend else None

    @staticmethod
    def _bpy():
        try:
            import bpy  # type: ignore
        except ImportError as exc:
            raise RuntimeError("BlenderExecutor requires execution inside Blender with bpy available") from exc
        return bpy

    def execute(self, task: Task) -> ExecutionResult:
        try:
            bpy = self._bpy()
            name = f"RF_{task.task_id}"

            if task.strategy in {"primitive_blockout", "retry_same", "simplify_geometry", "alternate_method"}:
                bpy.ops.mesh.primitive_cube_add(size=2.0)
                obj = bpy.context.active_object
                obj.name = name
                self._shape_for_task(obj, task.task_id)
            elif task.strategy in {"body_shell", "front_assembly", "engine_detail", "detail_pass", "materials", "preview", "split_task", "rebuild_from_checkpoint"}:
                bpy.ops.mesh.primitive_cube_add(size=1.0)
                obj = bpy.context.active_object
                obj.name = name
                self._shape_for_task(obj, task.task_id)
            else:
                return ExecutionResult(False, {}, f"Unknown strategy: {task.strategy}")

            if self.output_blend:
                self.output_blend.parent.mkdir(parents=True, exist_ok=True)
                bpy.ops.wm.save_as_mainfile(filepath=str(self.output_blend.resolve()))

            return ExecutionResult(
                True,
                {
                    "object_exists": obj is not None,
                    "object_name": obj.name,
                    "executor": "blender",
                    "strategy": task.strategy,
                    "dimensions": list(obj.dimensions),
                },
            )
        except Exception as exc:  # Blender operations must be captured into state, not kill the loop.
            return ExecutionResult(False, {}, str(exc))

    @staticmethod
    def _shape_for_task(obj: Any, task_id: str) -> None:
        presets = {
            "chassis_blockout": ((0.0, 0.0, 0.65), (4.8, 1.7, 0.35)),
            "cabin_blockout": ((0.35, 0.0, 1.55), (2.1, 1.65, 1.65)),
            "engine_volume": ((-1.65, 0.0, 1.05), (1.75, 1.15, 1.15)),
            "body_shell": ((0.35, 0.0, 1.45), (2.25, 1.72, 1.45)),
            "front_grille": ((-2.65, 0.0, 1.0), (0.28, 1.0, 1.55)),
            "engine_block": ((-1.65, 0.0, 1.05), (1.45, 1.0, 0.95)),
            "blower": ((-1.65, 0.0, 1.8), (0.95, 0.75, 0.55)),
        }
        location, scale = presets.get(task_id, ((0.0, 0.0, 1.0), (0.5, 0.5, 0.5)))
        obj.location = location
        obj.scale = scale

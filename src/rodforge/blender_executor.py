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
    """Minimal bpy bridge with optional low-cost visual observations."""

    def __init__(
        self,
        output_blend: str | Path | None = None,
        *,
        preview_dir: str | Path | None = None,
        render_every_task: bool = False,
        preview_resolution: int = 256,
    ):
        self.output_blend = Path(output_blend) if output_blend else None
        self.preview_dir = Path(preview_dir) if preview_dir else None
        self.render_every_task = bool(render_every_task)
        self.preview_resolution = max(64, int(preview_resolution))

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
            obj = self._execute_geometry(bpy, task)

            if self.output_blend:
                self.output_blend.parent.mkdir(parents=True, exist_ok=True)
                bpy.ops.wm.save_as_mainfile(filepath=str(self.output_blend.resolve()))

            evidence: dict[str, Any] = {
                "object_exists": obj is not None,
                "object_name": obj.name if obj is not None else "",
                "executor": "blender",
                "strategy": task.strategy,
            }
            if obj is not None and hasattr(obj, "dimensions"):
                evidence["dimensions"] = list(obj.dimensions)

            should_render = self.preview_dir is not None and (
                self.render_every_task or task.strategy == "preview"
            )
            if should_render:
                preview_path = self._render_observation(bpy, task)
                evidence["preview_path"] = str(preview_path)
                evidence["preview_resolution"] = self.preview_resolution

            return ExecutionResult(True, evidence)
        except Exception as exc:  # Blender operations must be captured into state, not kill the loop.
            return ExecutionResult(False, {}, str(exc))

    def _execute_geometry(self, bpy: Any, task: Task) -> Any:
        name = f"RF_{task.task_id}"

        if task.strategy == "preview":
            return self._representative_mesh(bpy)

        if task.strategy in {"primitive_blockout", "retry_same", "simplify_geometry", "alternate_method"}:
            bpy.ops.mesh.primitive_cube_add(size=2.0)
            obj = bpy.context.active_object
            obj.name = name
            self._shape_for_task(obj, task.task_id)
            return obj

        if task.strategy in {
            "body_shell",
            "front_assembly",
            "engine_detail",
            "detail_pass",
            "materials",
            "split_task",
            "rebuild_from_checkpoint",
        }:
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            obj = bpy.context.active_object
            obj.name = name
            self._shape_for_task(obj, task.task_id)
            return obj

        raise ValueError(f"Unknown strategy: {task.strategy}")

    def _render_observation(self, bpy: Any, task: Task) -> Path:
        if self.preview_dir is None:
            raise RuntimeError("Preview directory is not configured")

        self.preview_dir.mkdir(parents=True, exist_ok=True)
        scene = bpy.context.scene
        meshes = [obj for obj in scene.objects if getattr(obj, "type", None) == "MESH"]
        if not meshes:
            raise RuntimeError("Cannot render cognitive preview without mesh geometry")

        center, extent = self._scene_bounds(meshes)
        camera = self._ensure_camera(bpy, center, extent)
        self._ensure_light(bpy, center, extent)
        scene.camera = camera

        render = scene.render
        render.resolution_x = self.preview_resolution
        render.resolution_y = self.preview_resolution
        render.resolution_percentage = 100
        render.image_settings.file_format = "PNG"
        render.image_settings.color_mode = "RGBA"
        render.film_transparent = True

        self._prefer_eevee(scene)

        preview_path = self.preview_dir / f"{task.task_id}_{task.attempts:02d}.png"
        render.filepath = str(preview_path.resolve())
        bpy.ops.render.render(write_still=True)
        return preview_path

    @staticmethod
    def _scene_bounds(meshes: list[Any]) -> tuple[tuple[float, float, float], float]:
        points: list[tuple[float, float, float]] = []
        for obj in meshes:
            for corner in obj.bound_box:
                world = obj.matrix_world @ obj.location.__class__(corner)
                points.append((float(world.x), float(world.y), float(world.z)))

        min_x = min(point[0] for point in points)
        max_x = max(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_y = max(point[1] for point in points)
        min_z = min(point[2] for point in points)
        max_z = max(point[2] for point in points)
        center = (
            (min_x + max_x) / 2.0,
            (min_y + max_y) / 2.0,
            (min_z + max_z) / 2.0,
        )
        extent = max(max_x - min_x, max_y - min_y, max_z - min_z, 1.0)
        return center, extent

    @staticmethod
    def _ensure_camera(bpy: Any, center: tuple[float, float, float], extent: float) -> Any:
        from mathutils import Vector  # type: ignore

        camera = bpy.data.objects.get("RF_CognitiveCamera")
        if camera is None:
            camera_data = bpy.data.cameras.new("RF_CognitiveCamera")
            camera = bpy.data.objects.new("RF_CognitiveCamera", camera_data)
            bpy.context.scene.collection.objects.link(camera)

        target = Vector(center)
        camera.location = target + Vector((extent * 1.35, -extent * 1.75, extent * 0.95))
        direction = target - camera.location
        camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = extent * 1.55
        return camera

    @staticmethod
    def _ensure_light(bpy: Any, center: tuple[float, float, float], extent: float) -> None:
        from mathutils import Vector  # type: ignore

        light = bpy.data.objects.get("RF_CognitiveKey")
        if light is None:
            light_data = bpy.data.lights.new("RF_CognitiveKey", type="AREA")
            light = bpy.data.objects.new("RF_CognitiveKey", light_data)
            bpy.context.scene.collection.objects.link(light)

        target = Vector(center)
        light.location = target + Vector((-extent, -extent, extent * 2.0))
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
        light.data.energy = 1200.0
        light.data.shape = "DISK"
        light.data.size = extent * 2.0

    @staticmethod
    def _prefer_eevee(scene: Any) -> None:
        engines = {item.identifier for item in scene.bl_rna.properties["render_engine"].enum_items}
        if "BLENDER_EEVEE_NEXT" in engines:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        elif "BLENDER_EEVEE" in engines:
            scene.render.engine = "BLENDER_EEVEE"

    @staticmethod
    def _representative_mesh(bpy: Any) -> Any:
        meshes = [obj for obj in bpy.context.scene.objects if getattr(obj, "type", None) == "MESH"]
        return meshes[0] if meshes else None

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

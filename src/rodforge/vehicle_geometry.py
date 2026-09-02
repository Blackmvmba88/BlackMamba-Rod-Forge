from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class GeometryValidationError(ValueError):
    """Raised when the vehicle geometry contract is malformed."""


@dataclass(frozen=True, slots=True)
class VehicleGeometry:
    schema_version: int
    variant: str
    units: str
    status: str
    vehicle: dict[str, Any]
    constraints: dict[str, dict[str, Any]]
    notes: list[str]

    def constraints_for(self, task_id: str) -> dict[str, Any]:
        return deepcopy(self.constraints.get(task_id, {}))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "variant": self.variant,
            "units": self.units,
            "status": self.status,
            "vehicle": deepcopy(self.vehicle),
            "constraint_tasks": sorted(self.constraints),
        }


def load_vehicle_geometry(path: str | Path) -> VehicleGeometry:
    geometry_path = Path(path)
    data = yaml.safe_load(geometry_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise GeometryValidationError("vehicle geometry root must be a mapping")

    schema_version = int(data.get("schema_version", 1))
    if schema_version != 1:
        raise GeometryValidationError(f"unsupported vehicle geometry schema: {schema_version}")

    variant = str(data.get("variant", "")).strip()
    if not variant:
        raise GeometryValidationError("variant is required")

    units = str(data.get("units", "mm")).strip().lower()
    if units != "mm":
        raise GeometryValidationError("Rod Forge v2 geometry currently requires millimetres")

    status = str(data.get("status", "modeling_prior")).strip() or "modeling_prior"
    vehicle = data.get("vehicle", {})
    constraints = data.get("constraints", {})
    notes = data.get("notes", [])

    if not isinstance(vehicle, dict):
        raise GeometryValidationError("vehicle must be a mapping")
    if not isinstance(constraints, dict):
        raise GeometryValidationError("constraints must be a mapping")
    if not isinstance(notes, list):
        raise GeometryValidationError("notes must be a list")

    normalized_constraints: dict[str, dict[str, Any]] = {}
    for task_id, task_constraints in constraints.items():
        if not isinstance(task_id, str) or not task_id.strip():
            raise GeometryValidationError("constraint task ids must be non-empty strings")
        if not isinstance(task_constraints, dict):
            raise GeometryValidationError(f"constraints.{task_id} must be a mapping")
        _validate_ranges(task_constraints, f"constraints.{task_id}")
        normalized_constraints[task_id] = deepcopy(task_constraints)

    _validate_ranges(vehicle, "vehicle")

    return VehicleGeometry(
        schema_version=schema_version,
        variant=variant,
        units=units,
        status=status,
        vehicle=deepcopy(vehicle),
        constraints=normalized_constraints,
        notes=[str(note) for note in notes],
    )


def _validate_ranges(node: Any, path: str) -> None:
    if isinstance(node, dict):
        has_min = "min" in node
        has_max = "max" in node
        if has_min != has_max:
            raise GeometryValidationError(f"{path} ranges require both min and max")
        if has_min and has_max:
            minimum = node["min"]
            maximum = node["max"]
            if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
                raise GeometryValidationError(f"{path} range bounds must be numeric")
            if minimum > maximum:
                raise GeometryValidationError(f"{path} range min cannot exceed max")
            target = node.get("target")
            if target is not None:
                if not isinstance(target, (int, float)):
                    raise GeometryValidationError(f"{path}.target must be numeric")
                if not minimum <= target <= maximum:
                    raise GeometryValidationError(f"{path}.target must lie inside min/max")
        for key, value in node.items():
            _validate_ranges(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _validate_ranges(value, f"{path}[{index}]")

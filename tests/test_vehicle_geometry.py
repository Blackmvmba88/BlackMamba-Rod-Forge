from pathlib import Path

import pytest

from rodforge.vehicle_geometry import GeometryValidationError, load_vehicle_geometry


def test_repo_vehicle_geometry_contract_loads():
    geometry = load_vehicle_geometry("configs/vehicle_geometry.yaml")

    assert geometry.variant == "hotrod_04"
    assert geometry.units == "mm"
    assert geometry.vehicle["overall"]["length_mm"] == 2710
    assert geometry.constraints_for("front_suspension")["type"] == "double_wishbone"
    assert geometry.constraints_for("steering")["ackermann"] is True


def test_geometry_constraints_are_returned_as_copies():
    geometry = load_vehicle_geometry("configs/vehicle_geometry.yaml")
    first = geometry.constraints_for("front_wheels")
    first["outer_diameter_mm"] = 1

    assert geometry.constraints_for("front_wheels")["outer_diameter_mm"] == 580


def test_invalid_range_is_rejected(tmp_path: Path):
    path = tmp_path / "geometry.yaml"
    path.write_text(
        "schema_version: 1\n"
        "variant: broken\n"
        "units: mm\n"
        "constraints:\n"
        "  suspension:\n"
        "    roll_center_mm:\n"
        "      min: 90\n"
        "      max: 50\n",
        encoding="utf-8",
    )

    with pytest.raises(GeometryValidationError):
        load_vehicle_geometry(path)

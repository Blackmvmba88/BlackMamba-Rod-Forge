import pytest

from rodforge.mechanics import derive_mechanical_dimensions


def test_derive_mechanical_dimensions_from_rf_wheel_centers():
    dims = derive_mechanical_dimensions(
        (-1.88, -1.72, 0.76),
        (-1.88, 1.72, 0.76),
        (1.82, -1.75, 0.90),
        (1.82, 1.75, 0.90),
    )

    assert dims.front_axle_x == pytest.approx(-1.88)
    assert dims.rear_axle_x == pytest.approx(1.82)
    assert dims.center_y == pytest.approx(0.0)
    assert dims.front_half_track == pytest.approx(1.72)
    assert dims.rear_half_track == pytest.approx(1.75)
    assert dims.wheelbase == pytest.approx(3.70)


def test_derive_mechanical_dimensions_rejects_zero_wheelbase():
    with pytest.raises(ValueError, match="distinct front and rear axle"):
        derive_mechanical_dimensions(
            (0.0, -1.0, 0.5),
            (0.0, 1.0, 0.5),
            (0.0, -1.0, 0.5),
            (0.0, 1.0, 0.5),
        )

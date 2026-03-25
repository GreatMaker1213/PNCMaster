# last update: 2026-03-23 15:20:00
# modifier: Codex

from usv_sim.guidance.reference import HeadingSpeedReference


def test_heading_speed_reference_fields_and_units() -> None:
    ref = HeadingSpeedReference(desired_heading_error=0.5, desired_surge_speed=2.3)
    assert ref.desired_heading_error == 0.5
    assert ref.desired_surge_speed == 2.3
    assert isinstance(ref.desired_heading_error, float)
    assert isinstance(ref.desired_surge_speed, float)
    assert -3.14 <= ref.desired_heading_error <= 3.14

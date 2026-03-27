# last update: 2026-03-25 10:55:00
# modifier: Codex

from usv_sim.guidance.reference import DesiredVelocityReference, HeadingSpeedReference


def test_heading_speed_reference_fields() -> None:
    ref = HeadingSpeedReference(desired_heading_error=0.5, desired_surge_speed=2.3)
    assert ref.desired_heading_error == 0.5
    assert ref.desired_surge_speed == 2.3


def test_desired_velocity_reference_fields() -> None:
    ref = DesiredVelocityReference(desired_surge_speed=1.5, desired_yaw_rate=0.4)
    assert ref.desired_surge_speed == 1.5
    assert ref.desired_yaw_rate == 0.4

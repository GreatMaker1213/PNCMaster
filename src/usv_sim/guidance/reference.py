# last update: 2026-03-25 11:12:00
# modifier: Codex

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeadingSpeedReference:
    desired_heading_error: float
    desired_surge_speed: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "desired_heading_error", float(self.desired_heading_error))
        object.__setattr__(self, "desired_surge_speed", float(self.desired_surge_speed))


@dataclass(frozen=True)
class DesiredVelocityReference:
    desired_surge_speed: float
    desired_yaw_rate: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "desired_surge_speed", float(self.desired_surge_speed))
        object.__setattr__(self, "desired_yaw_rate", float(self.desired_yaw_rate))


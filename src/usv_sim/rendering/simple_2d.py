# last update: 2026-03-19 09:32:00
# modifier: Claude Code

from __future__ import annotations

import math

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

from usv_sim.core.types import WorldState


class Simple2DRenderer:
    def __init__(self) -> None:
        self._figure: Figure | None = None
        self._axes: Axes | None = None

    def _ensure_canvas(self) -> tuple[Figure, Axes]:
        if self._figure is None or self._axes is None:
            plt.ion()
            self._figure, self._axes = plt.subplots(figsize=(7, 7))
        return self._figure, self._axes

    def _draw_heading(self, axes: Axes, x: float, y: float, psi: float, radius: float, color: str) -> None:
        dx = math.cos(psi) * radius * 1.8
        dy = math.sin(psi) * radius * 1.8
        axes.plot([x, x + dx], [y, y + dy], color=color, linewidth=1.5)

    def render_world(self, world: WorldState, info: dict | None = None):
        figure, axes = self._ensure_canvas()
        axes.clear()

        boundary = world.boundary
        width = boundary.xmax - boundary.xmin
        height = boundary.ymax - boundary.ymin
        axes.add_patch(Rectangle((boundary.xmin, boundary.ymin), width, height, fill=False, edgecolor="black", linewidth=1.5))

        goal = world.goal
        axes.add_patch(Circle((goal.x, goal.y), goal.radius, facecolor="green", edgecolor="green", alpha=0.25, linewidth=1.5))

        for obstacle in world.obstacles:
            axes.add_patch(Circle((obstacle.x, obstacle.y), obstacle.radius, facecolor="gray", edgecolor="black", alpha=0.8))

        attacker = world.attacker
        axes.add_patch(Circle((attacker.x, attacker.y), attacker.radius, facecolor="blue", edgecolor="navy", alpha=0.9))
        self._draw_heading(axes, attacker.x, attacker.y, attacker.psi, attacker.radius, "navy")

        for defender in world.defenders:
            axes.add_patch(Circle((defender.x, defender.y), defender.radius, facecolor="red", edgecolor="darkred", alpha=0.85))
            self._draw_heading(axes, defender.x, defender.y, defender.psi, defender.radius, "darkred")

        title = f"scenario={world.scenario_id} step={world.step_count} t={world.sim_time:.2f}"
        if info is not None:
            goal_distance = info.get("goal_distance")
            termination_reason = info.get("termination_reason", "not_terminated")
            if goal_distance is not None:
                title += f" goal_d={float(goal_distance):.2f} term={termination_reason}"
        axes.set_title(title)
        axes.set_xlim(boundary.xmin - 2.0, boundary.xmax + 2.0)
        axes.set_ylim(boundary.ymin - 2.0, boundary.ymax + 2.0)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        axes.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
        figure.canvas.draw()
        backend = plt.get_backend().lower()
        if "agg" not in backend:
            figure.canvas.flush_events()
            plt.pause(0.001)
        return None

    def close(self) -> None:
        if self._figure is not None:
            plt.close(self._figure)
        self._figure = None
        self._axes = None

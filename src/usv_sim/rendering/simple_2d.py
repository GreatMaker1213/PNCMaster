# last update: 2026-03-20 09:25:00
# modifier: Claude Code

from __future__ import annotations

import math

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle

from usv_sim.core.types import WorldState


class Simple2DRenderer:
    def __init__(self) -> None:
        self._figure: Figure | None = None
        self._axes: Axes | None = None
        self._frame_pause = 0.01
        self._scene_signature: tuple | None = None
        self._boundary_patch: Rectangle | None = None
        self._goal_patch: Circle | None = None
        self._obstacle_patches: list[Circle] = []
        self._attacker_patch: Circle | None = None
        self._attacker_heading: Line2D | None = None
        self._defender_patches: list[Circle] = []
        self._defender_headings: list[Line2D] = []

    def _reset_scene_handles(self) -> None:
        self._scene_signature = None
        self._boundary_patch = None
        self._goal_patch = None
        self._obstacle_patches = []
        self._attacker_patch = None
        self._attacker_heading = None
        self._defender_patches = []
        self._defender_headings = []

    def _ensure_canvas(self) -> tuple[Figure, Axes]:
        if self._figure is not None and not plt.fignum_exists(self._figure.number):
            self._figure = None
            self._axes = None
            self._reset_scene_handles()

        if self._figure is None or self._axes is None:
            plt.ion()
            self._figure, self._axes = plt.subplots(figsize=(8.5, 8.5), dpi=90)
            manager = getattr(self._figure.canvas, "manager", None)
            if manager is not None and hasattr(manager, "set_window_title"):
                manager.set_window_title("USV Sim V0.2")
            
            # 保守式设置画布尺寸，跳过，默认的自适应即可
            # window = getattr(manager, "window", None)
            # if window is not None and hasattr(window, "minsize"):
            #     window.minsize(900, 900)
            # if window is not None and hasattr(window, "wm_geometry"):
            #     window.wm_geometry("960x960")
            # elif manager is not None and hasattr(manager, "resize"):
            #     manager.resize(960, 960)
            self._figure.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.93)
            
            # 本意是只有在使用可交互后端的时候才show，但是判断逻辑不正确
            # 考虑到大多数情况都在win下进行，且默认后端可交互，所以跳过判断
            # backend = plt.get_backend().lower()
            # if "agg" not in backend:  ，
            #     print("plt show block")
            #     plt.show(block=False)
            plt.show(block=False)
        return self._figure, self._axes

    def _make_scene_signature(self, world: WorldState) -> tuple:
        boundary = world.boundary
        goal = world.goal
        obstacle_signature = tuple(
            (obstacle.entity_id, obstacle.x, obstacle.y, obstacle.radius) for obstacle in world.obstacles
        )
        defender_signature = tuple((defender.entity_id, defender.radius) for defender in world.defenders)
        return (
            world.scenario_id,
            world.seed,
            boundary.xmin,
            boundary.xmax,
            boundary.ymin,
            boundary.ymax,
            goal.x,
            goal.y,
            goal.radius,
            obstacle_signature,
            defender_signature,
        )

    def _set_heading_line(self, line: Line2D, x: float, y: float, psi: float, radius: float) -> None:
        dx = math.cos(psi) * radius * 1.8
        dy = math.sin(psi) * radius * 1.8
        line.set_data([x, x + dx], [y, y + dy])

    def _setup_scene(self, world: WorldState) -> None:
        _, axes = self._ensure_canvas()
        self._reset_scene_handles()
        axes.clear()
        axes.set_facecolor("#f7f9fb")

        boundary = world.boundary
        width = boundary.xmax - boundary.xmin
        height = boundary.ymax - boundary.ymin
        self._boundary_patch = Rectangle(
            (boundary.xmin, boundary.ymin),
            width,
            height,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
        )
        axes.add_patch(self._boundary_patch)

        goal = world.goal
        self._goal_patch = Circle(
            (goal.x, goal.y),
            goal.radius,
            facecolor="green",
            edgecolor="green",
            alpha=0.25,
            linewidth=1.5,
        )
        axes.add_patch(self._goal_patch)

        self._obstacle_patches = []
        for obstacle in world.obstacles:
            patch = Circle(
                (obstacle.x, obstacle.y),
                obstacle.radius,
                facecolor="gray",
                edgecolor="black",
                alpha=0.8,
            )
            axes.add_patch(patch)
            self._obstacle_patches.append(patch)

        attacker = world.attacker
        self._attacker_patch = Circle(
            (attacker.x, attacker.y),
            attacker.radius,
            facecolor="blue",
            edgecolor="navy",
            alpha=0.9,
        )
        axes.add_patch(self._attacker_patch)
        self._attacker_heading = axes.plot([], [], color="navy", linewidth=1.8)[0]

        self._defender_patches = []
        self._defender_headings = []
        for defender in world.defenders:
            patch = Circle(
                (defender.x, defender.y),
                defender.radius,
                facecolor="red",
                edgecolor="darkred",
                alpha=0.85,
            )
            axes.add_patch(patch)
            heading = axes.plot([], [], color="darkred", linewidth=1.6)[0]
            self._defender_patches.append(patch)
            self._defender_headings.append(heading)

        axes.set_xlim(boundary.xmin - 2.0, boundary.xmax + 2.0)
        axes.set_ylim(boundary.ymin - 2.0, boundary.ymax + 2.0)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlabel("x")
        axes.set_ylabel("y")
        axes.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
        self._scene_signature = self._make_scene_signature(world)
        self._update_dynamic_artists(world)

    def _update_dynamic_artists(self, world: WorldState) -> None:
        if self._attacker_patch is None or self._attacker_heading is None:
            raise RuntimeError("renderer scene must be initialized before updating artists")

        attacker = world.attacker
        self._attacker_patch.center = (attacker.x, attacker.y)
        self._set_heading_line(self._attacker_heading, attacker.x, attacker.y, attacker.psi, attacker.radius)

        for patch, heading, defender in zip(self._defender_patches, self._defender_headings, world.defenders):
            patch.center = (defender.x, defender.y)
            self._set_heading_line(heading, defender.x, defender.y, defender.psi, defender.radius)

    def render_world(self, world: WorldState, info: dict | None = None):
        figure, axes = self._ensure_canvas()
        if self._scene_signature != self._make_scene_signature(world):
            self._setup_scene(world)
            figure, axes = self._ensure_canvas()

        self._update_dynamic_artists(world)

        title = f"scenario={world.scenario_id} step={world.step_count} t={world.sim_time:.2f}"
        if info is not None:
            goal_distance = info.get("goal_distance")
            termination_reason = info.get("termination_reason", "not_terminated")
            if goal_distance is not None:
                title += f" goal_d={float(goal_distance):.2f} term={termination_reason}"
        axes.set_title(title)

        figure.canvas.draw()
        backend = plt.get_backend().lower()
        # 在win下后端默认为TkAgg，可交互，跳过判断
        # if "agg" not in backend:
        #     figure.canvas.flush_events()
        #     plt.pause(self._frame_pause)
        figure.canvas.flush_events()
        plt.pause(self._frame_pause)

        return None

    def close(self) -> None:
        if self._figure is not None:
            plt.close(self._figure)
        self._figure = None
        self._axes = None
        self._reset_scene_handles()

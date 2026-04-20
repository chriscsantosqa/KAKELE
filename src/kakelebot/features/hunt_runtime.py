from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.config import HuntWaypoint
from kakelebot.core.input import KeyAction


@dataclass(frozen=True, slots=True)
class HuntCycleAction:
    action: KeyAction | None
    status: str
    waypoint_index: int
    total_waypoints: int
    relative_x: int
    relative_y: int
    completed_loops: int


class HuntRuntime:
    _DELTAS = {
        "UP": (0, -1),
        "DOWN": (0, 1),
        "LEFT": (-1, 0),
        "RIGHT": (1, 0),
    }

    _MOVEMENT_HOLD_SECONDS = 0.035

    def __init__(self) -> None:
        self._last_waypoint_at: float | None = None
        self._waypoint_index = 0
        self._waypoint_repeat_progress = 0
        self._last_route_signature: tuple | None = None
        self._relative_x = 0
        self._relative_y = 0
        self._completed_loops = 0

    def next_action(
        self,
        *,
        enabled: bool,
        loop_route: bool,
        waypoint_interval_seconds: float,
        move_up_hotkey: str,
        move_down_hotkey: str,
        move_left_hotkey: str,
        move_right_hotkey: str,
        use_coordinate_navigation: bool,
        coordinate_tolerance: int,
        player_position: tuple[int, int, int] | None,
        waypoints: list[HuntWaypoint],
        now: float,
    ) -> HuntCycleAction:
        total_waypoints = len(waypoints)
        if not enabled:
            self._reset_if_route_changed(None)
            return HuntCycleAction(None, "disabled", -1, 0, 0, 0, 0)
        if not waypoints:
            self._reset_if_route_changed(tuple())
            return HuntCycleAction(None, "no-waypoints", -1, 0, 0, 0, 0)

        route_signature = tuple(
            (
                waypoint.direction,
                waypoint.repeats,
                waypoint.relative_x,
                waypoint.relative_y,
                waypoint.target_x,
                waypoint.target_y,
                waypoint.target_z,
            )
            for waypoint in waypoints
        )
        self._reset_if_route_changed(route_signature)

        if self._last_waypoint_at is not None and (now - self._last_waypoint_at) < waypoint_interval_seconds:
            return self.snapshot(total_waypoints=total_waypoints, status="cooldown")

        if self._waypoint_index >= total_waypoints:
            if not loop_route:
                last_waypoint = waypoints[-1]
                return HuntCycleAction(
                    action=None,
                    status="completed",
                    waypoint_index=total_waypoints - 1,
                    total_waypoints=total_waypoints,
                    relative_x=last_waypoint.relative_x,
                    relative_y=last_waypoint.relative_y,
                    completed_loops=self._completed_loops,
                )
            self._waypoint_index = 0
            self._waypoint_repeat_progress = 0
            self._relative_x = 0
            self._relative_y = 0
            self._completed_loops += 1

        current_waypoint_index = self._waypoint_index
        waypoint = waypoints[current_waypoint_index]

        if use_coordinate_navigation and player_position is not None and self._waypoint_has_coordinates(waypoint):
            cycle = self._next_coordinate_action(
                waypoint=waypoint,
                current_waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                coordinate_tolerance=coordinate_tolerance,
                player_position=player_position,
                move_up_hotkey=move_up_hotkey,
                move_down_hotkey=move_down_hotkey,
                move_left_hotkey=move_left_hotkey,
                move_right_hotkey=move_right_hotkey,
                loop_route=loop_route,
                now=now,
            )
            if cycle is not None:
                return cycle

        hotkey = self._direction_hotkey(
            waypoint.direction,
            move_up_hotkey=move_up_hotkey,
            move_down_hotkey=move_down_hotkey,
            move_left_hotkey=move_left_hotkey,
            move_right_hotkey=move_right_hotkey,
        )
        if not hotkey:
            return HuntCycleAction(
                action=None,
                status="missing-direction-hotkey",
                waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
                completed_loops=self._completed_loops,
            )

        delta_x, delta_y = self._direction_delta(waypoint.direction)
        self._relative_x += delta_x
        self._relative_y += delta_y

        action = KeyAction(
            key=hotkey,
            reason=f"hunt-waypoint-{current_waypoint_index}-{waypoint.direction}",
            hold_seconds=self._MOVEMENT_HOLD_SECONDS,
        )

        self._last_waypoint_at = now
        self._waypoint_repeat_progress += 1
        if self._waypoint_repeat_progress >= max(1, waypoint.repeats):
            self._waypoint_index += 1
            self._waypoint_repeat_progress = 0
            if loop_route and self._waypoint_index >= total_waypoints:
                self._waypoint_index = 0
                self._relative_x = 0
                self._relative_y = 0
                self._completed_loops += 1

        return HuntCycleAction(
            action=action,
            status="executed",
            waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            relative_x=self._relative_x,
            relative_y=self._relative_y,
            completed_loops=self._completed_loops,
        )

    def _next_coordinate_action(
        self,
        *,
        waypoint: HuntWaypoint,
        current_waypoint_index: int,
        total_waypoints: int,
        coordinate_tolerance: int,
        player_position: tuple[int, int, int],
        move_up_hotkey: str,
        move_down_hotkey: str,
        move_left_hotkey: str,
        move_right_hotkey: str,
        loop_route: bool,
        now: float,
    ) -> HuntCycleAction | None:
        target_z = waypoint.target_z if waypoint.target_z is not None else player_position[2]
        if target_z != player_position[2]:
            return HuntCycleAction(
                action=None,
                status="z-mismatch",
                waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
                completed_loops=self._completed_loops,
            )

        delta_x = (waypoint.target_x or 0) - player_position[0]
        delta_y = (waypoint.target_y or 0) - player_position[1]
        tolerance = max(0, coordinate_tolerance)

        if abs(delta_x) <= tolerance and abs(delta_y) <= tolerance:
            self._advance_waypoint_after_coordinate_match(loop_route=loop_route, total_waypoints=total_waypoints)
            return HuntCycleAction(
                action=None,
                status="waypoint-reached",
                waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
                completed_loops=self._completed_loops,
            )

        direction = self._direction_from_delta(delta_x=delta_x, delta_y=delta_y)
        hotkey = self._direction_hotkey(
            direction,
            move_up_hotkey=move_up_hotkey,
            move_down_hotkey=move_down_hotkey,
            move_left_hotkey=move_left_hotkey,
            move_right_hotkey=move_right_hotkey,
        )
        if not hotkey:
            return HuntCycleAction(
                action=None,
                status="missing-direction-hotkey",
                waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
                completed_loops=self._completed_loops,
            )

        self._last_waypoint_at = now
        return HuntCycleAction(
            action=KeyAction(
                key=hotkey,
                reason=f"hunt-coordinate-{current_waypoint_index}-{direction}",
                hold_seconds=self._MOVEMENT_HOLD_SECONDS,
            ),
            status="coordinate-executed",
            waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            relative_x=self._relative_x,
            relative_y=self._relative_y,
            completed_loops=self._completed_loops,
        )

    def _advance_waypoint_after_coordinate_match(self, *, loop_route: bool, total_waypoints: int) -> None:
        self._waypoint_index += 1
        self._waypoint_repeat_progress = 0
        if loop_route and self._waypoint_index >= total_waypoints:
            self._waypoint_index = 0
            self._relative_x = 0
            self._relative_y = 0
            self._completed_loops += 1

    def snapshot(self, *, total_waypoints: int, status: str = "snapshot") -> HuntCycleAction:
        current_index = self._waypoint_index if total_waypoints > 0 else -1
        if total_waypoints > 0 and current_index >= total_waypoints:
            current_index = total_waypoints - 1
        return HuntCycleAction(
            action=None,
            status=status,
            waypoint_index=current_index,
            total_waypoints=total_waypoints,
            relative_x=self._relative_x,
            relative_y=self._relative_y,
            completed_loops=self._completed_loops,
        )

    def _reset_if_route_changed(self, route_signature: tuple | None) -> None:
        if route_signature == self._last_route_signature:
            return
        self._last_route_signature = route_signature
        self._last_waypoint_at = None
        self._waypoint_index = 0
        self._waypoint_repeat_progress = 0
        self._relative_x = 0
        self._relative_y = 0
        self._completed_loops = 0

    @staticmethod
    def _waypoint_has_coordinates(waypoint: HuntWaypoint) -> bool:
        return waypoint.target_x is not None and waypoint.target_y is not None

    @staticmethod
    def _direction_hotkey(
        direction: str,
        *,
        move_up_hotkey: str,
        move_down_hotkey: str,
        move_left_hotkey: str,
        move_right_hotkey: str,
    ) -> str:
        normalized = direction.strip().upper()
        mapping = {
            "UP": move_up_hotkey,
            "DOWN": move_down_hotkey,
            "LEFT": move_left_hotkey,
            "RIGHT": move_right_hotkey,
        }
        return mapping.get(normalized, "")

    @classmethod
    def _direction_delta(cls, direction: str) -> tuple[int, int]:
        return cls._DELTAS[direction.strip().upper()]

    @staticmethod
    def _direction_from_delta(*, delta_x: int, delta_y: int) -> str:
        if abs(delta_x) >= abs(delta_y):
            return "RIGHT" if delta_x > 0 else "LEFT"
        return "DOWN" if delta_y > 0 else "UP"

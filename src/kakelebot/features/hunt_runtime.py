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
    current_section: str


class HuntRuntime:
    _DELTAS = {
        "UP": (0, -1),
        "DOWN": (0, 1),
        "LEFT": (-1, 0),
        "RIGHT": (1, 0),
    }
    _RESYNC_DISTANCE_THRESHOLD = 6
    _MOVEMENT_HOLD_SECONDS = 0.035

    def __init__(self) -> None:
        self._last_waypoint_at: float | None = None
        self._waypoint_index = 0
        self._waypoint_repeat_progress = 0
        self._last_route_signature: tuple | None = None
        self._relative_x = 0
        self._relative_y = 0
        self._completed_loops = 0
        self._waypoint_hold_until: float | None = None
        self._waypoint_action_executed = False

    def current_section(self, waypoints: list[HuntWaypoint]) -> str:
        return self._current_section(waypoints)

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
            return HuntCycleAction(None, "disabled", -1, 0, 0, 0, 0, "idle")
        if not waypoints:
            self._reset_if_route_changed(tuple())
            return HuntCycleAction(None, "no-waypoints", -1, 0, 0, 0, 0, "idle")

        route_signature = tuple(
            (
                waypoint.direction,
                waypoint.repeats,
                waypoint.relative_x,
                waypoint.relative_y,
                waypoint.target_x,
                waypoint.target_y,
                waypoint.target_z,
                waypoint.waypoint_type,
                waypoint.label,
                waypoint.waypoint_range,
                waypoint.wait_time_ms,
                waypoint.action_key,
                waypoint.section,
            )
            for waypoint in waypoints
        )
        self._reset_if_route_changed(route_signature)

        if use_coordinate_navigation and player_position is not None:
            if self._try_resync_to_nearest_waypoint(
                player_position=player_position,
                waypoints=waypoints,
                coordinate_tolerance=coordinate_tolerance,
            ):
                self._last_waypoint_at = None

        current_section = self._current_section(waypoints)

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
                    current_section=last_waypoint.section,
                )
            self._waypoint_index = 0
            self._waypoint_repeat_progress = 0
            self._relative_x = 0
            self._relative_y = 0
            self._completed_loops += 1
            current_section = self._current_section(waypoints)

        current_waypoint_index = self._waypoint_index
        waypoint = waypoints[current_waypoint_index]
        current_section = waypoint.section

        coordinate_mode_active = (
            use_coordinate_navigation
            and player_position is not None
            and self._waypoint_has_coordinates(waypoint)
        )

        if not coordinate_mode_active and self._last_waypoint_at is not None and (now - self._last_waypoint_at) < waypoint_interval_seconds:
            return self.snapshot(total_waypoints=total_waypoints, status="cooldown", current_section=current_section)

        if coordinate_mode_active:
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
                current_section=current_section,
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
            self._advance_waypoint(loop_route=loop_route, total_waypoints=total_waypoints)

        return HuntCycleAction(
            action=action,
            status="executed",
            waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            relative_x=self._relative_x,
            relative_y=self._relative_y,
            completed_loops=self._completed_loops,
            current_section=current_section,
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
        delta_x = (waypoint.target_x or 0) - player_position[0]
        delta_y = (waypoint.target_y or 0) - player_position[1]
        tolerance = max(coordinate_tolerance, max(0, waypoint.waypoint_range - 1))

        if abs(delta_x) <= tolerance and abs(delta_y) <= tolerance:
            if waypoint.waypoint_type in {"stand", "action", "use", "floor-change"}:
                return self._handle_operational_waypoint(
                    waypoint=waypoint,
                    current_waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    loop_route=loop_route,
                    now=now,
                    player_position=player_position,
                )

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
                    current_section=waypoint.section,
                )

            self._advance_waypoint(loop_route=loop_route, total_waypoints=total_waypoints)
            return HuntCycleAction(
                action=None,
                status="waypoint-reached",
                waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
                completed_loops=self._completed_loops,
                current_section=waypoint.section,
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
                current_section=waypoint.section,
            )

        self._last_waypoint_at = now
        return HuntCycleAction(
            action=KeyAction(
                key=hotkey,
                reason=f"hunt-coordinate-{current_waypoint_index}-{direction}",
                hold_seconds=self._MOVEMENT_HOLD_SECONDS,
            ),
            status="coordinate-moving",
            waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            relative_x=self._relative_x,
            relative_y=self._relative_y,
            completed_loops=self._completed_loops,
            current_section=waypoint.section,
        )

    def _handle_operational_waypoint(
        self,
        *,
        waypoint: HuntWaypoint,
        current_waypoint_index: int,
        total_waypoints: int,
        loop_route: bool,
        now: float,
        player_position: tuple[int, int, int],
    ) -> HuntCycleAction:
        if waypoint.waypoint_type == "stand":
            if self._waypoint_hold_until is None:
                self._waypoint_hold_until = now + (max(0, waypoint.wait_time_ms) / 1000.0)
                return self._build_status_cycle(
                    status="stand-wait",
                    current_waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    current_section=waypoint.section,
                )
            if now < self._waypoint_hold_until:
                return self._build_status_cycle(
                    status="stand-wait",
                    current_waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    current_section=waypoint.section,
                )
            self._clear_waypoint_operation_state()
            self._advance_waypoint(loop_route=loop_route, total_waypoints=total_waypoints)
            return self._build_status_cycle(
                status="stand-complete",
                current_waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                current_section=waypoint.section,
            )

        if waypoint.waypoint_type in {"action", "use"}:
            status_prefix = waypoint.waypoint_type
            if not waypoint.action_key.strip():
                self._advance_waypoint(loop_route=loop_route, total_waypoints=total_waypoints)
                return self._build_status_cycle(
                    status=f"{status_prefix}-missing-key",
                    current_waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    current_section=waypoint.section,
                )
            if not self._waypoint_action_executed:
                self._waypoint_action_executed = True
                self._waypoint_hold_until = now + (max(0, waypoint.wait_time_ms) / 1000.0)
                self._last_waypoint_at = now
                return HuntCycleAction(
                    action=KeyAction(
                        key=waypoint.action_key,
                        reason=f"hunt-{status_prefix}-{current_waypoint_index}-{waypoint.label or status_prefix}",
                        hold_seconds=self._MOVEMENT_HOLD_SECONDS,
                    ),
                    status=f"{status_prefix}-executed",
                    waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    relative_x=self._relative_x,
                    relative_y=self._relative_y,
                    completed_loops=self._completed_loops,
                    current_section=waypoint.section,
                )
            if self._waypoint_hold_until is not None and now < self._waypoint_hold_until:
                return self._build_status_cycle(
                    status=f"{status_prefix}-wait",
                    current_waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    current_section=waypoint.section,
                )
            self._clear_waypoint_operation_state()
            self._advance_waypoint(loop_route=loop_route, total_waypoints=total_waypoints)
            return self._build_status_cycle(
                status=f"{status_prefix}-complete",
                current_waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                current_section=waypoint.section,
            )

        if waypoint.waypoint_type == "floor-change":
            target_z = waypoint.target_z if waypoint.target_z is not None else player_position[2]
            if player_position[2] == target_z:
                self._clear_waypoint_operation_state()
                self._advance_waypoint(loop_route=loop_route, total_waypoints=total_waypoints)
                return self._build_status_cycle(
                    status="floor-change-complete",
                    current_waypoint_index=current_waypoint_index,
                    total_waypoints=total_waypoints,
                    current_section=waypoint.section,
                )

            if self._waypoint_hold_until is None and waypoint.wait_time_ms > 0:
                self._waypoint_hold_until = now + (waypoint.wait_time_ms / 1000.0)

            if self._waypoint_hold_until is not None and now >= self._waypoint_hold_until:
                self._waypoint_hold_until = now + (max(250, waypoint.wait_time_ms) / 1000.0)

            return self._build_status_cycle(
                status="floor-change-wait",
                current_waypoint_index=current_waypoint_index,
                total_waypoints=total_waypoints,
                current_section=waypoint.section,
            )

        return self._build_status_cycle(
            status="unsupported-waypoint-type",
            current_waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            current_section=waypoint.section,
        )

    def _try_resync_to_nearest_waypoint(
        self,
        *,
        player_position: tuple[int, int, int],
        waypoints: list[HuntWaypoint],
        coordinate_tolerance: int,
    ) -> bool:
        current_waypoint = waypoints[min(max(self._waypoint_index, 0), len(waypoints) - 1)]
        if not self._waypoint_has_coordinates(current_waypoint):
            return False

        current_distance = self._waypoint_distance(player_position, current_waypoint)
        tolerance = max(coordinate_tolerance, max(0, current_waypoint.waypoint_range - 1))
        if current_distance <= max(tolerance, self._RESYNC_DISTANCE_THRESHOLD):
            return False

        nearest_index = self._nearest_waypoint_index(player_position, waypoints)
        if nearest_index is None or nearest_index == self._waypoint_index:
            return False

        self._waypoint_index = nearest_index
        self._waypoint_repeat_progress = 0
        self._clear_waypoint_operation_state()
        return True

    def _nearest_waypoint_index(
        self,
        player_position: tuple[int, int, int],
        waypoints: list[HuntWaypoint],
    ) -> int | None:
        best_index: int | None = None
        best_distance: int | None = None
        for index, waypoint in enumerate(waypoints):
            if not self._waypoint_has_coordinates(waypoint):
                continue
            distance = self._waypoint_distance(player_position, waypoint)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_index = index
        return best_index

    @staticmethod
    def _waypoint_distance(player_position: tuple[int, int, int], waypoint: HuntWaypoint) -> int:
        waypoint_x = waypoint.target_x or 0
        waypoint_y = waypoint.target_y or 0
        waypoint_z = waypoint.target_z if waypoint.target_z is not None else player_position[2]
        return (
            abs(player_position[0] - waypoint_x)
            + abs(player_position[1] - waypoint_y)
            + (abs(player_position[2] - waypoint_z) * 10)
        )

    def _advance_waypoint(self, *, loop_route: bool, total_waypoints: int) -> None:
        self._waypoint_index += 1
        self._waypoint_repeat_progress = 0
        self._clear_waypoint_operation_state()
        if loop_route and self._waypoint_index >= total_waypoints:
            self._waypoint_index = 0
            self._relative_x = 0
            self._relative_y = 0
            self._completed_loops += 1

    def _build_status_cycle(
        self,
        *,
        status: str,
        current_waypoint_index: int,
        total_waypoints: int,
        current_section: str,
    ) -> HuntCycleAction:
        return HuntCycleAction(
            action=None,
            status=status,
            waypoint_index=current_waypoint_index,
            total_waypoints=total_waypoints,
            relative_x=self._relative_x,
            relative_y=self._relative_y,
            completed_loops=self._completed_loops,
            current_section=current_section,
        )

    def _clear_waypoint_operation_state(self) -> None:
        self._waypoint_hold_until = None
        self._waypoint_action_executed = False

    def snapshot(self, *, total_waypoints: int, status: str = "snapshot", current_section: str = "hunt") -> HuntCycleAction:
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
            current_section=current_section,
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
        self._clear_waypoint_operation_state()

    def _current_section(self, waypoints: list[HuntWaypoint]) -> str:
        if not waypoints:
            return "idle"
        index = min(max(self._waypoint_index, 0), len(waypoints) - 1)
        return waypoints[index].section

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

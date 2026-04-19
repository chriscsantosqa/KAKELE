from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.config import HuntWaypoint
from kakelebot.core.input import KeyAction


@dataclass(frozen=True, slots=True)
class HuntCycleAction:
    action: KeyAction | None
    status: str
    waypoint_index: int


class HuntRuntime:
    def __init__(self) -> None:
        self._last_waypoint_at: float | None = None
        self._waypoint_index = 0
        self._waypoint_repeat_progress = 0
        self._last_route_signature: tuple | None = None

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
        waypoints: list[HuntWaypoint],
        now: float,
    ) -> HuntCycleAction:
        if not enabled:
            self._reset_if_route_changed(None)
            return HuntCycleAction(action=None, status="disabled", waypoint_index=-1)
        if not waypoints:
            self._reset_if_route_changed(tuple())
            return HuntCycleAction(action=None, status="no-waypoints", waypoint_index=-1)

        route_signature = tuple((waypoint.direction, waypoint.repeats) for waypoint in waypoints)
        self._reset_if_route_changed(route_signature)

        if self._last_waypoint_at is not None:
            if (now - self._last_waypoint_at) < waypoint_interval_seconds:
                return HuntCycleAction(
                    action=None,
                    status="cooldown",
                    waypoint_index=self._waypoint_index,
                )

        if self._waypoint_index >= len(waypoints):
            if not loop_route:
                return HuntCycleAction(action=None, status="completed", waypoint_index=len(waypoints) - 1)
            self._waypoint_index = 0
            self._waypoint_repeat_progress = 0

        waypoint = waypoints[self._waypoint_index]
        hotkey = self._direction_hotkey(
            waypoint.direction,
            move_up_hotkey=move_up_hotkey,
            move_down_hotkey=move_down_hotkey,
            move_left_hotkey=move_left_hotkey,
            move_right_hotkey=move_right_hotkey,
        )
        if not hotkey:
            return HuntCycleAction(action=None, status="missing-direction-hotkey", waypoint_index=self._waypoint_index)

        action = KeyAction(
            key=hotkey,
            reason=f"hunt-waypoint-{self._waypoint_index}-{waypoint.direction}",
        )
        self._last_waypoint_at = now
        self._waypoint_repeat_progress += 1
        if self._waypoint_repeat_progress >= max(1, waypoint.repeats):
            self._waypoint_index += 1
            self._waypoint_repeat_progress = 0
            if loop_route and self._waypoint_index >= len(waypoints):
                self._waypoint_index = 0
        return HuntCycleAction(action=action, status="executed", waypoint_index=self._waypoint_index)

    def _reset_if_route_changed(self, route_signature: tuple | None) -> None:
        if route_signature == self._last_route_signature:
            return
        self._last_route_signature = route_signature
        self._last_waypoint_at = None
        self._waypoint_index = 0
        self._waypoint_repeat_progress = 0

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

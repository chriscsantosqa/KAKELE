from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.config import HuntWaypoint


@dataclass(frozen=True, slots=True)
class RecordedRoute:
    waypoints: tuple[HuntWaypoint, ...]


class RouteRecorder:
    def __init__(self, minimum_step_distance: int = 1) -> None:
        self._minimum_step_distance = max(1, minimum_step_distance)
        self._positions: list[tuple[int, int, int]] = []

    def start(self) -> None:
        self._positions.clear()

    def record_position(self, position: tuple[int, int, int] | None) -> bool:
        if position is None:
            return False
        if not self._positions:
            self._positions.append(position)
            return True

        last_x, last_y, last_z = self._positions[-1]
        current_x, current_y, current_z = position
        if current_z != last_z:
            self._positions.append(position)
            return True

        distance = abs(current_x - last_x) + abs(current_y - last_y)
        if distance < self._minimum_step_distance:
            return False

        self._positions.append(position)
        return True

    def stop(self) -> RecordedRoute:
        return RecordedRoute(waypoints=tuple(self._to_waypoints(self._positions)))

    def snapshot(self) -> RecordedRoute:
        return RecordedRoute(waypoints=tuple(self._to_waypoints(self._positions)))

    @staticmethod
    def _to_waypoints(positions: list[tuple[int, int, int]]) -> list[HuntWaypoint]:
        waypoints: list[HuntWaypoint] = []
        for index, position in enumerate(positions):
            direction = "RIGHT"
            if index > 0:
                direction = RouteRecorder._direction_between(positions[index - 1], position)
            waypoints.append(
                HuntWaypoint(
                    direction=direction,
                    repeats=1,
                    relative_x=0,
                    relative_y=0,
                    target_x=position[0],
                    target_y=position[1],
                    target_z=position[2],
                )
            )
        return waypoints

    @staticmethod
    def _direction_between(
        previous: tuple[int, int, int],
        current: tuple[int, int, int],
    ) -> str:
        delta_x = current[0] - previous[0]
        delta_y = current[1] - previous[1]
        if abs(delta_x) >= abs(delta_y):
            return "RIGHT" if delta_x >= 0 else "LEFT"
        return "DOWN" if delta_y >= 0 else "UP"

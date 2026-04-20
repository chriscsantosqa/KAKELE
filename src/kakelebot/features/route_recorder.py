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
        return RecordedRoute(waypoints=tuple(self._to_waypoints(self._compact_positions(self._positions))))

    def snapshot(self) -> RecordedRoute:
        return RecordedRoute(waypoints=tuple(self._to_waypoints(self._compact_positions(self._positions))))

    @classmethod
    def _compact_positions(
        cls,
        positions: list[tuple[int, int, int]],
    ) -> list[tuple[int, int, int]]:
        if len(positions) <= 2:
            return list(positions)

        compacted: list[tuple[int, int, int]] = [positions[0]]
        for index in range(1, len(positions) - 1):
            previous = positions[index - 1]
            current = positions[index]
            next_position = positions[index + 1]

            if current[2] != previous[2] or next_position[2] != current[2]:
                compacted.append(current)
                continue

            previous_direction = cls._direction_between(previous, current)
            next_direction = cls._direction_between(current, next_position)
            if previous_direction != next_direction:
                compacted.append(current)

        compacted.append(positions[-1])
        return compacted

    @classmethod
    def _to_waypoints(cls, positions: list[tuple[int, int, int]]) -> list[HuntWaypoint]:
        waypoints: list[HuntWaypoint] = []
        for index, position in enumerate(positions):
            direction = "RIGHT"
            waypoint_type = "node"
            label = f"node-{index}"

            if index > 0:
                direction = cls._direction_between(positions[index - 1], position)
            if index == 0:
                waypoint_type = "start"
                label = "start"
            elif index == len(positions) - 1:
                waypoint_type = "stand"
                label = "end"

            waypoints.append(
                HuntWaypoint(
                    direction=direction,
                    repeats=1,
                    relative_x=0,
                    relative_y=0,
                    target_x=position[0],
                    target_y=position[1],
                    target_z=position[2],
                    waypoint_type=waypoint_type,
                    label=label,
                    waypoint_range=1,
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

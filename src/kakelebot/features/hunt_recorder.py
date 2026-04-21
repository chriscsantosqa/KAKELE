from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from kakelebot.core.config import HuntWaypoint
from kakelebot.features.route_recorder import RouteRecorder


@dataclass(frozen=True, slots=True)
class HuntRecordingSnapshot:
    is_recording: bool
    relative_x: int
    relative_y: int
    total_steps: int
    waypoints: tuple[HuntWaypoint, ...]
    status: str


class HuntRecorder:
    def __init__(self) -> None:
        self._lock = Lock()
        self._is_recording = False
        self._status = "idle"
        self._route_recorder = RouteRecorder(minimum_step_distance=1)
        self._origin_position: tuple[int, int, int] | None = None
        self._current_position: tuple[int, int, int] | None = None
        self._total_steps = 0

    def start(
        self,
        *,
        move_up_hotkey: str,
        move_down_hotkey: str,
        move_left_hotkey: str,
        move_right_hotkey: str,
        origin_position: tuple[int, int, int] | None = None,
    ) -> None:
        del move_up_hotkey, move_down_hotkey, move_left_hotkey, move_right_hotkey
        with self._lock:
            self._is_recording = True
            self._status = "recording"
            self._origin_position = origin_position
            self._current_position = origin_position
            self._total_steps = 0
            self._route_recorder.start()
            if origin_position is not None:
                self._route_recorder.record_position(origin_position)

    def stop(self) -> list[HuntWaypoint]:
        with self._lock:
            self._is_recording = False
            self._status = "stopped"
            recorded_route = self._route_recorder.stop()
            return [
                HuntWaypoint(
                    direction=waypoint.direction,
                    repeats=waypoint.repeats,
                    relative_x=waypoint.relative_x,
                    relative_y=waypoint.relative_y,
                    target_x=waypoint.target_x,
                    target_y=waypoint.target_y,
                    target_z=waypoint.target_z,
                    waypoint_type=waypoint.waypoint_type,
                    label=waypoint.label,
                    waypoint_range=waypoint.waypoint_range,
                    wait_time_ms=waypoint.wait_time_ms,
                    action_key=waypoint.action_key,
                    section=waypoint.section,
                )
                for waypoint in recorded_route.waypoints
            ]

    def record_position(self, position: tuple[int, int, int] | None) -> bool:
        with self._lock:
            if not self._is_recording:
                return False
            if position is None:
                self._status = "waiting-memory-position"
                return False
            if self._origin_position is None:
                self._origin_position = position
            self._current_position = position
            recorded = self._route_recorder.record_position(position)
            if recorded:
                self._total_steps += 1
                self._status = "recording"
            return recorded

    def snapshot(self) -> HuntRecordingSnapshot:
        with self._lock:
            recorded_route = self._route_recorder.snapshot()
            relative_x = 0
            relative_y = 0
            if self._origin_position is not None and self._current_position is not None:
                relative_x = self._current_position[0] - self._origin_position[0]
                relative_y = self._current_position[1] - self._origin_position[1]
            return HuntRecordingSnapshot(
                is_recording=self._is_recording,
                relative_x=relative_x,
                relative_y=relative_y,
                total_steps=self._total_steps,
                waypoints=recorded_route.waypoints,
                status=self._status,
            )

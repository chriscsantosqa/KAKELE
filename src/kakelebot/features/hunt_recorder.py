from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from kakelebot.core.config import HuntWaypoint

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover
    keyboard = None


@dataclass(frozen=True, slots=True)
class HuntRecordingSnapshot:
    is_recording: bool
    relative_x: int
    relative_y: int
    total_steps: int
    waypoints: tuple[HuntWaypoint, ...]
    status: str


class HuntRecorder:
    _DELTAS = {
        "UP": (0, -1),
        "DOWN": (0, 1),
        "LEFT": (-1, 0),
        "RIGHT": (1, 0),
    }

    _SPECIAL_KEYS = {
        "up": "UP",
        "down": "DOWN",
        "left": "LEFT",
        "right": "RIGHT",
        "space": "SPACE",
        "enter": "ENTER",
        "esc": "ESC",
        "page_up": "PAGEUP",
        "page_down": "PAGEDOWN",
        "backspace": "BACKSPACE",
    }

    def __init__(self) -> None:
        self._lock = Lock()
        self._listener = None
        self._is_recording = False
        self._hotkey_to_direction: dict[str, str] = {}
        self._waypoints: list[HuntWaypoint] = []
        self._relative_x = 0
        self._relative_y = 0
        self._total_steps = 0
        self._status = "idle"

    def start(
        self,
        *,
        move_up_hotkey: str,
        move_down_hotkey: str,
        move_left_hotkey: str,
        move_right_hotkey: str,
    ) -> None:
        if keyboard is None:
            raise RuntimeError("pynput is not installed.")

        self.stop()

        hotkey_map = {
            self._normalize_configured_hotkey(move_up_hotkey): "UP",
            self._normalize_configured_hotkey(move_down_hotkey): "DOWN",
            self._normalize_configured_hotkey(move_left_hotkey): "LEFT",
            self._normalize_configured_hotkey(move_right_hotkey): "RIGHT",
        }

        invalid = [key for key in hotkey_map if not key]
        if invalid:
            raise ValueError("All hunt movement hotkeys must be configured before recording.")

        with self._lock:
            self._hotkey_to_direction = hotkey_map
            self._waypoints = []
            self._relative_x = 0
            self._relative_y = 0
            self._total_steps = 0
            self._status = "recording"
            self._is_recording = True
            self._listener = keyboard.Listener(on_press=self._on_press)
            self._listener.start()

    def stop(self) -> list[HuntWaypoint]:
        listener = None
        with self._lock:
            if self._listener is not None:
                listener = self._listener
                self._listener = None
            self._is_recording = False
            self._status = "stopped"

            recorded = [
                HuntWaypoint(
                    direction=waypoint.direction,
                    repeats=waypoint.repeats,
                    relative_x=waypoint.relative_x,
                    relative_y=waypoint.relative_y,
                )
                for waypoint in self._waypoints
            ]

        if listener is not None:
            listener.stop()

        return recorded

    def snapshot(self) -> HuntRecordingSnapshot:
        with self._lock:
            return HuntRecordingSnapshot(
                is_recording=self._is_recording,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
                total_steps=self._total_steps,
                waypoints=tuple(
                    HuntWaypoint(
                        direction=waypoint.direction,
                        repeats=waypoint.repeats,
                        relative_x=waypoint.relative_x,
                        relative_y=waypoint.relative_y,
                    )
                    for waypoint in self._waypoints
                ),
                status=self._status,
            )

    def _on_press(self, key) -> None:
        normalized = self._normalize_pressed_key(key)
        if not normalized:
            return

        with self._lock:
            if not self._is_recording:
                return
            direction = self._hotkey_to_direction.get(normalized)
            if direction is None:
                return
            self._append_direction(direction)

    def _append_direction(self, direction: str) -> None:
        delta_x, delta_y = self._DELTAS[direction]
        self._relative_x += delta_x
        self._relative_y += delta_y
        self._total_steps += 1

        self._waypoints.append(
            HuntWaypoint(
                direction=direction,
                repeats=1,
                relative_x=self._relative_x,
                relative_y=self._relative_y,
            )
        )

    @staticmethod
    def _normalize_configured_hotkey(raw: str) -> str:
        return raw.strip().upper()

    def _normalize_pressed_key(self, key) -> str:
        if keyboard is None:
            return ""

        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.strip().upper()
            return ""

        if isinstance(key, keyboard.Key):
            name = getattr(key, "name", "") or str(key).split(".")[-1]
            return self._SPECIAL_KEYS.get(name.lower(), name.upper())

        return ""

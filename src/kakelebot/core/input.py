from __future__ import annotations

import inspect
import time
from dataclasses import dataclass
from typing import Protocol


class KeyInputAdapter(Protocol):
    def press(self, key: str, hold_seconds: float = 0.0) -> None:
        ...


@dataclass(frozen=True, slots=True)
class KeyAction:
    key: str
    reason: str
    hold_seconds: float = 0.0


class InputService:
    _HUNT_COORDINATE_PREFIX = "hunt-coordinate-"

    def __init__(self, adapter: KeyInputAdapter) -> None:
        self._adapter = adapter
        self._held_directional_key: str | None = None

    def execute(self, action: KeyAction) -> None:
        self.execute_many([action])

    def execute_many(self, actions: list[KeyAction], inter_key_delay_seconds: float = 0.0) -> None:
        directional_action = self._find_directional_hunt_action(actions)
        if directional_action is not None:
            self._sync_directional_hold(directional_action.key)
        else:
            self._release_directional_hold()

        non_directional_actions = [
            action for action in actions if not self._is_directional_hunt_action(action)
        ]
        if not non_directional_actions:
            return

        has_custom_hold = any(action.hold_seconds > 0 for action in non_directional_actions)
        press_many = getattr(self._adapter, "press_many", None)
        if callable(press_many) and not has_custom_hold:
            press_many([action.key for action in non_directional_actions], inter_key_delay_seconds)
            return

        for index, action in enumerate(non_directional_actions):
            self._press(action.key, action.hold_seconds)
            if inter_key_delay_seconds > 0 and index < len(non_directional_actions) - 1:
                time.sleep(inter_key_delay_seconds)

    def _press(self, key: str, hold_seconds: float) -> None:
        press = getattr(self._adapter, "press")
        try:
            signature = inspect.signature(press)
            if "hold_seconds" in signature.parameters:
                press(key, hold_seconds=hold_seconds)
                return
        except (TypeError, ValueError):
            pass
        press(key)

    def _sync_directional_hold(self, key: str) -> None:
        normalized = key.strip()
        if not normalized:
            self._release_directional_hold()
            return
        if self._held_directional_key == normalized:
            return
        if self._held_directional_key is not None:
            self._key_up(self._held_directional_key)
        self._key_down(normalized)
        self._held_directional_key = normalized

    def _release_directional_hold(self) -> None:
        if self._held_directional_key is None:
            return
        self._key_up(self._held_directional_key)
        self._held_directional_key = None

    def _key_down(self, key: str) -> None:
        key_down = getattr(self._adapter, "key_down", None)
        if callable(key_down):
            key_down(key)
            return
        self._press(key, 0.0)

    def _key_up(self, key: str) -> None:
        key_up = getattr(self._adapter, "key_up", None)
        if callable(key_up):
            key_up(key)

    @classmethod
    def _is_directional_hunt_action(cls, action: KeyAction) -> bool:
        return action.reason.startswith(cls._HUNT_COORDINATE_PREFIX)

    @classmethod
    def _find_directional_hunt_action(cls, actions: list[KeyAction]) -> KeyAction | None:
        for action in actions:
            if cls._is_directional_hunt_action(action):
                return action
        return None

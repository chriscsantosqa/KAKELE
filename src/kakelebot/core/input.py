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
    def __init__(self, adapter: KeyInputAdapter) -> None:
        self._adapter = adapter

    def execute(self, action: KeyAction) -> None:
        self._press(action.key, action.hold_seconds)

    def execute_many(self, actions: list[KeyAction], inter_key_delay_seconds: float = 0.0) -> None:
        if not actions:
            return

        has_custom_hold = any(action.hold_seconds > 0 for action in actions)
        press_many = getattr(self._adapter, "press_many", None)
        if callable(press_many) and not has_custom_hold:
            press_many([action.key for action in actions], inter_key_delay_seconds)
            return

        for index, action in enumerate(actions):
            self._press(action.key, action.hold_seconds)
            if inter_key_delay_seconds > 0 and index < len(actions) - 1:
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

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol


class KeyInputAdapter(Protocol):
    def press(self, key: str) -> None:
        ...


@dataclass(frozen=True, slots=True)
class KeyAction:
    key: str
    reason: str


class InputService:
    def __init__(self, adapter: KeyInputAdapter) -> None:
        self._adapter = adapter

    def execute(self, action: KeyAction) -> None:
        self._adapter.press(action.key)

    def execute_many(self, actions: list[KeyAction], inter_key_delay_seconds: float = 0.0) -> None:
        if not actions:
            return
        press_many = getattr(self._adapter, "press_many", None)
        if callable(press_many):
            press_many([action.key for action in actions], inter_key_delay_seconds)
            return
        for index, action in enumerate(actions):
            self._adapter.press(action.key)
            if inter_key_delay_seconds > 0 and index < len(actions) - 1:
                time.sleep(inter_key_delay_seconds)

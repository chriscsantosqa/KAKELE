from __future__ import annotations

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

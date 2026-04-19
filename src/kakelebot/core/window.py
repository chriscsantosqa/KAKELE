from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


GAME_WINDOW_TITLE = "Kakele"


class WindowAdapter(Protocol):
    def find_window(self, title: str) -> "WindowInfo | None":
        ...

    def activate_window(self, window: "WindowInfo") -> None:
        ...


@dataclass(frozen=True, slots=True)
class WindowInfo:
    title: str
    left: int
    top: int
    width: int
    height: int
    is_active: bool
    hwnd: int | None = None
    process_name: str | None = None

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


class WindowDiscoveryError(RuntimeError):
    """Raised when the target game window cannot be located."""


class WindowService:
    def __init__(self, adapter: WindowAdapter, window_title: str = GAME_WINDOW_TITLE) -> None:
        self._adapter = adapter
        self._window_title = window_title

    def get_game_window(self) -> WindowInfo:
        window = self._adapter.find_window(self._window_title)
        if window is None:
            raise WindowDiscoveryError(
                f"Game window '{self._window_title}' was not found."
            )
        return window

    def activate_game_window(self, window: WindowInfo | None = None) -> WindowInfo:
        resolved_window = window or self.get_game_window()
        self._adapter.activate_window(resolved_window)
        return self.get_game_window()

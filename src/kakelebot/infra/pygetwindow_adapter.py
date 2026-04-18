from __future__ import annotations

from typing import Any

from kakelebot.core.window import WindowInfo

try:
    import pygetwindow as gw
except ImportError:  # pragma: no cover
    gw = None


class PyGetWindowAdapter:
    def find_window(self, title: str) -> WindowInfo | None:
        if gw is None:
            raise RuntimeError("pygetwindow is not installed.")

        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return None

        window: Any = windows[0]
        return WindowInfo(
            title=window.title,
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height,
            is_active=bool(window.isActive),
        )

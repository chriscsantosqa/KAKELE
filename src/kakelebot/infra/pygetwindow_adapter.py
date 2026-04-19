from __future__ import annotations

import ctypes
import time
from pathlib import Path
from typing import Any

from kakelebot.core.window import WindowInfo

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

try:
    import pygetwindow as gw
except ImportError:  # pragma: no cover
    gw = None


_GAME_EXECUTABLE_NAMES = {"kakele.exe", "kakele"}
_EXCLUDED_WINDOW_TITLES = {"kakelebot next"}


class PyGetWindowAdapter:
    def find_window(self, title: str) -> WindowInfo | None:
        if gw is None:
            raise RuntimeError("pygetwindow is not installed.")

        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return None

        ranked_windows: list[tuple[int, Any]] = []
        for window in windows:
            rank = self._rank_window(window, title)
            if rank is None:
                continue
            ranked_windows.append((rank, window))

        if not ranked_windows:
            return None

        ranked_windows.sort(key=lambda item: item[0])
        selected_window = ranked_windows[0][1]
        process_name = self._get_process_name(selected_window)
        hwnd = self._get_hwnd(selected_window)
        return WindowInfo(
            title=selected_window.title,
            left=selected_window.left,
            top=selected_window.top,
            width=selected_window.width,
            height=selected_window.height,
            is_active=bool(selected_window.isActive),
            hwnd=hwnd,
            process_name=process_name,
        )

    def activate_window(self, window: WindowInfo) -> None:
        hwnd = window.hwnd
        if hwnd is None:
            return

        user32 = ctypes.windll.user32
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)
        user32.ShowWindow(hwnd, 5)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.05)

    def _rank_window(self, window: Any, requested_title: str) -> int | None:
        window_title = str(getattr(window, "title", "") or "").strip()
        if not window_title:
            return None
        if window_title.lower() in _EXCLUDED_WINDOW_TITLES:
            return None

        executable_name = self._get_process_name(window)
        title_lower = window_title.lower()
        requested_lower = requested_title.lower()
        is_active = bool(getattr(window, "isActive", False))

        if executable_name in _GAME_EXECUTABLE_NAMES:
            return 0 if is_active else 1
        if title_lower == requested_lower:
            return 2 if is_active else 3
        if title_lower.startswith(requested_lower) and "bot" not in title_lower:
            return 4 if is_active else 5
        if requested_lower in title_lower and "bot" not in title_lower:
            return 6 if is_active else 7
        return None

    def _get_process_name(self, window: Any) -> str | None:
        if psutil is None:
            return None

        hwnd = self._get_hwnd(window)
        if hwnd is None:
            return None

        process_id = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value == 0:
            return None

        try:
            process = psutil.Process(process_id.value)
            executable = process.exe() or process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            return None

        return Path(executable).name.lower()

    @staticmethod
    def _get_hwnd(window: Any) -> int | None:
        hwnd = getattr(window, "_hWnd", None)
        if hwnd is None:
            return None
        try:
            return int(hwnd)
        except (TypeError, ValueError):
            return None

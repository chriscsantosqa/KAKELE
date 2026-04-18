from __future__ import annotations

from typing import Any

try:
    import pyautogui
except ImportError:  # pragma: no cover
    pyautogui = None


class PyAutoGuiCaptureAdapter:
    def capture_region(self, left: int, top: int, width: int, height: int) -> Any:
        if pyautogui is None:
            raise RuntimeError("pyautogui is not installed.")

        return pyautogui.screenshot(region=(left, top, width, height))

from __future__ import annotations

import time

try:
    import pydirectinput
except ImportError:  # pragma: no cover
    pydirectinput = None


class PyDirectInputAdapter:
    _KEY_ALIASES = {
        "ENTER": "enter",
        "ESC": "esc",
        "SPACE": "space",
        "PAGEUP": "pageup",
        "PAGEDOWN": "pagedown",
        "BACKSPACE": "backspace",
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
    }

    def press(self, key: str) -> None:
        if pydirectinput is None:
            raise RuntimeError("pydirectinput is not installed.")

        normalized_key = self._normalize_key(key)
        if not normalized_key:
            return
        self._prepare_runtime()
        if hasattr(pydirectinput, "keyDown") and hasattr(pydirectinput, "keyUp"):
            pydirectinput.keyDown(normalized_key)
            pydirectinput.keyUp(normalized_key)
            return
        pydirectinput.press(normalized_key)

    def press_many(self, keys: list[str], inter_key_delay_seconds: float = 0.0) -> None:
        if pydirectinput is None:
            raise RuntimeError("pydirectinput is not installed.")
        if not keys:
            return

        self._prepare_runtime()
        normalized_keys = [self._normalize_key(key) for key in keys]
        filtered_keys = [key for key in normalized_keys if key]
        for index, key in enumerate(filtered_keys):
            if hasattr(pydirectinput, "keyDown") and hasattr(pydirectinput, "keyUp"):
                pydirectinput.keyDown(key)
                pydirectinput.keyUp(key)
            else:
                pydirectinput.press(key)
            if inter_key_delay_seconds > 0 and index < len(filtered_keys) - 1:
                time.sleep(inter_key_delay_seconds)

    def _normalize_key(self, key: str) -> str:
        normalized = key.strip().upper()
        if not normalized:
            return ""
        if normalized in self._KEY_ALIASES:
            return self._KEY_ALIASES[normalized]
        if normalized.startswith("F") and normalized[1:].isdigit():
            return normalized.lower()
        if len(normalized) == 1:
            return normalized.lower()
        return normalized.lower()

    @staticmethod
    def _prepare_runtime() -> None:
        if hasattr(pydirectinput, "PAUSE"):
            pydirectinput.PAUSE = 0
        if hasattr(pydirectinput, "FAILSAFE"):
            pydirectinput.FAILSAFE = False

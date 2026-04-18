from __future__ import annotations

from collections.abc import Callable

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover
    keyboard = None


class GlobalHotkeyService:
    def __init__(self) -> None:
        self._listener = None

    def configure(
        self,
        start_stop_hotkey: str,
        pause_resume_hotkey: str,
        on_start_stop: Callable[[], None],
        on_pause_resume: Callable[[], None],
    ) -> None:
        if keyboard is None:
            raise RuntimeError("pynput is not installed.")

        bindings: dict[str, Callable[[], None]] = {}
        bindings[self._normalize_hotkey(start_stop_hotkey)] = on_start_stop
        bindings[self._normalize_hotkey(pause_resume_hotkey)] = on_pause_resume

        self.stop()
        self._listener = keyboard.GlobalHotKeys(bindings)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    @staticmethod
    def _normalize_hotkey(raw_hotkey: str) -> str:
        hotkey = raw_hotkey.strip().lower()
        if not hotkey:
            raise ValueError("Hotkey cannot be empty.")

        parts = [part.strip() for part in hotkey.split("+") if part.strip()]
        normalized_parts: list[str] = []
        modifier_map = {
            "ctrl": "<ctrl>",
            "control": "<ctrl>",
            "alt": "<alt>",
            "shift": "<shift>",
            "cmd": "<cmd>",
            "command": "<cmd>",
            "win": "<cmd>",
            "windows": "<cmd>",
        }

        for part in parts:
            if part in modifier_map:
                normalized_parts.append(modifier_map[part])
            elif part.startswith("f") and part[1:].isdigit():
                normalized_parts.append(f"<{part}>")
            else:
                normalized_parts.append(part)

        return "+".join(normalized_parts)

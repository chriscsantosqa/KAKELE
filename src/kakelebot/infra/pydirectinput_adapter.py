from __future__ import annotations

import time

try:
    import pydirectinput
except ImportError:  # pragma: no cover
    pydirectinput = None


class PyDirectInputAdapter:
    def press(self, key: str) -> None:
        if pydirectinput is None:
            raise RuntimeError("pydirectinput is not installed.")

        self._prepare_runtime()
        pydirectinput.press(key)

    def press_many(self, keys: list[str], inter_key_delay_seconds: float = 0.0) -> None:
        if pydirectinput is None:
            raise RuntimeError("pydirectinput is not installed.")
        if not keys:
            return

        self._prepare_runtime()
        for index, key in enumerate(keys):
            if hasattr(pydirectinput, "keyDown") and hasattr(pydirectinput, "keyUp"):
                pydirectinput.keyDown(key)
                pydirectinput.keyUp(key)
            else:
                pydirectinput.press(key)
            if inter_key_delay_seconds > 0 and index < len(keys) - 1:
                time.sleep(inter_key_delay_seconds)

    @staticmethod
    def _prepare_runtime() -> None:
        if hasattr(pydirectinput, "PAUSE"):
            pydirectinput.PAUSE = 0
        if hasattr(pydirectinput, "FAILSAFE"):
            pydirectinput.FAILSAFE = False

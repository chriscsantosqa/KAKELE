from __future__ import annotations

try:
    import pydirectinput
except ImportError:  # pragma: no cover
    pydirectinput = None


class PyDirectInputAdapter:
    def press(self, key: str) -> None:
        if pydirectinput is None:
            raise RuntimeError("pydirectinput is not installed.")

        if hasattr(pydirectinput, "PAUSE"):
            pydirectinput.PAUSE = 0
        if hasattr(pydirectinput, "FAILSAFE"):
            pydirectinput.FAILSAFE = False

        pydirectinput.press(key)

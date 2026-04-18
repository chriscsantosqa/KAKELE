from __future__ import annotations

try:
    import pydirectinput
except ImportError:  # pragma: no cover
    pydirectinput = None


class PyDirectInputAdapter:
    def press(self, key: str) -> None:
        if pydirectinput is None:
            raise RuntimeError("pydirectinput is not installed.")

        pydirectinput.press(key)

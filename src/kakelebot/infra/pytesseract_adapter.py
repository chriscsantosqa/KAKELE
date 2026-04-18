from __future__ import annotations

from typing import Any

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None


class PyTesseractAdapter:
    def __init__(self, executable_path: str | None = None) -> None:
        if pytesseract is None:
            raise RuntimeError("pytesseract is not installed.")

        if executable_path:
            pytesseract.pytesseract.tesseract_cmd = executable_path

        self._pytesseract = pytesseract

    def image_to_string(self, image: Any, config: str | None = None) -> str:
        return self._pytesseract.image_to_string(image, config=config or "")

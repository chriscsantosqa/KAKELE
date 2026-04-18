from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

import cv2
import numpy as np


class OcrAdapter(Protocol):
    def image_to_string(self, image: Any, config: str) -> str:
        ...


@dataclass(frozen=True, slots=True)
class NumericBarReading:
    current: int | None
    maximum: int | None
    raw_text: str
    normalized_text: str

    @property
    def is_valid(self) -> bool:
        return self.current is not None and self.maximum is not None


class OcrService:
    OCR_CONFIG = "--psm 7 -c tessedit_char_whitelist=0123456789/,."

    def __init__(self, adapter: OcrAdapter) -> None:
        self._adapter = adapter

    def read_numeric_bar(self, frame: Any) -> NumericBarReading:
        processed = self._preprocess_bar_frame(frame)
        raw_text = self._adapter.image_to_string(processed, self.OCR_CONFIG)
        normalized = self._normalize_text(raw_text)
        current, maximum = self._parse_numeric_bar(normalized)

        return NumericBarReading(
            current=current,
            maximum=maximum,
            raw_text=raw_text,
            normalized_text=normalized,
        )

    @staticmethod
    def _preprocess_bar_frame(frame: Any) -> np.ndarray:
        image = np.array(frame)

        if image.ndim == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        height, width = image.shape[:2]
        resized = cv2.resize(
            image,
            (max(1, width * 3), max(1, height * 3)),
            interpolation=cv2.INTER_CUBIC,
        )
        blurred = cv2.GaussianBlur(resized, (3, 3), 0)
        thresholded = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )[1]

        return thresholded

    @staticmethod
    def _normalize_text(text: str) -> str:
        compact = text.strip().replace("\n", "")
        compact = compact.replace(",", "/").replace(".", "/")
        compact = re.sub(r"[^0-9/]", "", compact)
        compact = re.sub(r"/{2,}", "/", compact)
        return compact

    @staticmethod
    def _parse_numeric_bar(text: str) -> tuple[int | None, int | None]:
        if not text:
            return None, None

        if "/" in text:
            parts = [part for part in text.split("/") if part.isdigit()]
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])

        digits_only = "".join(char for char in text if char.isdigit())
        if len(digits_only) >= 2 and len(digits_only) % 2 == 0:
            middle = len(digits_only) // 2
            return int(digits_only[:middle]), int(digits_only[middle:])

        if digits_only.isdigit():
            return int(digits_only), None

        return None, None

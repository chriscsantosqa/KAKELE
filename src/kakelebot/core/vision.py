from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from kakelebot.core.image_processing import ImagePreprocessor


class OcrAdapter(Protocol):
    def image_to_string(self, image, config: str | None = None) -> str:
        ...


@dataclass(frozen=True, slots=True)
class BarReading:
    current: int
    maximum: int
    source_text: str
    confidence_ok: bool

    @property
    def percentage(self) -> float:
        if self.maximum <= 0:
            return 0.0
        return (self.current / self.maximum) * 100


class VisionService:
    def __init__(self, ocr_adapter: OcrAdapter, preprocessor: ImagePreprocessor | None = None) -> None:
        self._ocr = ocr_adapter
        self._preprocessor = preprocessor or ImagePreprocessor()

    def read_bar_value(self, image) -> BarReading | None:
        prepared_image = self._preprocessor.preprocess_bar(image)
        raw_text = self._ocr.image_to_string(prepared_image, config="--psm 7")
        normalized = self._normalize(raw_text)
        numbers = self._extract_numbers(normalized)

        if len(numbers) < 2:
            return None

        current, maximum = numbers[0], numbers[1]
        if maximum <= 0 or current < 0:
            return None

        confidence_ok = current <= maximum
        if not confidence_ok:
            return None

        return BarReading(
            current=current,
            maximum=maximum,
            source_text=normalized,
            confidence_ok=confidence_ok,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return text.strip().replace("\n", " ").replace("|", "/")

    @staticmethod
    def _extract_numbers(text: str) -> list[int]:
        matches = re.findall(r"\d+", text)
        return [int(value) for value in matches]

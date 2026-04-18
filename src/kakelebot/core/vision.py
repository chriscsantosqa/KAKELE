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


@dataclass(frozen=True, slots=True)
class OcrPreview:
    original_image: object
    processed_image: object
    raw_text: str
    normalized_text: str
    reading: BarReading | None


class VisionService:
    def __init__(self, ocr_adapter: OcrAdapter, preprocessor: ImagePreprocessor | None = None) -> None:
        self._ocr = ocr_adapter
        self._preprocessor = preprocessor or ImagePreprocessor()

    def read_bar_value(self, image) -> BarReading | None:
        return self.build_preview(image).reading

    def build_preview(self, image) -> OcrPreview:
        prepared_image = self._preprocessor.preprocess_bar(image)
        raw_text = self._ocr.image_to_string(prepared_image, config="--psm 7")
        normalized = self._normalize(raw_text)
        reading = self._parse_reading(normalized)
        return OcrPreview(
            original_image=image,
            processed_image=prepared_image,
            raw_text=raw_text,
            normalized_text=normalized,
            reading=reading,
        )

    def _parse_reading(self, normalized_text: str) -> BarReading | None:
        numbers = self._extract_numbers(normalized_text)

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
            source_text=normalized_text,
            confidence_ok=confidence_ok,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return text.strip().replace("\n", " ").replace("|", "/")

    @staticmethod
    def _extract_numbers(text: str) -> list[int]:
        matches = re.findall(r"\d+", text)
        return [int(value) for value in matches]

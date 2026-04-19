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


@dataclass(frozen=True, slots=True)
class TargetPreview:
    original_image: object
    processed_image: object
    raw_text: str
    normalized_text: str
    has_target: bool
    reason: str
    activity_ratio: float
    contrast_score: float


class VisionService:
    _BAR_OCR_CONFIG = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/"

    def __init__(self, ocr_adapter: OcrAdapter, preprocessor: ImagePreprocessor | None = None) -> None:
        self._ocr = ocr_adapter
        self._preprocessor = preprocessor or ImagePreprocessor()

    def read_bar_value(self, image) -> BarReading | None:
        return self.build_preview(image).reading

    def build_preview(self, image) -> OcrPreview:
        prepared_image = self._preprocessor.preprocess_status_bar(image)
        raw_text = self._ocr.image_to_string(prepared_image, config=self._BAR_OCR_CONFIG)
        normalized = self._normalize_bar_text(raw_text)
        reading = self._parse_reading(normalized)
        return OcrPreview(
            original_image=image,
            processed_image=prepared_image,
            raw_text=raw_text,
            normalized_text=normalized,
            reading=reading,
        )

    def build_target_preview(self, image) -> TargetPreview:
        prepared_image = self._preprocessor.preprocess_bar(image)
        raw_text = self._ocr.image_to_string(prepared_image, config="--psm 7")
        normalized = self._normalize(raw_text)
        activity_ratio = self._bright_pixel_ratio(prepared_image)
        contrast_score = self._contrast_score(prepared_image)
        has_target, reason = self._detect_target_presence(normalized, activity_ratio, contrast_score)
        return TargetPreview(
            original_image=image,
            processed_image=prepared_image,
            raw_text=raw_text,
            normalized_text=normalized,
            has_target=has_target,
            reason=reason,
            activity_ratio=activity_ratio,
            contrast_score=contrast_score,
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
    def _normalize_bar_text(text: str) -> str:
        normalized = (
            text.strip()
            .replace("\n", " ")
            .replace("|", "/")
            .replace("\\", "/")
            .replace(":", "/")
            .replace(";", "/")
        )
        return re.sub(r"[^0-9/ ]+", "", normalized)

    @staticmethod
    def _extract_numbers(text: str) -> list[int]:
        matches = re.findall(r"\d+", text)
        return [int(value) for value in matches]

    @staticmethod
    def _detect_target_presence(
        normalized_text: str,
        activity_ratio: float,
        contrast_score: float,
    ) -> tuple[bool, str]:
        if normalized_text:
            return True, "ocr-text-detected"
        if activity_ratio >= 0.10 and contrast_score >= 20.0:
            return True, "visual-activity-detected"
        return False, "no-target-signal"

    @staticmethod
    def _bright_pixel_ratio(image) -> float:
        histogram = image.histogram()
        total_pixels = max(1, sum(histogram))
        bright_pixels = sum(histogram[200:256])
        return bright_pixels / total_pixels

    @staticmethod
    def _contrast_score(image) -> float:
        try:
            from PIL import ImageStat
        except ImportError:
            return 0.0
        stat = ImageStat.Stat(image)
        return float(stat.stddev[0]) if stat.stddev else 0.0

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from kakelebot.core.config import NormalizedRegionSettings


@dataclass(frozen=True, slots=True)
class VisionElementAssessment:
    detected: bool
    confidence: str
    rationale: str


@dataclass(frozen=True, slots=True)
class AIVisionRequest:
    profile_name: str
    resolution_width: int
    resolution_height: int
    ui_scale: float
    window_title: str
    window_width: int
    window_height: int
    resolution_validation_message: str
    whole_window_image: object
    life_image: object | None
    mana_image: object | None
    target_image: object | None
    life_ocr_text: str | None
    mana_ocr_text: str | None
    target_ocr_text: str | None


@dataclass(frozen=True, slots=True)
class AIVisionAnalysisResult:
    summary: str
    screen_state: str
    can_start_session: bool
    issues: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    suggested_rois: dict[str, NormalizedRegionSettings] = field(default_factory=dict)
    detected_elements: dict[str, VisionElementAssessment] = field(default_factory=dict)
    raw_response: str | None = None
    error_message: str | None = None

    @property
    def has_roi_suggestions(self) -> bool:
        return bool(self.suggested_rois)


class VisionAssistant(Protocol):
    def analyze(self, request: AIVisionRequest) -> AIVisionAnalysisResult:
        ...


def build_error_analysis(message: str) -> AIVisionAnalysisResult:
    return AIVisionAnalysisResult(
        summary="AI visual analysis unavailable",
        screen_state="unknown",
        can_start_session=False,
        issues=[message],
        recommended_actions=["Review AI vision settings before using this feature."],
        error_message=message,
    )

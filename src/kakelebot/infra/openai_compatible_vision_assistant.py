from __future__ import annotations

import base64
import io
import json
import os
import urllib.error
import urllib.request

from kakelebot.core.ai_vision import (
    AIVisionAnalysisResult,
    AIVisionRequest,
    VisionAssistant,
    VisionElementAssessment,
    build_error_analysis,
)
from kakelebot.core.config import AiVisionSettings, NormalizedRegionSettings


class OpenAICompatibleVisionAssistant(VisionAssistant):
    def __init__(self, settings: AiVisionSettings) -> None:
        self._settings = settings

    def analyze(self, request: AIVisionRequest) -> AIVisionAnalysisResult:
        api_key = os.getenv(self._settings.api_key_env_var.strip())
        if not api_key:
            return build_error_analysis(
                f"Environment variable '{self._settings.api_key_env_var}' is not set."
            )
        if not self._settings.model.strip():
            return build_error_analysis("AI vision model is empty in settings.json.")

        endpoint = self._build_endpoint_url()
        payload = self._build_payload(request)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        raw_response = None

        try:
            http_request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(http_request, timeout=self._settings.timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            return build_error_analysis(f"AI HTTP error {error.code}: {detail}")
        except urllib.error.URLError as error:
            return build_error_analysis(f"AI connection error: {error.reason}")
        except TimeoutError:
            return build_error_analysis("AI request timed out.")

        try:
            response_json = json.loads(raw_response)
            content = self._extract_response_content(response_json)
            structured = self._extract_json_payload(content)
            return self._build_result(structured, raw_response)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            return build_error_analysis(f"AI response parsing failed: {error}")

    def _build_endpoint_url(self) -> str:
        return self._settings.base_url.rstrip("/") + "/" + self._settings.endpoint_path.strip("/")

    def _build_payload(self, request: AIVisionRequest) -> dict:
        return {
            "model": self._settings.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": self._system_prompt(),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": self._user_content(request),
                },
            ],
        }

    def _user_content(self, request: AIVisionRequest) -> list[dict]:
        content: list[dict] = [
            {
                "type": "text",
                "text": self._request_context_text(request),
            },
            {
                "type": "image_url",
                "image_url": {"url": self._image_to_data_url(request.whole_window_image)},
            },
        ]

        optional_images = [
            ("life_roi", request.life_image),
            ("mana_roi", request.mana_image),
            ("target_roi", request.target_image),
        ]
        for name, image in optional_images:
            if image is None:
                continue
            content.append({"type": "text", "text": f"Image purpose: {name}"})
            content.append({"type": "image_url", "image_url": {"url": self._image_to_data_url(image)}})
        return content

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a visual calibration assistant for a desktop game automation tool. "
            "Return only valid JSON. Do not wrap in markdown. "
            "Evaluate whether the health bar, mana bar and target area appear to be correctly selected. "
            "Provide conservative suggestions only. Never claim certainty when uncertain. "
            "JSON schema: {"
            "summary": string,"
            "screen_state": string,"
            "can_start_session": boolean,"
            "issues": string[],"
            "recommended_actions": string[],"
            "detected_elements": {"
            "life_bar": {"detected": boolean, "confidence": string, "rationale": string},"
            "mana_bar": {"detected": boolean, "confidence": string, "rationale": string},"
            "target_area": {"detected": boolean, "confidence": string, "rationale": string}"
            "},"
            "suggested_rois": {"
            "life": {"left_ratio": number, "top_ratio": number, "width_ratio": number, "height_ratio": number},"
            "mana": {"left_ratio": number, "top_ratio": number, "width_ratio": number, "height_ratio": number},"
            "target": {"left_ratio": number, "top_ratio": number, "width_ratio": number, "height_ratio": number}"
            "}"
            "}"
        )

    @staticmethod
    def _request_context_text(request: AIVisionRequest) -> str:
        return (
            f"Profile: {request.profile_name}\n"
            f"Profile resolution: {request.resolution_width}x{request.resolution_height}\n"
            f"Window: {request.window_title} ({request.window_width}x{request.window_height})\n"
            f"UI scale: {request.ui_scale}\n"
            f"Resolution validation: {request.resolution_validation_message}\n"
            f"Life OCR: {request.life_ocr_text or 'empty'}\n"
            f"Mana OCR: {request.mana_ocr_text or 'empty'}\n"
            f"Target OCR: {request.target_ocr_text or 'empty'}\n"
            "The first image is the whole game window. The following images are ROI crops."
        )

    @staticmethod
    def _image_to_data_url(image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def _extract_response_content(response_json: dict) -> str:
        choices = response_json.get("choices")
        if not choices:
            raise ValueError("No choices returned by AI provider.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "\n".join(part for part in text_parts if part)
        raise ValueError("Unsupported AI response content format.")

    @staticmethod
    def _extract_json_payload(content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        return json.loads(cleaned)

    def _build_result(self, payload: dict, raw_response: str) -> AIVisionAnalysisResult:
        detected_elements = {}
        for key, value in (payload.get("detected_elements") or {}).items():
            if not isinstance(value, dict):
                continue
            detected_elements[key] = VisionElementAssessment(
                detected=bool(value.get("detected")),
                confidence=str(value.get("confidence", "unknown")),
                rationale=str(value.get("rationale", "")),
            )

        suggested_rois = {}
        for key, value in (payload.get("suggested_rois") or {}).items():
            normalized = self._build_region(value)
            if normalized is not None:
                suggested_rois[key] = normalized

        return AIVisionAnalysisResult(
            summary=str(payload.get("summary", "AI visual analysis completed.")),
            screen_state=str(payload.get("screen_state", "unknown")),
            can_start_session=bool(payload.get("can_start_session", False)),
            issues=[str(item) for item in payload.get("issues", [])],
            recommended_actions=[str(item) for item in payload.get("recommended_actions", [])],
            suggested_rois=suggested_rois,
            detected_elements=detected_elements,
            raw_response=raw_response,
            error_message=None,
        )

    @staticmethod
    def _build_region(value: object) -> NormalizedRegionSettings | None:
        if not isinstance(value, dict):
            return None
        try:
            region = NormalizedRegionSettings(
                left_ratio=float(value["left_ratio"]),
                top_ratio=float(value["top_ratio"]),
                width_ratio=float(value["width_ratio"]),
                height_ratio=float(value["height_ratio"]),
            )
        except (KeyError, TypeError, ValueError):
            return None
        if not OpenAICompatibleVisionAssistant._valid_ratio(region.left_ratio):
            return None
        if not OpenAICompatibleVisionAssistant._valid_ratio(region.top_ratio):
            return None
        if not OpenAICompatibleVisionAssistant._valid_ratio(region.width_ratio, allow_zero=False):
            return None
        if not OpenAICompatibleVisionAssistant._valid_ratio(region.height_ratio, allow_zero=False):
            return None
        return region

    @staticmethod
    def _valid_ratio(value: float, allow_zero: bool = True) -> bool:
        minimum = 0.0 if allow_zero else 0.0001
        return minimum <= value <= 1.0

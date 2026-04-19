from __future__ import annotations

import json

from kakelebot.core.calibration import CalibrationService
from kakelebot.core.capture import CaptureService
from kakelebot.core.input import InputService
from kakelebot.core.runtime import RuntimeBootstrap
from kakelebot.core.session import SessionController
from kakelebot.core.vision import VisionService
from kakelebot.core.window import WindowService
from kakelebot.features.healing import HealingService
from kakelebot.features.healing_loop import HealingLoopRunner
from kakelebot.features.healing_runtime import HealingRuntime
from kakelebot.gui import _build_ai_vision_assistant
from kakelebot.infra.pyautogui_capture_adapter import PyAutoGuiCaptureAdapter
from kakelebot.infra.pydirectinput_adapter import PyDirectInputAdapter
from kakelebot.infra.pygetwindow_adapter import PyGetWindowAdapter
from kakelebot.infra.pytesseract_adapter import PyTesseractAdapter


def run() -> int:
    runtime = RuntimeBootstrap().initialize()

    window_service = WindowService(adapter=PyGetWindowAdapter())
    capture_service = CaptureService(adapter=PyAutoGuiCaptureAdapter())
    calibration_service = CalibrationService()
    healing_service = HealingService()
    vision_service = VisionService(PyTesseractAdapter())
    input_service = InputService(PyDirectInputAdapter())
    ai_vision_assistant = _build_ai_vision_assistant(runtime.settings)

    healing_runtime = HealingRuntime(
        capture_service=capture_service,
        vision_service=vision_service,
        healing_service=healing_service,
        input_service=input_service,
    )
    healing_loop = HealingLoopRunner(
        window_service=window_service,
        calibration_service=calibration_service,
        healing_runtime=healing_runtime,
    )
    session_controller = SessionController(
        window_service=window_service,
        capture_service=capture_service,
        calibration_service=calibration_service,
        healing_loop=healing_loop,
        vision_service=vision_service,
        ai_vision_assistant=ai_vision_assistant,
    )

    result = session_controller.analyze_visual_state(runtime.profile)
    payload = {
        "summary": result.summary,
        "screen_state": result.screen_state,
        "can_start_session": result.can_start_session,
        "issues": result.issues,
        "recommended_actions": result.recommended_actions,
        "detected_elements": {
            key: {
                "detected": value.detected,
                "confidence": value.confidence,
                "rationale": value.rationale,
            }
            for key, value in result.detected_elements.items()
        },
        "suggested_rois": {
            key: {
                "left_ratio": value.left_ratio,
                "top_ratio": value.top_ratio,
                "width_ratio": value.width_ratio,
                "height_ratio": value.height_ratio,
            }
            for key, value in result.suggested_rois.items()
        },
        "error_message": result.error_message,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if result.error_message is None else 1


if __name__ == "__main__":
    raise SystemExit(run())

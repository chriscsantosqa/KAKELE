from __future__ import annotations

from kakelebot.core.calibration import CalibrationService
from kakelebot.core.capture import CaptureService
from kakelebot.core.config import AppSettings
from kakelebot.core.input import InputService
from kakelebot.core.profile_manager import ProfileManager
from kakelebot.core.runtime import RuntimeBootstrap
from kakelebot.core.session import SessionController
from kakelebot.core.vision import VisionService
from kakelebot.core.window import WindowService
from kakelebot.features.healing import HealingService
from kakelebot.features.healing_loop import HealingLoopRunner
from kakelebot.features.healing_runtime import HealingRuntime
from kakelebot.infra.openai_compatible_vision_assistant import OpenAICompatibleVisionAssistant
from kakelebot.infra.pyautogui_capture_adapter import PyAutoGuiCaptureAdapter
from kakelebot.infra.pydirectinput_adapter import PyDirectInputAdapter
from kakelebot.infra.pygetwindow_adapter import PyGetWindowAdapter
from kakelebot.infra.pytesseract_adapter import PyTesseractAdapter
from kakelebot.ui.modern_main_window import ModernMainWindow


def _build_ai_vision_assistant(settings: AppSettings):
    if not settings.ai_vision.enabled:
        return None
    if settings.ai_vision.provider != "openai_compatible":
        return None
    return OpenAICompatibleVisionAssistant(settings.ai_vision)


def run_gui() -> int:
    runtime = RuntimeBootstrap().initialize()

    window_service = WindowService(adapter=PyGetWindowAdapter())
    capture_service = CaptureService(adapter=PyAutoGuiCaptureAdapter())
    calibration_service = CalibrationService()
    healing_service = HealingService()
    vision_service = VisionService(PyTesseractAdapter())
    input_service = InputService(PyDirectInputAdapter())
    profile_manager = ProfileManager(
        profiles_dir=runtime.paths.profiles,
        settings=runtime.settings,
        settings_path=runtime.paths.root / "settings.json",
    )
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

    profile_path = runtime.paths.profiles / f"{runtime.profile.name}.json"
    window = ModernMainWindow(
        session_controller=session_controller,
        profile=runtime.profile,
        profile_path=profile_path,
        profile_manager=profile_manager,
    )
    window.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_gui())

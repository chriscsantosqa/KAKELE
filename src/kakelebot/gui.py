from __future__ import annotations

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
from kakelebot.infra.pyautogui_capture_adapter import PyAutoGuiCaptureAdapter
from kakelebot.infra.pydirectinput_adapter import PyDirectInputAdapter
from kakelebot.infra.pygetwindow_adapter import PyGetWindowAdapter
from kakelebot.infra.pytesseract_adapter import PyTesseractAdapter
from kakelebot.ui.main_window import MainWindow


def run_gui() -> int:
    runtime = RuntimeBootstrap().initialize()

    window_service = WindowService(adapter=PyGetWindowAdapter())
    capture_service = CaptureService(adapter=PyAutoGuiCaptureAdapter())
    calibration_service = CalibrationService()
    healing_service = HealingService()
    vision_service = VisionService(PyTesseractAdapter())
    input_service = InputService(PyDirectInputAdapter())

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
    )

    settings_path = runtime.paths.root / "settings.json"
    profile_path = runtime.paths.profiles / f"{runtime.profile.name}.json"
    window = MainWindow(
        session_controller=session_controller,
        profile=runtime.profile,
        profile_path=profile_path,
        settings=runtime.settings,
        settings_path=settings_path,
        profiles_dir=runtime.paths.profiles,
    )
    window.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_gui())

from __future__ import annotations

import logging

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


logger = logging.getLogger(__name__)


def run() -> int:
    runtime = RuntimeBootstrap().initialize()

    logger.info("KakeleBot next bootstrap initialized")
    logger.info("Active profile: %s", runtime.profile.name)
    logger.info("Log file: %s", runtime.log_file)
    logger.info("Profiles directory: %s", runtime.paths.profiles)

    print("KakeleBot next bootstrap initialized successfully.")
    print(f"Active profile: {runtime.profile.name}")
    print(f"Log file: {runtime.log_file}")

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
    )

    profile_path = runtime.paths.profiles / f"{runtime.profile.name}.json"
    session_result = session_controller.start_healing_bootstrap_session(
        profile=runtime.profile,
        profile_path=profile_path,
    )

    logger.info("Session status: %s", session_result.status)
    logger.info("Session result: %s", session_result)

    print(f"Session status: {session_result.status.state} - {session_result.status.message}")

    if session_result.error_message:
        print(f"Session error: {session_result.error_message}")
        return 1

    if session_result.window is not None:
        print(
            f"Game window found: {session_result.window.title} "
            f"({session_result.window.width}x{session_result.window.height})"
        )

    if session_result.whole_window_region is not None:
        print(
            "Whole window region: "
            f"{session_result.whole_window_region.width}x{session_result.whole_window_region.height}"
        )

    if session_result.calibration_snapshot is not None:
        snapshot = session_result.calibration_snapshot
        print(
            "Calibration regions prepared: "
            f"life={snapshot.life_bar.width}x{snapshot.life_bar.height}, "
            f"mana={snapshot.mana_bar.width}x{snapshot.mana_bar.height}, "
            f"target={snapshot.target_status.width}x{snapshot.target_status.height}, "
            f"minimap={snapshot.minimap.width}x{snapshot.minimap.height}"
        )

    if session_result.healing_loop_result is not None:
        print(
            f"Healing loop cycles completed: "
            f"{session_result.healing_loop_result.cycles_completed}"
        )
        print(
            f"Healing loop last cycle: "
            f"{session_result.healing_loop_result.last_cycle}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

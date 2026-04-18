from __future__ import annotations

import logging

from kakelebot.core.calibration import CalibrationService
from kakelebot.core.capture import CaptureService
from kakelebot.core.input import InputService
from kakelebot.core.runtime import RuntimeBootstrap
from kakelebot.core.vision import VisionService
from kakelebot.core.window import WindowDiscoveryError, WindowService
from kakelebot.features.healing import HealingService
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

    try:
        game_window = window_service.get_game_window()
        whole_window = capture_service.whole_window_region(game_window)
        frame = capture_service.capture(whole_window)

        calibration_service.update_profile_resolution(runtime.profile, game_window)
        profile_path = runtime.paths.profiles / f"{runtime.profile.name}.json"
        calibration_service.save_profile(profile_path, runtime.profile)
        snapshot = calibration_service.build_snapshot(game_window, runtime.profile)

        logger.info(
            "Game window found: title=%s left=%s top=%s width=%s height=%s active=%s",
            game_window.title,
            game_window.left,
            game_window.top,
            game_window.width,
            game_window.height,
            game_window.is_active,
        )
        logger.info(
            "Initial capture completed: region=%s frame_width=%s frame_height=%s",
            whole_window.name,
            getattr(frame, "width", "unknown"),
            getattr(frame, "height", "unknown"),
        )
        logger.info(
            "Calibration snapshot: life=%s mana=%s target=%s minimap=%s",
            snapshot.life_bar,
            snapshot.mana_bar,
            snapshot.target_status,
            snapshot.minimap,
        )

        print(
            f"Game window found: {game_window.title} "
            f"({game_window.width}x{game_window.height})"
        )
        print(
            f"Initial capture completed: "
            f"{getattr(frame, 'width', 'unknown')}x{getattr(frame, 'height', 'unknown')}"
        )
        print(
            "Calibration regions prepared: "
            f"life={snapshot.life_bar.width}x{snapshot.life_bar.height}, "
            f"mana={snapshot.mana_bar.width}x{snapshot.mana_bar.height}, "
            f"target={snapshot.target_status.width}x{snapshot.target_status.height}, "
            f"minimap={snapshot.minimap.width}x{snapshot.minimap.height}"
        )

        try:
            vision_service = VisionService(PyTesseractAdapter())
            input_service = InputService(PyDirectInputAdapter())
            healing_runtime = HealingRuntime(
                capture_service=capture_service,
                vision_service=vision_service,
                healing_service=healing_service,
                input_service=input_service,
            )

            cycle_result = healing_runtime.execute_cycle(
                snapshot=snapshot,
                life_hotkey=runtime.profile.hotkeys.heal_life,
                mana_hotkey=runtime.profile.hotkeys.heal_mana,
                life_threshold_percent=runtime.profile.thresholds.life_percent,
                mana_threshold_percent=runtime.profile.thresholds.mana_percent,
                window_is_active=game_window.is_active,
            )

            logger.info("Life OCR reading: %s", cycle_result.life_reading)
            logger.info("Mana OCR reading: %s", cycle_result.mana_reading)
            logger.info("Healing decision: %s", cycle_result.decision)
            logger.info("Healing actions executed: %s", cycle_result.actions_executed)

            print(f"Life OCR reading: {cycle_result.life_reading}")
            print(f"Mana OCR reading: {cycle_result.mana_reading}")
            print(f"Healing decision: {cycle_result.decision.reason}")
            print(f"Healing actions executed: {cycle_result.actions_executed}")
        except RuntimeError as error:
            logger.warning("Healing bootstrap unavailable: %s", error)
            print(f"Healing bootstrap unavailable: {error}")
    except WindowDiscoveryError as error:
        logger.warning("%s", error)
        print(str(error))

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

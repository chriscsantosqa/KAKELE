from __future__ import annotations

import logging

from kakelebot.core.capture import CaptureService
from kakelebot.core.runtime import RuntimeBootstrap
from kakelebot.core.window import WindowDiscoveryError, WindowService
from kakelebot.infra.pyautogui_capture_adapter import PyAutoGuiCaptureAdapter
from kakelebot.infra.pygetwindow_adapter import PyGetWindowAdapter


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

    try:
        game_window = window_service.get_game_window()
        whole_window = capture_service.whole_window_region(game_window)
        frame = capture_service.capture(whole_window)

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

        print(
            f"Game window found: {game_window.title} "
            f"({game_window.width}x{game_window.height})"
        )
        print(
            f"Initial capture completed: "
            f"{getattr(frame, 'width', 'unknown')}x{getattr(frame, 'height', 'unknown')}"
        )
    except WindowDiscoveryError as error:
        logger.warning("%s", error)
        print(str(error))

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

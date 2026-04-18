from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from kakelebot.core.calibration import CalibrationService, CalibrationSnapshot
from kakelebot.core.capture import CaptureService, ScreenRegion
from kakelebot.core.config import ProfileSettings
from kakelebot.core.window import WindowDiscoveryError, WindowInfo, WindowService
from kakelebot.features.healing_loop import HealingLoopResult, HealingLoopRunner


class SessionState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SessionStatus:
    state: SessionState
    message: str


@dataclass(frozen=True, slots=True)
class SessionRunResult:
    status: SessionStatus
    window: WindowInfo | None
    whole_window_region: ScreenRegion | None
    calibration_snapshot: CalibrationSnapshot | None
    healing_loop_result: HealingLoopResult | None
    error_message: str | None


class SessionController:
    def __init__(
        self,
        window_service: WindowService,
        capture_service: CaptureService,
        calibration_service: CalibrationService,
        healing_loop: HealingLoopRunner,
    ) -> None:
        self._window_service = window_service
        self._capture_service = capture_service
        self._calibration_service = calibration_service
        self._healing_loop = healing_loop
        self._status = SessionStatus(SessionState.IDLE, "session initialized")

    @property
    def status(self) -> SessionStatus:
        return self._status

    def pause(self) -> None:
        self._status = SessionStatus(SessionState.PAUSED, "session paused")

    def resume(self) -> None:
        self._status = SessionStatus(SessionState.RUNNING, "session resumed")

    def stop(self) -> None:
        self._status = SessionStatus(SessionState.STOPPED, "session stopped")

    def start_healing_bootstrap_session(
        self,
        profile: ProfileSettings,
        profile_path,
    ) -> SessionRunResult:
        self._status = SessionStatus(SessionState.RUNNING, "healing bootstrap session started")

        try:
            window = self._window_service.get_game_window()
            whole_window_region = self._capture_service.whole_window_region(window)
            self._capture_service.capture(whole_window_region)

            self._calibration_service.update_profile_resolution(profile, window)
            self._calibration_service.save_profile(profile_path, profile)
            calibration_snapshot = self._calibration_service.build_snapshot(window, profile)

            healing_loop_result = self._healing_loop.run(profile)
            self._status = SessionStatus(SessionState.COMPLETED, "healing bootstrap session completed")

            return SessionRunResult(
                status=self._status,
                window=window,
                whole_window_region=whole_window_region,
                calibration_snapshot=calibration_snapshot,
                healing_loop_result=healing_loop_result,
                error_message=None,
            )
        except (WindowDiscoveryError, RuntimeError) as error:
            self._status = SessionStatus(SessionState.FAILED, str(error))
            return SessionRunResult(
                status=self._status,
                window=None,
                whole_window_region=None,
                calibration_snapshot=None,
                healing_loop_result=None,
                error_message=str(error),
            )

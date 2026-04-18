from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock

from kakelebot.core.calibration import CalibrationService, CalibrationSnapshot
from kakelebot.core.capture import CaptureService, ScreenRegion
from kakelebot.core.config import ProfileSettings
from kakelebot.core.vision import OcrPreview, VisionService
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


@dataclass(frozen=True, slots=True)
class SessionPreviewResult:
    status: SessionStatus
    window: WindowInfo | None
    calibration_snapshot: CalibrationSnapshot | None
    life_preview: OcrPreview | None
    mana_preview: OcrPreview | None
    error_message: str | None


class SessionController:
    def __init__(
        self,
        window_service: WindowService,
        capture_service: CaptureService,
        calibration_service: CalibrationService,
        healing_loop: HealingLoopRunner,
        vision_service: VisionService,
    ) -> None:
        self._window_service = window_service
        self._capture_service = capture_service
        self._calibration_service = calibration_service
        self._healing_loop = healing_loop
        self._vision_service = vision_service
        self._status = SessionStatus(SessionState.IDLE, "session initialized")
        self._last_result: SessionRunResult | None = None
        self._lock = RLock()

    @property
    def status(self) -> SessionStatus:
        with self._lock:
            return self._status

    @property
    def last_result(self) -> SessionRunResult | None:
        with self._lock:
            return self._last_result

    def pause(self) -> None:
        with self._lock:
            if self._status.state == SessionState.RUNNING:
                self._status = SessionStatus(SessionState.PAUSED, "session paused")

    def resume(self) -> None:
        with self._lock:
            if self._status.state == SessionState.PAUSED:
                self._status = SessionStatus(SessionState.RUNNING, "session resumed")

    def stop(self) -> None:
        with self._lock:
            self._status = SessionStatus(SessionState.STOPPED, "session stopped")

    def start_healing_bootstrap_session(
        self,
        profile: ProfileSettings,
        profile_path,
    ) -> SessionRunResult:
        with self._lock:
            self._status = SessionStatus(SessionState.RUNNING, "healing bootstrap session started")
            self._last_result = None

        try:
            window = self._window_service.get_game_window()
            whole_window_region = self._capture_service.whole_window_region(window)
            self._capture_service.capture(whole_window_region)

            self._calibration_service.update_profile_resolution(profile, window)
            self._calibration_service.save_profile(profile_path, profile)
            calibration_snapshot = self._calibration_service.build_snapshot(window, profile)

            healing_loop_result = self._healing_loop.run(
                profile,
                should_continue=self._should_continue,
                is_paused=self._is_paused,
            )

            with self._lock:
                if self._status.state == SessionState.STOPPED:
                    final_status = self._status
                elif healing_loop_result.fail_safe_triggered:
                    final_status = SessionStatus(
                        SessionState.FAILED,
                        f"fail-safe triggered: {healing_loop_result.termination_reason}",
                    )
                    self._status = final_status
                else:
                    final_status = SessionStatus(SessionState.COMPLETED, "healing bootstrap session completed")
                    self._status = final_status

            result = SessionRunResult(
                status=final_status,
                window=window,
                whole_window_region=whole_window_region,
                calibration_snapshot=calibration_snapshot,
                healing_loop_result=healing_loop_result,
                error_message=None,
            )
            with self._lock:
                self._last_result = result
            return result
        except (WindowDiscoveryError, RuntimeError) as error:
            with self._lock:
                self._status = SessionStatus(SessionState.FAILED, str(error))
                result = SessionRunResult(
                    status=self._status,
                    window=None,
                    whole_window_region=None,
                    calibration_snapshot=None,
                    healing_loop_result=None,
                    error_message=str(error),
                )
                self._last_result = result
                return result

    def capture_preview(self, profile: ProfileSettings) -> SessionPreviewResult:
        try:
            window = self._window_service.get_game_window()
            calibration_snapshot = self._calibration_service.build_snapshot(window, profile)
            life_image = self._capture_service.capture(calibration_snapshot.life_bar)
            mana_image = self._capture_service.capture(calibration_snapshot.mana_bar)
            life_preview = self._vision_service.build_preview(life_image)
            mana_preview = self._vision_service.build_preview(mana_image)

            return SessionPreviewResult(
                status=SessionStatus(SessionState.IDLE, "preview captured"),
                window=window,
                calibration_snapshot=calibration_snapshot,
                life_preview=life_preview,
                mana_preview=mana_preview,
                error_message=None,
            )
        except (WindowDiscoveryError, RuntimeError) as error:
            return SessionPreviewResult(
                status=SessionStatus(SessionState.FAILED, str(error)),
                window=None,
                calibration_snapshot=None,
                life_preview=None,
                mana_preview=None,
                error_message=str(error),
            )

    def _should_continue(self) -> bool:
        with self._lock:
            return self._status.state != SessionState.STOPPED

    def _is_paused(self) -> bool:
        with self._lock:
            return self._status.state == SessionState.PAUSED

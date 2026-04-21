from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock

from kakelebot.core.ai_vision import AIVisionAnalysisResult, AIVisionRequest, VisionAssistant, build_error_analysis
from kakelebot.core.calibration import (
    CalibrationService,
    CalibrationSnapshot,
    WindowResolutionValidation,
)
from kakelebot.core.capture import CaptureService, ScreenRegion
from kakelebot.core.config import ProfileSettings
from kakelebot.core.vision import OcrPreview, TargetPreview, VisionService
from kakelebot.core.window import WindowDiscoveryError, WindowInfo, WindowService
from kakelebot.features.healing_loop import HealingLoopResult, HealingLoopRunner
from kakelebot.features.healing_runtime import HealingCycleResult


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
    resolution_validation: WindowResolutionValidation | None
    healing_loop_result: HealingLoopResult | None
    error_message: str | None


@dataclass(frozen=True, slots=True)
class SessionPreviewResult:
    status: SessionStatus
    window: WindowInfo | None
    calibration_snapshot: CalibrationSnapshot | None
    resolution_validation: WindowResolutionValidation | None
    life_preview: OcrPreview | None
    mana_preview: OcrPreview | None
    target_preview: TargetPreview | None
    error_message: str | None


class SessionController:
    def __init__(
        self,
        window_service: WindowService,
        capture_service: CaptureService,
        calibration_service: CalibrationService,
        healing_loop: HealingLoopRunner,
        vision_service: VisionService,
        ai_vision_assistant: VisionAssistant | None = None,
    ) -> None:
        self._window_service = window_service
        self._capture_service = capture_service
        self._calibration_service = calibration_service
        self._healing_loop = healing_loop
        self._vision_service = vision_service
        self._ai_vision_assistant = ai_vision_assistant
        self._status = SessionStatus(SessionState.IDLE, "session initialized")
        self._last_result: SessionRunResult | None = None
        self._lock = RLock()
        self._cavebot_active = False
        self._live_cycle_result: HealingCycleResult | None = None
        self._live_cycles_completed = 0

    @property
    def status(self) -> SessionStatus:
        with self._lock:
            return self._status

    @property
    def last_result(self) -> SessionRunResult | None:
        with self._lock:
            return self._last_result

    @property
    def cavebot_active(self) -> bool:
        with self._lock:
            return self._cavebot_active

    @property
    def live_cycle_result(self) -> HealingCycleResult | None:
        with self._lock:
            return self._live_cycle_result

    @property
    def live_cycles_completed(self) -> int:
        with self._lock:
            return self._live_cycles_completed

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
            self._cavebot_active = False
            self._status = SessionStatus(SessionState.STOPPED, "session stopped")

    def start_cavebot(self) -> None:
        with self._lock:
            self._cavebot_active = True
            if self._status.state == SessionState.RUNNING:
                self._status = SessionStatus(SessionState.RUNNING, "cavebot started")

    def stop_cavebot(self) -> None:
        with self._lock:
            self._cavebot_active = False
            if self._status.state == SessionState.RUNNING:
                self._status = SessionStatus(SessionState.RUNNING, "cavebot stopped")

    def start_healing_bootstrap_session(
        self,
        profile: ProfileSettings,
        profile_path,
    ) -> SessionRunResult:
        with self._lock:
            self._cavebot_active = profile.hunt.enabled
            self._live_cycle_result = None
            self._live_cycles_completed = 0
            self._status = SessionStatus(SessionState.RUNNING, "healing bootstrap session started")
            self._last_result = None

        try:
            window = self._window_service.get_game_window()
            whole_window_region = self._capture_service.whole_window_region(window)
            self._capture_service.capture_window(window)

            self._calibration_service.update_profile_resolution(profile, window)
            self._calibration_service.save_profile(profile_path, profile)
            calibration_snapshot = self._calibration_service.build_snapshot(window, profile)
            resolution_validation = self._calibration_service.validate_window_resolution(profile, window)

            if not resolution_validation.matches_profile:
                with self._lock:
                    self._cavebot_active = False
                    self._status = SessionStatus(SessionState.FAILED, resolution_validation.message)
                    result = SessionRunResult(
                        status=self._status,
                        window=window,
                        whole_window_region=whole_window_region,
                        calibration_snapshot=calibration_snapshot,
                        resolution_validation=resolution_validation,
                        healing_loop_result=None,
                        error_message=resolution_validation.message,
                    )
                    self._last_result = result
                    return result

            healing_loop_result = self._healing_loop.run(
                profile,
                should_continue=self._should_continue,
                is_paused=self._is_paused,
                is_cavebot_active=self._is_cavebot_active,
                on_cycle=self._on_cycle_update,
            )

            with self._lock:
                self._cavebot_active = False
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
                resolution_validation=resolution_validation,
                healing_loop_result=healing_loop_result,
                error_message=None,
            )
            with self._lock:
                self._last_result = result
            return result
        except (WindowDiscoveryError, RuntimeError) as error:
            with self._lock:
                self._cavebot_active = False
                self._status = SessionStatus(SessionState.FAILED, str(error))
                result = SessionRunResult(
                    status=self._status,
                    window=None,
                    whole_window_region=None,
                    calibration_snapshot=None,
                    resolution_validation=None,
                    healing_loop_result=None,
                    error_message=str(error),
                )
                self._last_result = result
                return result

    def capture_preview(self, profile: ProfileSettings) -> SessionPreviewResult:
        try:
            window = self._window_service.get_game_window()
            whole_window_image = self._capture_service.capture_window(window)
            calibration_snapshot = self._calibration_service.build_snapshot(window, profile)
            resolution_validation = self._calibration_service.validate_window_resolution(profile, window)
            life_image = self._crop_window_image(window, whole_window_image, calibration_snapshot.life_bar)
            mana_image = self._crop_window_image(window, whole_window_image, calibration_snapshot.mana_bar)
            target_image = self._crop_window_image(window, whole_window_image, calibration_snapshot.target_status)
            life_preview = self._vision_service.build_preview(life_image)
            mana_preview = self._vision_service.build_preview(mana_image)
            target_preview = self._vision_service.build_target_preview(target_image)

            return SessionPreviewResult(
                status=SessionStatus(SessionState.IDLE, "preview captured"),
                window=window,
                calibration_snapshot=calibration_snapshot,
                resolution_validation=resolution_validation,
                life_preview=life_preview,
                mana_preview=mana_preview,
                target_preview=target_preview,
                error_message=None,
            )
        except (WindowDiscoveryError, RuntimeError) as error:
            return SessionPreviewResult(
                status=SessionStatus(SessionState.FAILED, str(error)),
                window=None,
                calibration_snapshot=None,
                resolution_validation=None,
                life_preview=None,
                mana_preview=None,
                target_preview=None,
                error_message=str(error),
            )

    def analyze_visual_state(self, profile: ProfileSettings) -> AIVisionAnalysisResult:
        if self._ai_vision_assistant is None:
            return build_error_analysis(
                "AI vision assistant is disabled. Configure ai_vision in settings.json first."
            )
        try:
            window = self._window_service.get_game_window()
            whole_window_region = self._capture_service.whole_window_region(window)
            whole_window_image = self._capture_service.capture_window(window)
            calibration_snapshot = self._calibration_service.build_snapshot(window, profile)
            resolution_validation = self._calibration_service.validate_window_resolution(profile, window)

            life_image = self._crop_window_image(window, whole_window_image, calibration_snapshot.life_bar)
            mana_image = self._crop_window_image(window, whole_window_image, calibration_snapshot.mana_bar)
            target_image = self._crop_window_image(window, whole_window_image, calibration_snapshot.target_status)
            life_preview = self._vision_service.build_preview(life_image)
            mana_preview = self._vision_service.build_preview(mana_image)
            target_preview = self._vision_service.build_target_preview(target_image)

            request = AIVisionRequest(
                profile_name=profile.name,
                resolution_width=profile.resolution_width,
                resolution_height=profile.resolution_height,
                ui_scale=profile.ui_scale,
                window_title=window.title,
                window_width=window.width,
                window_height=window.height,
                resolution_validation_message=(
                    resolution_validation.message if resolution_validation is not None else "unavailable"
                ),
                whole_window_image=whole_window_image,
                life_image=life_image,
                mana_image=mana_image,
                target_image=target_image,
                life_ocr_text=life_preview.normalized_text,
                mana_ocr_text=mana_preview.normalized_text,
                target_ocr_text=target_preview.normalized_text,
            )
            return self._ai_vision_assistant.analyze(request)
        except (WindowDiscoveryError, RuntimeError) as error:
            return build_error_analysis(str(error))

    @staticmethod
    def _crop_window_image(window: WindowInfo, whole_window_image, region: ScreenRegion):
        relative_left = max(0, region.left - window.left)
        relative_top = max(0, region.top - window.top)
        relative_right = min(window.width, relative_left + region.width)
        relative_bottom = min(window.height, relative_top + region.height)
        return whole_window_image.crop(
            (relative_left, relative_top, relative_right, relative_bottom)
        )

    def _should_continue(self) -> bool:
        with self._lock:
            return self._status.state != SessionState.STOPPED

    def _is_paused(self) -> bool:
        with self._lock:
            return self._status.state == SessionState.PAUSED

    def _is_cavebot_active(self) -> bool:
        with self._lock:
            return self._cavebot_active

    def _on_cycle_update(self, cycle_result: HealingCycleResult, cycles_completed: int) -> None:
        with self._lock:
            self._live_cycle_result = cycle_result
            self._live_cycles_completed = cycles_completed

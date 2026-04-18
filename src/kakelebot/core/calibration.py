from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.capture import ScreenRegion
from kakelebot.core.config import NormalizedRegionSettings, ProfileSettings, save_profile
from kakelebot.core.window import WindowInfo


@dataclass(frozen=True, slots=True)
class CalibrationSnapshot:
    window_width: int
    window_height: int
    life_bar: ScreenRegion
    mana_bar: ScreenRegion
    target_status: ScreenRegion
    minimap: ScreenRegion


@dataclass(frozen=True, slots=True)
class WindowResolutionValidation:
    configured_width: int
    configured_height: int
    actual_width: int
    actual_height: int
    profile_resolution_set: bool
    matches_profile: bool
    message: str


class CalibrationService:
    def build_snapshot(self, window: WindowInfo, profile: ProfileSettings) -> CalibrationSnapshot:
        return CalibrationSnapshot(
            window_width=window.width,
            window_height=window.height,
            life_bar=self._to_screen_region("life-bar", window, profile.rois.life_bar),
            mana_bar=self._to_screen_region("mana-bar", window, profile.rois.mana_bar),
            target_status=self._to_screen_region("target-status", window, profile.rois.target_status),
            minimap=self._to_screen_region("minimap", window, profile.rois.minimap),
        )

    def update_profile_resolution(self, profile: ProfileSettings, window: WindowInfo) -> None:
        if profile.resolution_width <= 0 or profile.resolution_height <= 0:
            profile.resolution_width = window.width
            profile.resolution_height = window.height

    def validate_window_resolution(
        self,
        profile: ProfileSettings,
        window: WindowInfo,
    ) -> WindowResolutionValidation:
        configured_width = profile.resolution_width
        configured_height = profile.resolution_height
        actual_width = window.width
        actual_height = window.height

        profile_resolution_set = configured_width > 0 and configured_height > 0
        if not profile_resolution_set:
            return WindowResolutionValidation(
                configured_width=configured_width,
                configured_height=configured_height,
                actual_width=actual_width,
                actual_height=actual_height,
                profile_resolution_set=False,
                matches_profile=True,
                message="profile resolution not set; current window can be adopted",
            )

        matches_profile = configured_width == actual_width and configured_height == actual_height
        if matches_profile:
            message = "window resolution matches profile"
        else:
            message = (
                f"window resolution mismatch: profile expects {configured_width}x{configured_height}, "
                f"current window is {actual_width}x{actual_height}"
            )

        return WindowResolutionValidation(
            configured_width=configured_width,
            configured_height=configured_height,
            actual_width=actual_width,
            actual_height=actual_height,
            profile_resolution_set=True,
            matches_profile=matches_profile,
            message=message,
        )

    def save_profile(self, profile_path, profile: ProfileSettings) -> None:
        save_profile(profile_path, profile)

    @staticmethod
    def _to_screen_region(
        name: str,
        window: WindowInfo,
        roi: NormalizedRegionSettings,
    ) -> ScreenRegion:
        return ScreenRegion(
            name=name,
            left=window.left + int(window.width * roi.left_ratio),
            top=window.top + int(window.height * roi.top_ratio),
            width=max(1, int(window.width * roi.width_ratio)),
            height=max(1, int(window.height * roi.height_ratio)),
        )

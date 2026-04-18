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
        profile.resolution_width = window.width
        profile.resolution_height = window.height

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

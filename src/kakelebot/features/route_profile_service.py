from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from kakelebot.core.config import ProfileSettings, load_profile, save_profile
from kakelebot.features.route_recorder import RecordedRoute


class RouteProfileService:
    def save_recorded_route(
        self,
        *,
        profile_path: Path,
        recorded_route: RecordedRoute,
        mode: str = "replace",
        section: str = "hunt",
        enable_coordinate_navigation: bool = True,
    ) -> ProfileSettings:
        profile = load_profile(profile_path)
        updated_profile = self.merge_recorded_route(
            profile=profile,
            recorded_route=recorded_route,
            mode=mode,
            section=section,
            enable_coordinate_navigation=enable_coordinate_navigation,
        )
        save_profile(profile_path, updated_profile)
        return updated_profile

    def merge_recorded_route(
        self,
        *,
        profile: ProfileSettings,
        recorded_route: RecordedRoute,
        mode: str = "replace",
        section: str = "hunt",
        enable_coordinate_navigation: bool = True,
    ) -> ProfileSettings:
        normalized_mode = mode.strip().lower()
        normalized_section = section.strip().lower() or "hunt"
        incoming_waypoints = [
            replace(waypoint, section=normalized_section)
            for waypoint in recorded_route.waypoints
        ]

        if normalized_mode == "replace":
            merged_waypoints = incoming_waypoints
        elif normalized_mode == "append":
            merged_waypoints = list(profile.hunt.waypoints)
            if merged_waypoints and incoming_waypoints:
                if self._same_position(merged_waypoints[-1], incoming_waypoints[0]):
                    incoming_waypoints = incoming_waypoints[1:]
            merged_waypoints.extend(incoming_waypoints)
        else:
            raise ValueError(f"Unsupported route merge mode: {mode}")

        profile.hunt.waypoints = merged_waypoints
        if merged_waypoints and enable_coordinate_navigation:
            profile.hunt.use_coordinate_navigation = True
        return profile

    @staticmethod
    def _same_position(left, right) -> bool:
        return (
            left.target_x == right.target_x
            and left.target_y == right.target_y
            and left.target_z == right.target_z
        )

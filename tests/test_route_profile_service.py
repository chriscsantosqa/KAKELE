from __future__ import annotations

from kakelebot.core.config import HuntWaypoint, ProfileSettings
from kakelebot.features.route_profile_service import RouteProfileService
from kakelebot.features.route_recorder import RecordedRoute


def test_route_profile_service_replaces_existing_route_and_applies_section():
    service = RouteProfileService()
    profile = ProfileSettings()
    profile.hunt.waypoints = [
        HuntWaypoint(direction="RIGHT", target_x=10, target_y=10, target_z=7, section="old")
    ]

    updated = service.merge_recorded_route(
        profile=profile,
        recorded_route=RecordedRoute(
            waypoints=(
                HuntWaypoint(direction="RIGHT", target_x=100, target_y=100, target_z=7),
                HuntWaypoint(direction="DOWN", target_x=101, target_y=100, target_z=7),
            )
        ),
        mode="replace",
        section="refill",
    )

    assert len(updated.hunt.waypoints) == 2
    assert updated.hunt.waypoints[0].target_x == 100
    assert updated.hunt.waypoints[0].section == "refill"
    assert updated.hunt.use_coordinate_navigation is True


def test_route_profile_service_appends_route_and_skips_duplicate_join_waypoint():
    service = RouteProfileService()
    profile = ProfileSettings()
    profile.hunt.waypoints = [
        HuntWaypoint(direction="RIGHT", target_x=100, target_y=100, target_z=7, section="hunt"),
        HuntWaypoint(direction="DOWN", target_x=101, target_y=100, target_z=7, section="hunt"),
    ]

    updated = service.merge_recorded_route(
        profile=profile,
        recorded_route=RecordedRoute(
            waypoints=(
                HuntWaypoint(direction="LEFT", target_x=101, target_y=100, target_z=7),
                HuntWaypoint(direction="LEFT", target_x=102, target_y=100, target_z=7),
            )
        ),
        mode="append",
        section="escape",
    )

    assert len(updated.hunt.waypoints) == 3
    assert updated.hunt.waypoints[-1].target_x == 102
    assert updated.hunt.waypoints[-1].section == "escape"

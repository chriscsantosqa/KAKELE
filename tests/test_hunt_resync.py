from __future__ import annotations

from kakelebot.core.config import HuntWaypoint
from kakelebot.features.hunt_runtime import HuntRuntime


def test_hunt_runtime_resyncs_to_nearest_waypoint_when_player_is_far_from_current_target():
    runtime = HuntRuntime()
    waypoints = [
        HuntWaypoint(direction="RIGHT", target_x=10, target_y=10, target_z=7, section="hunt"),
        HuntWaypoint(direction="DOWN", target_x=100, target_y=100, target_z=7, section="refill"),
    ]

    result = runtime.next_action(
        enabled=True,
        loop_route=False,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=True,
        coordinate_tolerance=0,
        player_position=(100, 100, 7),
        waypoints=waypoints,
        now=1.0,
    )

    assert result.current_section == "refill"
    assert result.waypoint_index == 1


def test_hunt_runtime_does_not_resync_when_player_is_still_close_enough_to_current_waypoint():
    runtime = HuntRuntime()
    waypoints = [
        HuntWaypoint(direction="RIGHT", target_x=10, target_y=10, target_z=7, section="hunt"),
        HuntWaypoint(direction="DOWN", target_x=100, target_y=100, target_z=7, section="refill"),
    ]

    result = runtime.next_action(
        enabled=True,
        loop_route=False,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=True,
        coordinate_tolerance=10,
        player_position=(12, 12, 7),
        waypoints=waypoints,
        now=1.0,
    )

    assert result.current_section == "hunt"
    assert result.waypoint_index == 0

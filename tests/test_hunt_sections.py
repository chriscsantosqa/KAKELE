from __future__ import annotations

from kakelebot.core.config import HuntWaypoint
from kakelebot.features.hunt_runtime import HuntRuntime


def test_hunt_runtime_exposes_current_section_from_active_waypoint():
    runtime = HuntRuntime()
    waypoints = [
        HuntWaypoint(direction="RIGHT", repeats=1, section="hunt"),
        HuntWaypoint(direction="DOWN", repeats=1, section="refill"),
    ]

    first = runtime.next_action(
        enabled=True,
        loop_route=False,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=False,
        coordinate_tolerance=0,
        player_position=None,
        waypoints=waypoints,
        now=1.0,
    )
    second = runtime.next_action(
        enabled=True,
        loop_route=False,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=False,
        coordinate_tolerance=0,
        player_position=None,
        waypoints=waypoints,
        now=2.0,
    )

    assert first.current_section == "hunt"
    assert second.current_section == "refill"

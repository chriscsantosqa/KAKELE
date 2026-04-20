from __future__ import annotations

from kakelebot.core.config import HuntWaypoint
from kakelebot.features.hunt_runtime import HuntRuntime


def test_hunt_runtime_moves_toward_coordinate_waypoint_using_player_position():
    runtime = HuntRuntime()

    result = runtime.next_action(
        enabled=True,
        loop_route=True,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=True,
        coordinate_tolerance=0,
        player_position=(100, 100, 7),
        waypoints=[HuntWaypoint(direction="RIGHT", target_x=102, target_y=100, target_z=7)],
        now=1.0,
    )

    assert result.action is not None
    assert result.action.key == "RIGHT"
    assert result.status == "coordinate-executed"


def test_hunt_runtime_marks_waypoint_as_reached_when_inside_coordinate_tolerance():
    runtime = HuntRuntime()

    result = runtime.next_action(
        enabled=True,
        loop_route=False,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=True,
        coordinate_tolerance=1,
        player_position=(100, 100, 7),
        waypoints=[HuntWaypoint(direction="RIGHT", target_x=101, target_y=100, target_z=7)],
        now=1.0,
    )

    assert result.action is None
    assert result.status == "waypoint-reached"


def test_hunt_runtime_falls_back_to_directional_navigation_without_player_position():
    runtime = HuntRuntime()

    result = runtime.next_action(
        enabled=True,
        loop_route=True,
        waypoint_interval_seconds=0.0,
        move_up_hotkey="UP",
        move_down_hotkey="DOWN",
        move_left_hotkey="LEFT",
        move_right_hotkey="RIGHT",
        use_coordinate_navigation=True,
        coordinate_tolerance=0,
        player_position=None,
        waypoints=[HuntWaypoint(direction="LEFT", repeats=1)],
        now=1.0,
    )

    assert result.action is not None
    assert result.action.key == "LEFT"
    assert result.status == "executed"

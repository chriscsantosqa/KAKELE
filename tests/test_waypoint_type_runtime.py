from __future__ import annotations

from kakelebot.core.config import HuntWaypoint
from kakelebot.features.hunt_runtime import HuntRuntime


def test_hunt_runtime_holds_position_on_stand_waypoint_until_wait_completes():
    runtime = HuntRuntime()
    waypoint = HuntWaypoint(
        direction="RIGHT",
        target_x=100,
        target_y=100,
        target_z=7,
        waypoint_type="stand",
        wait_time_ms=1000,
    )

    first = runtime.next_action(
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
        waypoints=[waypoint],
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
        use_coordinate_navigation=True,
        coordinate_tolerance=0,
        player_position=(100, 100, 7),
        waypoints=[waypoint],
        now=1.5,
    )
    third = runtime.next_action(
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
        waypoints=[waypoint],
        now=2.1,
    )

    assert first.action is None
    assert first.status == "stand-wait"
    assert second.action is None
    assert second.status == "stand-wait"
    assert third.action is None
    assert third.status == "stand-complete"


def test_hunt_runtime_executes_action_waypoint_and_waits_before_advancing():
    runtime = HuntRuntime()
    waypoint = HuntWaypoint(
        direction="RIGHT",
        target_x=100,
        target_y=100,
        target_z=7,
        waypoint_type="action",
        action_key="F6",
        wait_time_ms=500,
        label="use-lever",
    )

    first = runtime.next_action(
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
        waypoints=[waypoint],
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
        use_coordinate_navigation=True,
        coordinate_tolerance=0,
        player_position=(100, 100, 7),
        waypoints=[waypoint],
        now=1.2,
    )
    third = runtime.next_action(
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
        waypoints=[waypoint],
        now=1.6,
    )

    assert first.action is not None
    assert first.action.key == "F6"
    assert first.status == "action-executed"
    assert second.action is None
    assert second.status == "action-wait"
    assert third.action is None
    assert third.status == "action-complete"

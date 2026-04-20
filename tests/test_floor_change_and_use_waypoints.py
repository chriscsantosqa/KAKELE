from __future__ import annotations

from kakelebot.core.config import HuntWaypoint
from kakelebot.features.hunt_runtime import HuntRuntime


def test_hunt_runtime_executes_use_waypoint_and_waits_before_advancing():
    runtime = HuntRuntime()
    waypoint = HuntWaypoint(
        direction="RIGHT",
        target_x=100,
        target_y=100,
        target_z=7,
        waypoint_type="use",
        action_key="F6",
        wait_time_ms=500,
        label="usar-portal",
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
    assert first.status == "use-executed"
    assert second.action is None
    assert second.status == "use-wait"
    assert third.action is None
    assert third.status == "use-complete"


def test_hunt_runtime_waits_for_natural_floor_change_until_target_z_is_reached():
    runtime = HuntRuntime()
    waypoint = HuntWaypoint(
        direction="UP",
        target_x=50,
        target_y=50,
        target_z=6,
        waypoint_type="floor-change",
        wait_time_ms=300,
        label="subir-escada",
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
        player_position=(50, 50, 7),
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
        player_position=(50, 50, 7),
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
        player_position=(50, 50, 6),
        waypoints=[waypoint],
        now=2.0,
    )

    assert first.action is None
    assert first.status == "floor-change-wait"
    assert second.action is None
    assert second.status == "floor-change-wait"
    assert third.action is None
    assert third.status == "floor-change-complete"

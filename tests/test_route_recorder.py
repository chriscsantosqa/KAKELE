from __future__ import annotations

from kakelebot.features.route_recorder import RouteRecorder


def test_route_recorder_compacts_straight_segments_and_keeps_turn_nodes():
    recorder = RouteRecorder(minimum_step_distance=1)
    recorder.start()

    recorder.record_position((100, 100, 7))
    recorder.record_position((101, 100, 7))
    recorder.record_position((102, 100, 7))
    recorder.record_position((102, 101, 7))
    recorder.record_position((102, 102, 7))

    route = recorder.stop()

    assert len(route.waypoints) == 3
    assert route.waypoints[0].label == "start"
    assert route.waypoints[0].waypoint_type == "start"
    assert route.waypoints[1].label == "node-1"
    assert route.waypoints[1].waypoint_type == "node"
    assert route.waypoints[2].label == "end"
    assert route.waypoints[2].waypoint_type == "stand"
    assert route.waypoints[1].target_x == 102
    assert route.waypoints[1].target_y == 100


def test_route_recorder_keeps_floor_change_as_explicit_node():
    recorder = RouteRecorder(minimum_step_distance=1)
    recorder.start()

    recorder.record_position((100, 100, 7))
    recorder.record_position((101, 100, 7))
    recorder.record_position((101, 100, 8))

    route = recorder.stop()

    assert len(route.waypoints) == 3
    assert route.waypoints[1].target_z == 7
    assert route.waypoints[2].target_z == 8

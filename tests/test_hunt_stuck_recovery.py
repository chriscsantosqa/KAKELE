from __future__ import annotations

from collections import deque

from PIL import Image

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService, ScreenRegion
from kakelebot.core.config import HuntWaypoint
from kakelebot.core.input import InputService
from kakelebot.core.memory import MemoryReadResult, PlayerState
from kakelebot.core.vision import BarReading
from kakelebot.core.window import WindowInfo
from kakelebot.features.healing import HealingService
from kakelebot.features.healing_runtime import HealingRuntime


class _CaptureAdapter:
    def capture_region(self, left: int, top: int, width: int, height: int):
        return Image.new("RGB", (width, height), "black")

    def capture_window(self, window: WindowInfo):
        return Image.new("RGB", (window.width, window.height), "black")


class _VisionService:
    def read_bar_value(self, image):
        return BarReading(current=90, maximum=100, source_text="vision", confidence_ok=True)

    def build_target_preview(self, image):
        class Target:
            has_target = False
            normalized_text = ""

        return Target()


class _InputAdapter:
    def __init__(self):
        self.pressed: list[str] = []

    def press(self, key: str, hold_seconds: float = 0.0) -> None:
        self.pressed.append(key)


class _MemoryServiceSequence:
    def __init__(self, positions: list[tuple[int, int, int]]):
        self._positions = deque(positions)
        self._last = positions[-1]

    def try_get_player_state(self):
        if self._positions:
            self._last = self._positions.popleft()
        x, y, z = self._last
        return MemoryReadResult(
            available=True,
            state=PlayerState(
                hp=100,
                max_hp=100,
                mp=100,
                max_mp=100,
                x=x,
                y=y,
                z=z,
                level=1,
                exp=0,
                has_target=False,
                target_id=0,
            ),
            source="test",
            error=None,
        )


def _build_runtime(memory_service):
    input_adapter = _InputAdapter()
    runtime = HealingRuntime(
        capture_service=CaptureService(_CaptureAdapter()),
        vision_service=_VisionService(),
        healing_service=HealingService(),
        input_service=InputService(input_adapter),
        memory_service=memory_service,
    )

    window = WindowInfo(title="Kakele", left=0, top=0, width=800, height=600, is_active=True)
    snap = CalibrationSnapshot(
        window_width=800,
        window_height=600,
        life_bar=ScreenRegion("life", 0, 0, 100, 20),
        mana_bar=ScreenRegion("mana", 0, 20, 100, 20),
        target_status=ScreenRegion("target", 0, 40, 100, 20),
        minimap=ScreenRegion("minimap", 600, 0, 200, 200),
    )
    return runtime, input_adapter, window, snap


def _run_cycle(runtime, window, snap):
    return runtime.execute_cycle(
        window=window,
        snapshot=snap,
        life_hotkey="F1",
        mana_hotkey="F2",
        haste_hotkey="F3",
        attack_hotkey="F4",
        secondary_attack_hotkey="F5",
        haste_enabled=False,
        haste_interval_seconds=30,
        haste_cooldown_seconds=1,
        attack_enabled=False,
        attack_cooldown_seconds=0,
        secondary_attack_enabled=False,
        secondary_attack_cooldown_seconds=1,
        secondary_attack_after_primary_only=True,
        secondary_attack_combo_window_seconds=1,
        target_confirmation_cycles=1,
        target_stability_window=2,
        max_target_text_variants=10,
        life_threshold_percent=10,
        mana_threshold_percent=10,
        life_cooldown_seconds=1,
        mana_cooldown_seconds=1,
        window_is_active=True,
        hunt_enabled=True,
        hunt_loop_route=True,
        hunt_waypoint_interval_seconds=0,
        hunt_move_up_hotkey="UP",
        hunt_move_down_hotkey="DOWN",
        hunt_move_left_hotkey="LEFT",
        hunt_move_right_hotkey="RIGHT",
        hunt_waypoints=[HuntWaypoint(direction="UP", repeats=1, relative_x=0, relative_y=-1)],
        memory_enabled=True,
        memory_prefer_for_healing=True,
        memory_prefer_for_target=True,
        memory_prefer_for_cavebot=True,
        memory_process_name="kakele.exe",
    )


def test_hunt_triggers_stuck_recovery_when_position_does_not_change():
    runtime, input_adapter, window, snap = _build_runtime(
        _MemoryServiceSequence(positions=[(100, 100, 7)] * 6)
    )

    results = [_run_cycle(runtime, window, snap) for _ in range(6)]

    assert any(result.hunt_status == "stuck-recovery" for result in results)
    # primeiro movimento é UP; recuperação lateral esperada é LEFT
    assert "LEFT" in input_adapter.pressed


def test_hunt_does_not_trigger_recovery_when_position_progresses():
    runtime, input_adapter, window, snap = _build_runtime(
        _MemoryServiceSequence(positions=[(100, 100, 7), (100, 99, 7), (100, 98, 7), (100, 97, 7), (100, 96, 7)])
    )

    results = [_run_cycle(runtime, window, snap) for _ in range(5)]

    assert all(result.hunt_status != "stuck-recovery" for result in results)
    assert "LEFT" not in input_adapter.pressed

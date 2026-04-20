from __future__ import annotations

from PIL import Image

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService, ScreenRegion
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
        return BarReading(current=10, maximum=100, source_text="vision", confidence_ok=True)

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


class _MemoryService:
    def __init__(self, has_target: bool = True):
        self._has_target = has_target

    def try_get_player_state(self):
        return MemoryReadResult(
            available=True,
            state=PlayerState(
                hp=95,
                max_hp=100,
                mp=90,
                max_mp=100,
                x=100,
                y=200,
                z=7,
                level=1,
                exp=0,
                has_target=self._has_target,
                target_id=123,
            ),
            source="test",
            error=None,
        )


def test_healing_runtime_prefers_memory_for_heal_and_target():
    input_adapter = _InputAdapter()
    runtime = HealingRuntime(
        capture_service=CaptureService(_CaptureAdapter()),
        vision_service=_VisionService(),
        healing_service=HealingService(),
        input_service=InputService(input_adapter),
        memory_service=_MemoryService(has_target=True),
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

    result = runtime.execute_cycle(
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
        attack_enabled=True,
        attack_cooldown_seconds=0,
        secondary_attack_enabled=False,
        secondary_attack_cooldown_seconds=1,
        secondary_attack_after_primary_only=True,
        secondary_attack_combo_window_seconds=1,
        target_confirmation_cycles=1,
        target_stability_window=1,
        max_target_text_variants=10,
        life_threshold_percent=60,
        mana_threshold_percent=40,
        life_cooldown_seconds=1,
        mana_cooldown_seconds=1,
        window_is_active=True,
        hunt_enabled=False,
        hunt_loop_route=False,
        hunt_waypoint_interval_seconds=1,
        hunt_move_up_hotkey="UP",
        hunt_move_down_hotkey="DOWN",
        hunt_move_left_hotkey="LEFT",
        hunt_move_right_hotkey="RIGHT",
        hunt_waypoints=[],
        memory_enabled=True,
        memory_prefer_for_healing=True,
        memory_prefer_for_target=True,
        memory_prefer_for_cavebot=True,
        memory_process_name="kakele.exe",
    )

    assert result.data_source in {"memory-hybrid", "memory-target"}
    assert result.memory_status.startswith("memory-ok")
    assert result.life_reading is not None
    assert result.life_reading.current == 95
    assert result.decision.should_heal_life is False
    assert result.has_target is True
    assert "F4" in input_adapter.pressed

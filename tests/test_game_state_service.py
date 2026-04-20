from __future__ import annotations

from kakelebot.core.game_state import GameStateService
from kakelebot.core.memory import MemoryReadResult, PlayerState
from kakelebot.core.vision import BarReading, TargetPreview


def _memory_result() -> MemoryReadResult:
    return MemoryReadResult(
        available=True,
        state=PlayerState(
            hp=100,
            max_hp=200,
            mp=50,
            max_mp=100,
            x=10,
            y=20,
            z=7,
            level=1,
            exp=0,
            has_target=True,
            target_id=999,
        ),
        source="MemoryAdapter",
        error=None,
    )


def _target_preview() -> TargetPreview:
    return TargetPreview(
        original_image=None,
        processed_image=None,
        raw_text="orc",
        normalized_text="orc",
        has_target=True,
        reason="ocr-text-detected",
        activity_ratio=0.2,
        contrast_score=30.0,
    )


def test_game_state_prefers_memory_when_enabled():
    service = GameStateService()

    state = service.build_state(
        life_reading=BarReading(10, 100, "vision-life", True),
        mana_reading=BarReading(20, 100, "vision-mana", True),
        target_preview=_target_preview(),
        memory_result=_memory_result(),
        memory_enabled=True,
        memory_prefer_for_healing=True,
        memory_prefer_for_target=True,
        memory_prefer_for_cavebot=True,
        memory_process_name="kakele.exe",
    )

    assert state.vitals.life is not None
    assert state.vitals.life.current == 100
    assert state.vitals.mana is not None
    assert state.vitals.mana.current == 50
    assert state.target.target_reason == "memory"
    assert state.navigation.player_position == (10, 20, 7)
    assert state.vitals.memory_status == "memory-ok:kakele.exe"


def test_game_state_falls_back_to_vision_when_memory_is_unavailable():
    service = GameStateService()

    state = service.build_state(
        life_reading=BarReading(10, 100, "vision-life", True),
        mana_reading=BarReading(20, 100, "vision-mana", True),
        target_preview=_target_preview(),
        memory_result=None,
        memory_enabled=False,
        memory_prefer_for_healing=True,
        memory_prefer_for_target=True,
        memory_prefer_for_cavebot=True,
        memory_process_name="kakele.exe",
    )

    assert state.vitals.life is not None
    assert state.vitals.life.current == 10
    assert state.vitals.mana is not None
    assert state.vitals.mana.current == 20
    assert state.target.target_reason == "vision"
    assert state.target.target_text == "orc"
    assert state.navigation.player_position is None
    assert state.vitals.memory_status == "memory-disabled"

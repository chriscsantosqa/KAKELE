from __future__ import annotations

from kakelebot.core.memory import MemoryReadResult, PlayerState
from kakelebot.core.memory_field_tester import MemoryFieldTester
from kakelebot.core.memory_validator import MemorySnapshotValidator


class _FakeMemoryService:
    def __init__(self, result: MemoryReadResult) -> None:
        self._result = result

    def try_get_player_state(self) -> MemoryReadResult:
        return self._result


class _FakeTester(MemoryFieldTester):
    def __init__(self, result: MemoryReadResult) -> None:
        super().__init__()
        self._result = result

    def test_field(self, *, memory_settings, field_name: str):
        return super().test_field(memory_settings=memory_settings, field_name=field_name)


def test_memory_validator_can_validate_only_position_fields():
    validator = MemorySnapshotValidator()

    result = validator.validate(
        {
            "hp": 0,
            "max_hp": 0,
            "mp": 0,
            "max_mp": 0,
            "x": 123,
            "y": 456,
            "z": 7,
            "has_target": 0,
            "target_id": 0,
        },
        required_fields={"x", "y", "z"},
    )

    assert result.is_valid is True
    assert result.reasons == tuple()


def test_memory_field_tester_extracts_coordinate_value_when_snapshot_is_valid(monkeypatch):
    from kakelebot.core import memory_field_tester as module
    from kakelebot.core.config import MemorySettings

    state = PlayerState(
        hp=100,
        max_hp=100,
        mp=50,
        max_mp=50,
        x=321,
        y=654,
        z=8,
        level=12,
        exp=987,
        has_target=False,
        target_id=0,
    )
    result = MemoryReadResult(available=True, state=state, source="fake")
    monkeypatch.setattr(module, "build_memory_service", lambda _settings: _FakeMemoryService(result))

    tester = MemoryFieldTester()
    tested = tester.test_field(memory_settings=MemorySettings(enabled=True), field_name="x")

    assert tested.success is True
    assert tested.value == 321
    assert tested.message == "ok"


def test_memory_field_tester_rejects_invalid_target_pair(monkeypatch):
    from kakelebot.core import memory_field_tester as module
    from kakelebot.core.config import MemorySettings

    state = PlayerState(
        hp=100,
        max_hp=100,
        mp=50,
        max_mp=50,
        x=321,
        y=654,
        z=8,
        level=12,
        exp=987,
        has_target=True,
        target_id=0,
    )
    result = MemoryReadResult(available=True, state=state, source="fake")
    monkeypatch.setattr(module, "build_memory_service", lambda _settings: _FakeMemoryService(result))

    tester = MemoryFieldTester()
    tested = tester.test_field(memory_settings=MemorySettings(enabled=True), field_name="target_id")

    assert tested.success is False
    assert tested.value == 0
    assert "target_id must be positive" in tested.message

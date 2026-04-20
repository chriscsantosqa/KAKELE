from __future__ import annotations

from kakelebot.core.memory import MemoryService


class _OkAdapter:
    def read_all_offsets(self):
        return {
            "hp": 123,
            "max_hp": 456,
            "mp": 11,
            "max_mp": 22,
            "x": 10,
            "y": 20,
            "z": 7,
            "level": 99,
            "exp": 1000,
            "has_target": 1,
            "target_id": 777,
        }


class _FailAdapter:
    def read_all_offsets(self):
        raise RuntimeError("boom")


class _DiagnosticsAdapter:
    def read_with_diagnostics(self):
        return {
            "values": {
                "hp": 80,
                "max_hp": 100,
                "mp": 30,
                "max_mp": 100,
                "x": 10,
                "y": 20,
                "z": 7,
                "has_target": 0,
                "target_id": 0,
            },
            "errors": {
                "target_id": "failed to read address",
            },
        }


def test_try_get_player_state_success():
    service = MemoryService(_OkAdapter())

    result = service.try_get_player_state()

    assert result.available is True
    assert result.state is not None
    assert result.state.hp == 123
    assert result.state.has_target is True
    assert result.state.target_id == 777


def test_try_get_player_state_failure_is_graceful():
    service = MemoryService(_FailAdapter())

    result = service.try_get_player_state()

    assert result.available is False
    assert result.state is None
    assert "boom" in (result.error or "")


def test_try_get_player_state_uses_diagnostics_payload():
    service = MemoryService(_DiagnosticsAdapter())

    result = service.try_get_player_state()

    assert result.available is True
    assert result.state is not None
    assert result.state.hp == 80
    assert result.field_errors is not None
    assert "target_id" in result.field_errors

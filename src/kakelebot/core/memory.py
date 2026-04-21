from __future__ import annotations

from dataclasses import dataclass
import logging

from kakelebot.core.memory_validator import MemorySnapshotValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PlayerState:
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    x: int
    y: int
    z: int
    level: int
    exp: int
    has_target: bool
    target_id: int


@dataclass(frozen=True, slots=True)
class MemoryReadResult:
    available: bool
    state: PlayerState | None
    source: str
    error: str | None = None


class MemoryService:
    def __init__(self, adapter: any, validator: MemorySnapshotValidator | None = None):
        self._adapter = adapter
        self._validator = validator or MemorySnapshotValidator()

    def try_get_player_state(self, required_fields: set[str] | None = None) -> MemoryReadResult:
        try:
            data = self._adapter.read_all_offsets()
            validation = self._validator.validate(data, required_fields=required_fields)
            if not validation.is_valid:
                error_message = "; ".join(validation.reasons)
                logger.warning("memory read rejected by validator: %s", error_message)
                return MemoryReadResult(
                    available=False,
                    state=None,
                    source=self._adapter.__class__.__name__,
                    error=error_message,
                )

            state = PlayerState(
                hp=max(0, int(data.get("hp", 0))),
                max_hp=max(1, int(data.get("max_hp", 100))),
                mp=max(0, int(data.get("mp", 0))),
                max_mp=max(1, int(data.get("max_mp", 100))),
                x=int(data.get("x", 0)),
                y=int(data.get("y", 0)),
                z=int(data.get("z", 0)),
                level=max(1, int(data.get("level", 1))),
                exp=max(0, int(data.get("exp", 0))),
                has_target=bool(int(data.get("has_target", 0))),
                target_id=max(0, int(data.get("target_id", 0))),
            )
            return MemoryReadResult(
                available=True,
                state=state,
                source=self._adapter.__class__.__name__,
                error=None,
            )
        except Exception as error:  # noqa: BLE001 - memory adapter failures must degrade gracefully
            logger.warning("memory read failed: %s", error)
            return MemoryReadResult(
                available=False,
                state=None,
                source=self._adapter.__class__.__name__,
                error=str(error),
            )

    def get_player_state(self, required_fields: set[str] | None = None) -> PlayerState:
        result = self.try_get_player_state(required_fields=required_fields)
        if not result.available or result.state is None:
            raise RuntimeError(result.error or "memory unavailable")
        return result.state

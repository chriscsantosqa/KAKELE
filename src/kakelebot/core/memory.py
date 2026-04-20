from __future__ import annotations
from dataclasses import dataclass
import logging

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
    field_errors: dict[str, str] | None = None
    raw_values: dict[str, int] | None = None


class MemoryService:
    def __init__(self, adapter: any):
        self._adapter = adapter

    def try_get_player_state(self) -> MemoryReadResult:
        try:
            diagnostics_reader = getattr(self._adapter, "read_with_diagnostics", None)
            if callable(diagnostics_reader):
                payload = diagnostics_reader()
                data = payload.get("values", {})
                field_errors = payload.get("errors", {})
            else:
                data = self._adapter.read_all_offsets()
                field_errors = {}

            required_fields = ("hp", "max_hp", "mp", "max_mp", "x", "y", "z", "has_target", "target_id")
            missing = [name for name in required_fields if name not in data]
            if missing:
                message = f"missing required fields: {', '.join(missing)}"
                return MemoryReadResult(
                    available=False,
                    state=None,
                    source=self._adapter.__class__.__name__,
                    error=message,
                    field_errors=field_errors,
                    raw_values=data,
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
                field_errors=field_errors,
                raw_values=data,
            )
        except Exception as error:  # noqa: BLE001 - memory adapter failures must degrade gracefully
            logger.warning("memory read failed: %s", error)
            return MemoryReadResult(
                available=False,
                state=None,
                source=self._adapter.__class__.__name__,
                error=str(error),
                field_errors=None,
                raw_values=None,
            )

    def get_player_state(self) -> PlayerState:
        result = self.try_get_player_state()
        if not result.available or result.state is None:
            raise RuntimeError(result.error or "memory unavailable")
        return result.state

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

class MemoryService:
    def __init__(self, adapter: any):
        self._adapter = adapter

    def get_player_state(self) -> PlayerState:
        # Aqui o adaptador lerá os endereços de memória reais
        data = self._adapter.read_all_offsets()
        return PlayerState(
            hp=data.get("hp", 0),
            max_hp=data.get("max_hp", 100),
            mp=data.get("mp", 0),
            max_mp=data.get("max_mp", 100),
            x=data.get("x", 0),
            y=data.get("y", 0),
            z=data.get("z", 0),
            level=data.get("level", 1),
            exp=data.get("exp", 0)
        )
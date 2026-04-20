from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.config import SpecialArea


@dataclass(frozen=True, slots=True)
class SpecialAreaMatch:
    area: SpecialArea
    wait_time_ms: int


class SpecialAreaService:
    def match(
        self,
        *,
        player_position: tuple[int, int, int] | None,
        special_areas: list[SpecialArea],
    ) -> SpecialAreaMatch | None:
        if player_position is None:
            return None

        px, py, pz = player_position
        for area in special_areas:
            if pz != area.z:
                continue
            if not (area.x <= px < area.x + area.width):
                continue
            if not (area.y <= py < area.y + area.height):
                continue
            return SpecialAreaMatch(
                area=area,
                wait_time_ms=max(area.wait_time_min_ms, area.wait_time_max_ms),
            )
        return None

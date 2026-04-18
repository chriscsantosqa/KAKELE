from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.vision import BarReading


@dataclass(frozen=True, slots=True)
class HealingDecision:
    should_heal_life: bool
    should_heal_mana: bool
    reason: str


class HealingService:
    def evaluate(
        self,
        life: BarReading | None,
        mana: BarReading | None,
        life_threshold_percent: int,
        mana_threshold_percent: int,
    ) -> HealingDecision:
        reasons: list[str] = []
        should_heal_life = False
        should_heal_mana = False

        if life is not None and life.percentage <= life_threshold_percent:
            should_heal_life = True
            reasons.append(
                f"life={life.current}/{life.maximum} ({life.percentage:.1f}%) <= {life_threshold_percent}%"
            )

        if mana is not None and mana.percentage <= mana_threshold_percent:
            should_heal_mana = True
            reasons.append(
                f"mana={mana.current}/{mana.maximum} ({mana.percentage:.1f}%) <= {mana_threshold_percent}%"
            )

        if not reasons:
            reasons.append("thresholds not reached")

        return HealingDecision(
            should_heal_life=should_heal_life,
            should_heal_mana=should_heal_mana,
            reason="; ".join(reasons),
        )

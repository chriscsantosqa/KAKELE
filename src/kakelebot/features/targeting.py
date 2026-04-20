from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from kakelebot.core.game_state import TargetState


@dataclass(frozen=True, slots=True)
class TargetEvaluation:
    has_target: bool
    target_text: str
    target_reason: str
    confirmed: bool
    oscillating: bool
    valid: bool
    failure_reason: str


class TargetPolicyService:
    def evaluate(
        self,
        *,
        target_state: TargetState,
        recent_observations: deque[tuple[bool, str]],
        confirmation_cycles: int,
        stability_window: int,
        max_target_text_variants: int,
    ) -> TargetEvaluation:
        has_target = target_state.has_target
        target_text = target_state.target_text
        target_reason = target_state.target_reason

        recent_observations.append((has_target, target_text))

        confirmed = self._target_confirmed(recent_observations, confirmation_cycles)
        oscillating = self._target_oscillating(
            recent_observations,
            stability_window,
            max_target_text_variants,
        )
        valid = has_target and confirmed and not oscillating
        failure_reason = self._failure_reason(
            has_target=has_target,
            confirmed=confirmed,
            oscillating=oscillating,
        )

        return TargetEvaluation(
            has_target=has_target,
            target_text=target_text,
            target_reason=target_reason,
            confirmed=confirmed,
            oscillating=oscillating,
            valid=valid,
            failure_reason=failure_reason,
        )

    @staticmethod
    def _target_confirmed(
        recent_observations: deque[tuple[bool, str]],
        cycles: int,
    ) -> bool:
        if len(recent_observations) < cycles:
            return False
        return all(x[0] for x in list(recent_observations)[-cycles:])

    @staticmethod
    def _target_oscillating(
        recent_observations: deque[tuple[bool, str]],
        window: int,
        max_variants: int,
    ) -> bool:
        if len(recent_observations) < window:
            return False

        recent = list(recent_observations)[-window:]
        flips = sum(
            1 for i in range(1, len(recent))
            if recent[i][0] != recent[i - 1][0]
        )
        texts = {text for has_target, text in recent if has_target}

        return flips >= 2 or len(texts) > max_variants

    @staticmethod
    def _failure_reason(*, has_target: bool, confirmed: bool, oscillating: bool) -> str:
        if not has_target:
            return "no-target"
        if not confirmed:
            return "unconfirmed-target"
        if oscillating:
            return "oscillating-target"
        return "valid-target"

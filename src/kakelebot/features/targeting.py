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
    matched_allowed_rule: bool
    matched_blocked_rule: bool


class TargetPolicyService:
    def evaluate(
        self,
        *,
        target_state: TargetState,
        recent_observations: deque[tuple[bool, str]],
        confirmation_cycles: int,
        stability_window: int,
        max_target_text_variants: int,
        allowed_target_texts: list[str],
        blocked_target_texts: list[str],
        require_target_text_match: bool,
    ) -> TargetEvaluation:
        has_target = target_state.has_target
        target_text = target_state.target_text
        target_reason = target_state.target_reason

        recent_observations.append((has_target, target_text))

        normalized_target_text = self._normalize_text(target_text)
        normalized_allowed_texts = [self._normalize_text(value) for value in allowed_target_texts if value.strip()]
        normalized_blocked_texts = [self._normalize_text(value) for value in blocked_target_texts if value.strip()]

        confirmed = self._target_confirmed(recent_observations, confirmation_cycles)
        oscillating = self._target_oscillating(
            recent_observations,
            stability_window,
            max_target_text_variants,
        )
        matched_allowed_rule = self._matches_any_rule(normalized_target_text, normalized_allowed_texts)
        matched_blocked_rule = self._matches_any_rule(normalized_target_text, normalized_blocked_texts)

        valid = (
            has_target
            and confirmed
            and not oscillating
            and not matched_blocked_rule
            and (not require_target_text_match or matched_allowed_rule)
        )
        failure_reason = self._failure_reason(
            has_target=has_target,
            confirmed=confirmed,
            oscillating=oscillating,
            matched_allowed_rule=matched_allowed_rule,
            matched_blocked_rule=matched_blocked_rule,
            require_target_text_match=require_target_text_match,
        )

        return TargetEvaluation(
            has_target=has_target,
            target_text=target_text,
            target_reason=target_reason,
            confirmed=confirmed,
            oscillating=oscillating,
            valid=valid,
            failure_reason=failure_reason,
            matched_allowed_rule=matched_allowed_rule,
            matched_blocked_rule=matched_blocked_rule,
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
    def _matches_any_rule(target_text: str, rules: list[str]) -> bool:
        if not target_text or not rules:
            return False
        return any(rule in target_text for rule in rules)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _failure_reason(
        *,
        has_target: bool,
        confirmed: bool,
        oscillating: bool,
        matched_allowed_rule: bool,
        matched_blocked_rule: bool,
        require_target_text_match: bool,
    ) -> str:
        if not has_target:
            return "no-target"
        if not confirmed:
            return "unconfirmed-target"
        if oscillating:
            return "oscillating-target"
        if matched_blocked_rule:
            return "blocked-target"
        if require_target_text_match and not matched_allowed_rule:
            return "target-not-allowed"
        return "valid-target"

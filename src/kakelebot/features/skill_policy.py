from __future__ import annotations

from dataclasses import dataclass

from kakelebot.features.targeting import TargetEvaluation


@dataclass(frozen=True, slots=True)
class SecondarySkillEvaluation:
    allowed: bool
    reason: str
    matched_allowed_rule: bool
    matched_blocked_rule: bool


class SecondarySkillPolicyService:
    def evaluate(
        self,
        *,
        target_evaluation: TargetEvaluation,
        allowed_target_texts: list[str],
        blocked_target_texts: list[str],
        require_target_text_match: bool,
    ) -> SecondarySkillEvaluation:
        if not target_evaluation.valid:
            return SecondarySkillEvaluation(
                allowed=False,
                reason=target_evaluation.failure_reason,
                matched_allowed_rule=False,
                matched_blocked_rule=False,
            )

        normalized_target_text = self._normalize_text(target_evaluation.target_text)
        normalized_allowed_texts = [self._normalize_text(value) for value in allowed_target_texts if value.strip()]
        normalized_blocked_texts = [self._normalize_text(value) for value in blocked_target_texts if value.strip()]

        matched_allowed_rule = self._matches_any_rule(normalized_target_text, normalized_allowed_texts)
        matched_blocked_rule = self._matches_any_rule(normalized_target_text, normalized_blocked_texts)

        if matched_blocked_rule:
            return SecondarySkillEvaluation(
                allowed=False,
                reason="secondary-skill-blocked-target",
                matched_allowed_rule=matched_allowed_rule,
                matched_blocked_rule=True,
            )

        if require_target_text_match and not matched_allowed_rule:
            return SecondarySkillEvaluation(
                allowed=False,
                reason="secondary-skill-target-not-allowed",
                matched_allowed_rule=False,
                matched_blocked_rule=False,
            )

        return SecondarySkillEvaluation(
            allowed=True,
            reason="secondary-skill-allowed",
            matched_allowed_rule=matched_allowed_rule,
            matched_blocked_rule=matched_blocked_rule,
        )

    @staticmethod
    def _matches_any_rule(target_text: str, rules: list[str]) -> bool:
        if not target_text or not rules:
            return False
        return any(rule in target_text for rule in rules)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return value.strip().lower()

from __future__ import annotations

from kakelebot.features.skill_policy import SecondarySkillPolicyService
from kakelebot.features.targeting import TargetEvaluation


def _valid_target(target_text: str = "orc warrior") -> TargetEvaluation:
    return TargetEvaluation(
        has_target=True,
        target_text=target_text,
        target_reason="vision",
        confirmed=True,
        oscillating=False,
        valid=True,
        failure_reason="valid-target",
        matched_allowed_rule=True,
        matched_blocked_rule=False,
    )


def test_secondary_skill_policy_allows_skill_for_valid_target_by_default():
    service = SecondarySkillPolicyService()

    result = service.evaluate(
        target_evaluation=_valid_target(),
        allowed_target_texts=[],
        blocked_target_texts=[],
        require_target_text_match=False,
    )

    assert result.allowed is True
    assert result.reason == "secondary-skill-allowed"


def test_secondary_skill_policy_blocks_skill_when_target_matches_blocklist():
    service = SecondarySkillPolicyService()

    result = service.evaluate(
        target_evaluation=_valid_target("goblin mage"),
        allowed_target_texts=[],
        blocked_target_texts=["goblin"],
        require_target_text_match=False,
    )

    assert result.allowed is False
    assert result.reason == "secondary-skill-blocked-target"
    assert result.matched_blocked_rule is True


def test_secondary_skill_policy_requires_allowlist_match_when_enabled():
    service = SecondarySkillPolicyService()

    result = service.evaluate(
        target_evaluation=_valid_target("orc warrior"),
        allowed_target_texts=["orc"],
        blocked_target_texts=[],
        require_target_text_match=True,
    )

    assert result.allowed is True
    assert result.matched_allowed_rule is True


def test_secondary_skill_policy_rejects_when_allowlist_is_required_but_not_matched():
    service = SecondarySkillPolicyService()

    result = service.evaluate(
        target_evaluation=_valid_target("skeleton archer"),
        allowed_target_texts=["orc"],
        blocked_target_texts=[],
        require_target_text_match=True,
    )

    assert result.allowed is False
    assert result.reason == "secondary-skill-target-not-allowed"


def test_secondary_skill_policy_propagates_invalid_target_failure_reason():
    service = SecondarySkillPolicyService()
    invalid_target = TargetEvaluation(
        has_target=False,
        target_text="",
        target_reason="vision",
        confirmed=False,
        oscillating=False,
        valid=False,
        failure_reason="no-target",
        matched_allowed_rule=False,
        matched_blocked_rule=False,
    )

    result = service.evaluate(
        target_evaluation=invalid_target,
        allowed_target_texts=["orc"],
        blocked_target_texts=[],
        require_target_text_match=True,
    )

    assert result.allowed is False
    assert result.reason == "no-target"

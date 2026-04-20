from __future__ import annotations

from kakelebot.features.section_policy import SectionPolicyService


def test_section_policy_allows_full_behavior_in_hunt_section():
    service = SectionPolicyService()

    policy = service.resolve("hunt")

    assert policy.section == "hunt"
    assert policy.allow_primary_attack is True
    assert policy.allow_secondary_attack is True
    assert policy.pause_hunt_during_target is True


def test_section_policy_blocks_combat_and_keeps_route_moving_in_refill_section():
    service = SectionPolicyService()

    policy = service.resolve("refill")

    assert policy.section == "refill"
    assert policy.allow_primary_attack is False
    assert policy.allow_secondary_attack is False
    assert policy.pause_hunt_during_target is False


def test_section_policy_blocks_combat_and_keeps_route_moving_in_escape_section():
    service = SectionPolicyService()

    policy = service.resolve("escape")

    assert policy.section == "escape"
    assert policy.allow_primary_attack is False
    assert policy.allow_secondary_attack is False
    assert policy.pause_hunt_during_target is False

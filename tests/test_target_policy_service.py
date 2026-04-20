from __future__ import annotations

from collections import deque

from kakelebot.core.game_state import TargetState
from kakelebot.features.targeting import TargetPolicyService


def test_target_policy_marks_target_as_valid_when_confirmed_and_stable():
    service = TargetPolicyService()
    recent = deque([(True, "orc")], maxlen=12)

    result = service.evaluate(
        target_state=TargetState(
            has_target=True,
            target_text="orc",
            target_reason="memory",
            data_source="memory-target",
        ),
        recent_observations=recent,
        confirmation_cycles=2,
        stability_window=3,
        max_target_text_variants=2,
    )

    assert result.has_target is True
    assert result.confirmed is True
    assert result.oscillating is False
    assert result.valid is True
    assert result.failure_reason == "valid-target"


def test_target_policy_marks_target_as_oscillating_when_text_varies_too_much():
    service = TargetPolicyService()
    recent = deque(
        [
            (True, "orc"),
            (True, "goblin"),
        ],
        maxlen=12,
    )

    result = service.evaluate(
        target_state=TargetState(
            has_target=True,
            target_text="skeleton",
            target_reason="vision",
            data_source="vision",
        ),
        recent_observations=recent,
        confirmation_cycles=2,
        stability_window=3,
        max_target_text_variants=2,
    )

    assert result.has_target is True
    assert result.confirmed is True
    assert result.oscillating is True
    assert result.valid is False
    assert result.failure_reason == "oscillating-target"


def test_target_policy_marks_target_as_unconfirmed_when_cycles_are_insufficient():
    service = TargetPolicyService()
    recent = deque([], maxlen=12)

    result = service.evaluate(
        target_state=TargetState(
            has_target=True,
            target_text="orc",
            target_reason="memory",
            data_source="memory-target",
        ),
        recent_observations=recent,
        confirmation_cycles=3,
        stability_window=4,
        max_target_text_variants=2,
    )

    assert result.has_target is True
    assert result.confirmed is False
    assert result.valid is False
    assert result.failure_reason == "unconfirmed-target"


def test_target_policy_marks_missing_target_correctly():
    service = TargetPolicyService()
    recent = deque([], maxlen=12)

    result = service.evaluate(
        target_state=TargetState(
            has_target=False,
            target_text="",
            target_reason="vision",
            data_source="vision",
        ),
        recent_observations=recent,
        confirmation_cycles=2,
        stability_window=3,
        max_target_text_variants=2,
    )

    assert result.has_target is False
    assert result.valid is False
    assert result.failure_reason == "no-target"

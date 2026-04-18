from __future__ import annotations

import time
from dataclasses import dataclass

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService
from kakelebot.core.input import InputService, KeyAction
from kakelebot.core.vision import BarReading, VisionService
from kakelebot.features.healing import HealingDecision, HealingService


@dataclass(frozen=True, slots=True)
class HealingCycleResult:
    life_reading: BarReading | None
    mana_reading: BarReading | None
    decision: HealingDecision
    actions_executed: tuple[KeyAction, ...]
    suppressed_actions: tuple[str, ...]
    haste_status: str
    attack_status: str
    has_target: bool
    target_reason: str
    target_text: str


class HealingRuntime:
    def __init__(
        self,
        capture_service: CaptureService,
        vision_service: VisionService,
        healing_service: HealingService,
        input_service: InputService,
    ) -> None:
        self._capture = capture_service
        self._vision = vision_service
        self._healing = healing_service
        self._input = input_service
        self._time_provider = time.monotonic
        self._last_life_action_at: float | None = None
        self._last_mana_action_at: float | None = None
        self._last_haste_action_at: float | None = None
        self._last_attack_action_at: float | None = None

    def execute_cycle(
        self,
        snapshot: CalibrationSnapshot,
        life_hotkey: str,
        mana_hotkey: str,
        haste_hotkey: str,
        attack_hotkey: str,
        haste_enabled: bool,
        haste_interval_seconds: float,
        haste_cooldown_seconds: float,
        attack_enabled: bool,
        attack_cooldown_seconds: float,
        life_threshold_percent: int,
        mana_threshold_percent: int,
        life_cooldown_seconds: float,
        mana_cooldown_seconds: float,
        window_is_active: bool,
    ) -> HealingCycleResult:
        life_image = self._capture.capture(snapshot.life_bar)
        mana_image = self._capture.capture(snapshot.mana_bar)
        target_image = self._capture.capture(snapshot.target_status)

        life_reading = self._vision.read_bar_value(life_image)
        mana_reading = self._vision.read_bar_value(mana_image)
        target_preview = self._vision.build_target_preview(target_image)

        decision = self._healing.evaluate(
            life=life_reading,
            mana=mana_reading,
            life_threshold_percent=life_threshold_percent,
            mana_threshold_percent=mana_threshold_percent,
        )

        executed_actions: list[KeyAction] = []
        suppressed_actions: list[str] = []
        haste_status = "disabled"
        attack_status = "disabled"

        if not window_is_active:
            suppressed_actions.append("window-inactive")
            if haste_enabled:
                haste_status = "window-inactive"
            if attack_enabled:
                attack_status = "window-inactive"
        else:
            if decision.should_heal_life:
                if self._can_execute_life(life_cooldown_seconds):
                    action = KeyAction(key=life_hotkey, reason=decision.reason)
                    self._input.execute(action)
                    executed_actions.append(action)
                    self._last_life_action_at = self._time_provider()
                else:
                    suppressed_actions.append("life-cooldown")

            if decision.should_heal_mana:
                if self._can_execute_mana(mana_cooldown_seconds):
                    action = KeyAction(key=mana_hotkey, reason=decision.reason)
                    self._input.execute(action)
                    executed_actions.append(action)
                    self._last_mana_action_at = self._time_provider()
                else:
                    suppressed_actions.append("mana-cooldown")

            attack_status = self._try_execute_attack(
                attack_hotkey=attack_hotkey,
                attack_enabled=attack_enabled,
                attack_cooldown_seconds=attack_cooldown_seconds,
                has_target=target_preview.has_target,
                executed_actions=executed_actions,
                suppressed_actions=suppressed_actions,
            )

            haste_status = self._try_execute_haste(
                haste_hotkey=haste_hotkey,
                haste_enabled=haste_enabled,
                haste_interval_seconds=haste_interval_seconds,
                haste_cooldown_seconds=haste_cooldown_seconds,
                executed_actions=executed_actions,
            )

        return HealingCycleResult(
            life_reading=life_reading,
            mana_reading=mana_reading,
            decision=decision,
            actions_executed=tuple(executed_actions),
            suppressed_actions=tuple(suppressed_actions),
            haste_status=haste_status,
            attack_status=attack_status,
            has_target=target_preview.has_target,
            target_reason=target_preview.reason,
            target_text=target_preview.normalized_text,
        )

    def _try_execute_attack(
        self,
        attack_hotkey: str,
        attack_enabled: bool,
        attack_cooldown_seconds: float,
        has_target: bool,
        executed_actions: list[KeyAction],
        suppressed_actions: list[str],
    ) -> str:
        if not attack_enabled:
            return "disabled"
        if not has_target:
            suppressed_actions.append("attack-no-target")
            return "no-target"
        if not self._can_execute_attack(attack_cooldown_seconds):
            suppressed_actions.append("attack-cooldown")
            return "cooldown"

        action = KeyAction(key=attack_hotkey, reason="target-detected")
        self._input.execute(action)
        executed_actions.append(action)
        self._last_attack_action_at = self._time_provider()
        return "executed"

    def _try_execute_haste(
        self,
        haste_hotkey: str,
        haste_enabled: bool,
        haste_interval_seconds: float,
        haste_cooldown_seconds: float,
        executed_actions: list[KeyAction],
    ) -> str:
        if not haste_enabled:
            return "disabled"

        if not self._haste_due(haste_interval_seconds):
            return "not-due"

        if not self._can_execute_haste(haste_cooldown_seconds):
            return "cooldown"

        action = KeyAction(key=haste_hotkey, reason="haste-interval-elapsed")
        self._input.execute(action)
        executed_actions.append(action)
        self._last_haste_action_at = self._time_provider()
        return "executed"

    def _can_execute_life(self, cooldown_seconds: float) -> bool:
        if self._last_life_action_at is None:
            return True
        return (self._time_provider() - self._last_life_action_at) >= cooldown_seconds

    def _can_execute_mana(self, cooldown_seconds: float) -> bool:
        if self._last_mana_action_at is None:
            return True
        return (self._time_provider() - self._last_mana_action_at) >= cooldown_seconds

    def _can_execute_haste(self, cooldown_seconds: float) -> bool:
        if self._last_haste_action_at is None:
            return True
        return (self._time_provider() - self._last_haste_action_at) >= cooldown_seconds

    def _can_execute_attack(self, cooldown_seconds: float) -> bool:
        if self._last_attack_action_at is None:
            return True
        return (self._time_provider() - self._last_attack_action_at) >= cooldown_seconds

    def _haste_due(self, interval_seconds: float) -> bool:
        if self._last_haste_action_at is None:
            return True
        return (self._time_provider() - self._last_haste_action_at) >= interval_seconds

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService
from kakelebot.core.input import InputService, KeyAction
from kakelebot.core.vision import BarReading, VisionService
from kakelebot.core.window import WindowInfo
from kakelebot.features.healing import HealingDecision, HealingService
from kakelebot.core.config import HuntWaypoint
from kakelebot.features.hunt_runtime import HuntRuntime


@dataclass(frozen=True, slots=True)
class HealingCycleResult:
    life_reading: BarReading | None
    mana_reading: BarReading | None
    decision: HealingDecision
    actions_executed: tuple[KeyAction, ...]
    suppressed_actions: tuple[str, ...]
    haste_status: str
    attack_status: str
    secondary_attack_status: str
    has_target: bool
    target_confirmed: bool
    target_oscillating: bool
    target_reason: str
    target_text: str
    hunt_status: str


class HealingRuntime:
    _MULTI_ACTION_DELAY_SECONDS = 0.0

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
        self._hunt = HuntRuntime()
        self._time_provider = time.monotonic
        self._last_life_action_at: float | None = None
        self._last_mana_action_at: float | None = None
        self._last_haste_action_at: float | None = None
        self._last_attack_action_at: float | None = None
        self._last_secondary_attack_action_at: float | None = None
        self._last_primary_attack_at: float | None = None
        self._recent_target_observations: deque[tuple[bool, str]] = deque(maxlen=12)

    def execute_cycle(
        self,
        window: WindowInfo,
        snapshot: CalibrationSnapshot,
        life_hotkey: str,
        mana_hotkey: str,
        haste_hotkey: str,
        attack_hotkey: str,
        secondary_attack_hotkey: str,
        haste_enabled: bool,
        haste_interval_seconds: float,
        haste_cooldown_seconds: float,
        attack_enabled: bool,
        attack_cooldown_seconds: float,
        secondary_attack_enabled: bool,
        secondary_attack_cooldown_seconds: float,
        secondary_attack_after_primary_only: bool,
        secondary_attack_combo_window_seconds: float,
        target_confirmation_cycles: int,
        target_stability_window: int,
        max_target_text_variants: int,
        life_threshold_percent: int,
        mana_threshold_percent: int,
        life_cooldown_seconds: float,
        mana_cooldown_seconds: float,
        window_is_active: bool,
        hunt_enabled: bool,
        hunt_loop_route: bool,
        hunt_waypoint_interval_seconds: float,
        hunt_move_up_hotkey: str,
        hunt_move_down_hotkey: str,
        hunt_move_left_hotkey: str,
        hunt_move_right_hotkey: str,
        hunt_waypoints: list[HuntWaypoint],
    ) -> HealingCycleResult:
        if not window_is_active:
            return self._inactive_window_result(
                haste_enabled=haste_enabled,
                attack_enabled=attack_enabled,
                secondary_attack_enabled=secondary_attack_enabled,
                hunt_enabled=hunt_enabled,
            )

        whole_window_image = self._capture.capture_window(window)
        life_image = self._crop_from_window_buffer(window, whole_window_image, snapshot.life_bar)
        mana_image = self._crop_from_window_buffer(window, whole_window_image, snapshot.mana_bar)

        life_reading = self._vision.read_bar_value(life_image)
        mana_reading = self._vision.read_bar_value(mana_image)
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
        secondary_attack_status = "disabled"
        hunt_status = "disabled"
        has_target = False
        target_confirmed = False
        target_oscillating = False
        target_reason = "not-evaluated"
        target_text = ""

        immediate_actions: list[KeyAction] = []
        now = self._time_provider()
        life_critical = self._life_is_critical(life_reading, life_threshold_percent)

        if decision.should_heal_life:
            if self._can_execute_life(life_cooldown_seconds):
                immediate_actions.append(KeyAction(key=life_hotkey, reason=decision.reason))
                self._last_life_action_at = now
            else:
                suppressed_actions.append("life-cooldown")

        if decision.should_heal_mana:
            if self._can_execute_mana(mana_cooldown_seconds):
                immediate_actions.append(KeyAction(key=mana_hotkey, reason=decision.reason))
                self._last_mana_action_at = now
            else:
                suppressed_actions.append("mana-cooldown")

        target_image = self._crop_from_window_buffer(window, whole_window_image, snapshot.target_status)
        target_preview = self._vision.build_target_preview(target_image)
        has_target = target_preview.has_target
        target_reason = target_preview.reason
        target_text = target_preview.normalized_text
        self._record_target_observation(has_target, target_text)
        target_confirmed = self._target_confirmed(target_confirmation_cycles)
        target_oscillating = self._target_oscillating(
            target_stability_window=target_stability_window,
            max_target_text_variants=max_target_text_variants,
        )

        if life_critical:
            suppressed_actions.append("combat-deprioritized-due-critical-life")
            if haste_enabled:
                haste_status = "deprioritized-due-critical-life"
            if attack_enabled:
                attack_status = "deprioritized-due-critical-life"
            if secondary_attack_enabled:
                secondary_attack_status = "deprioritized-due-critical-life"
            if hunt_enabled:
                hunt_status = "deprioritized-due-critical-life"
            if immediate_actions:
                self._input.execute_many(immediate_actions, self._MULTI_ACTION_DELAY_SECONDS)
                executed_actions.extend(immediate_actions)
            return HealingCycleResult(
                life_reading=life_reading,
                mana_reading=mana_reading,
                decision=decision,
                actions_executed=tuple(executed_actions),
                suppressed_actions=tuple(suppressed_actions),
                haste_status=haste_status,
                attack_status=attack_status,
                secondary_attack_status=secondary_attack_status,
                hunt_status=hunt_status,
                has_target=has_target,
                target_confirmed=target_confirmed,
                target_oscillating=target_oscillating,
                target_reason="critical-life-priority",
                target_text=target_text,
            )

        if attack_enabled:
            attack_status = self._queue_attack(
                attack_hotkey=attack_hotkey,
                attack_cooldown_seconds=attack_cooldown_seconds,
                has_target=has_target,
                target_confirmed=target_confirmed,
                target_oscillating=target_oscillating,
                queued_actions=immediate_actions,
                suppressed_actions=suppressed_actions,
            )

        if secondary_attack_enabled:
            secondary_attack_status = self._queue_secondary_attack(
                secondary_attack_hotkey=secondary_attack_hotkey,
                secondary_attack_cooldown_seconds=secondary_attack_cooldown_seconds,
                secondary_attack_after_primary_only=secondary_attack_after_primary_only,
                secondary_attack_combo_window_seconds=secondary_attack_combo_window_seconds,
                has_target=has_target,
                target_confirmed=target_confirmed,
                target_oscillating=target_oscillating,
                primary_attack_status=attack_status,
                queued_actions=immediate_actions,
                suppressed_actions=suppressed_actions,
            )

        if haste_enabled:
            haste_status = self._queue_haste(
                haste_hotkey=haste_hotkey,
                haste_interval_seconds=haste_interval_seconds,
                haste_cooldown_seconds=haste_cooldown_seconds,
                queued_actions=immediate_actions,
            )
         
        if hunt_enabled:
            hunt_status = self._queue_hunt(
                loop_route=hunt_loop_route,
                waypoint_interval_seconds=hunt_waypoint_interval_seconds,
                move_up_hotkey=hunt_move_up_hotkey,
                move_down_hotkey=hunt_move_down_hotkey,
                move_left_hotkey=hunt_move_left_hotkey,
                move_right_hotkey=hunt_move_right_hotkey,
                waypoints=hunt_waypoints,
                has_target=has_target,
                queued_actions=immediate_actions,
                now=now,
                suppressed_actions=suppressed_actions,
            )
        else:
            hunt_status = "disabled" 

        if immediate_actions:
            self._input.execute_many(immediate_actions, self._MULTI_ACTION_DELAY_SECONDS)
            executed_actions.extend(immediate_actions)

        return HealingCycleResult(
            life_reading=life_reading,
            mana_reading=mana_reading,
            decision=decision,
            actions_executed=tuple(executed_actions),
            suppressed_actions=tuple(suppressed_actions),
            haste_status=haste_status,
            attack_status=attack_status,
            secondary_attack_status=secondary_attack_status,
            hunt_status=hunt_status,
            has_target=has_target,
            target_confirmed=target_confirmed,
            target_oscillating=target_oscillating,
            target_reason=target_reason,
            target_text=target_text,
        )

    def _inactive_window_result(
        self,
        *,
        haste_enabled: bool,
        attack_enabled: bool,
        secondary_attack_enabled: bool,
        hunt_enabled: bool,
    ) -> HealingCycleResult:
        suppressed_actions = ["window-inactive"]
        return HealingCycleResult(
            life_reading=None,
            mana_reading=None,
            decision=HealingDecision(False, False, "window-inactive"),
            actions_executed=tuple(),
            suppressed_actions=tuple(suppressed_actions),
            haste_status="window-inactive" if haste_enabled else "disabled",
            attack_status="window-inactive" if attack_enabled else "disabled",
            secondary_attack_status="window-inactive" if secondary_attack_enabled else "disabled",
            hunt_status="window-inactive" if hunt_enabled else "disabled",
            has_target=False,
            target_confirmed=False,
            target_oscillating=False,
            target_reason="window-inactive",
            target_text="",
        )

    @staticmethod
    def _crop_from_window_buffer(window: WindowInfo, whole_window_image, region) -> object:
        relative_left = max(0, region.left - window.left)
        relative_top = max(0, region.top - window.top)
        relative_right = min(window.width, relative_left + region.width)
        relative_bottom = min(window.height, relative_top + region.height)
        return whole_window_image.crop(
            (relative_left, relative_top, relative_right, relative_bottom)
        )

    @staticmethod
    def _life_is_critical(life_reading: BarReading | None, threshold_percent: int) -> bool:
        if life_reading is None:
            return False
        critical_threshold = max(18.0, threshold_percent * 0.55)
        return life_reading.percentage <= critical_threshold

    def _record_target_observation(self, has_target: bool, normalized_text: str) -> None:
        signal = normalized_text.strip().lower() or "<empty>"
        self._recent_target_observations.append((has_target, signal))

    def _target_confirmed(self, required_cycles: int) -> bool:
        if required_cycles <= 1:
            return bool(self._recent_target_observations and self._recent_target_observations[-1][0])
        if len(self._recent_target_observations) < required_cycles:
            return False
        recent = list(self._recent_target_observations)[-required_cycles:]
        return all(has_target for has_target, _ in recent)

    def _target_oscillating(self, target_stability_window: int, max_target_text_variants: int) -> bool:
        if target_stability_window <= 1 or len(self._recent_target_observations) < 2:
            return False

        window = list(self._recent_target_observations)[-target_stability_window:]
        state_flips = sum(
            1
            for index in range(1, len(window))
            if window[index][0] != window[index - 1][0]
        )
        text_variants = {
            text
            for has_target, text in window
            if has_target and text != "<empty>"
        }
        return state_flips >= 2 or len(text_variants) > max_target_text_variants

    def _queue_attack(
        self,
        attack_hotkey: str,
        attack_cooldown_seconds: float,
        has_target: bool,
        target_confirmed: bool,
        target_oscillating: bool,
        queued_actions: list[KeyAction],
        suppressed_actions: list[str],
    ) -> str:
        if not has_target:
            suppressed_actions.append("attack-no-target")
            return "no-target"
        if not target_confirmed:
            suppressed_actions.append("attack-awaiting-confirmation")
            return "awaiting-confirmation"
        if target_oscillating:
            suppressed_actions.append("attack-target-oscillating")
            return "target-oscillating"
        if not self._can_execute_attack(attack_cooldown_seconds):
            suppressed_actions.append("attack-cooldown")
            return "cooldown"

        queued_actions.append(KeyAction(key=attack_hotkey, reason="target-confirmed"))
        now = self._time_provider()
        self._last_attack_action_at = now
        self._last_primary_attack_at = now
        return "executed"

    def _queue_secondary_attack(
        self,
        secondary_attack_hotkey: str,
        secondary_attack_cooldown_seconds: float,
        secondary_attack_after_primary_only: bool,
        secondary_attack_combo_window_seconds: float,
        has_target: bool,
        target_confirmed: bool,
        target_oscillating: bool,
        primary_attack_status: str,
        queued_actions: list[KeyAction],
        suppressed_actions: list[str],
    ) -> str:
        if not has_target:
            suppressed_actions.append("secondary-no-target")
            return "no-target"
        if not target_confirmed:
            suppressed_actions.append("secondary-awaiting-confirmation")
            return "awaiting-confirmation"
        if target_oscillating:
            suppressed_actions.append("secondary-target-oscillating")
            return "target-oscillating"
        if secondary_attack_after_primary_only and not self._combo_window_open(
            primary_attack_status=primary_attack_status,
            combo_window_seconds=secondary_attack_combo_window_seconds,
        ):
            suppressed_actions.append("secondary-awaiting-primary")
            return "awaiting-primary"
        if not self._can_execute_secondary_attack(secondary_attack_cooldown_seconds):
            suppressed_actions.append("secondary-cooldown")
            return "cooldown"

        queued_actions.append(KeyAction(key=secondary_attack_hotkey, reason="combo-follow-up"))
        self._last_secondary_attack_action_at = self._time_provider()
        return "executed"

    def _combo_window_open(self, primary_attack_status: str, combo_window_seconds: float) -> bool:
        if primary_attack_status == "executed":
            return True
        if self._last_primary_attack_at is None:
            return False
        return (self._time_provider() - self._last_primary_attack_at) <= combo_window_seconds

    def _queue_haste(
        self,
        haste_hotkey: str,
        haste_interval_seconds: float,
        haste_cooldown_seconds: float,
        queued_actions: list[KeyAction],
    ) -> str:
        if not self._haste_due(haste_interval_seconds):
            return "not-due"
        if not self._can_execute_haste(haste_cooldown_seconds):
            return "cooldown"
        queued_actions.append(KeyAction(key=haste_hotkey, reason="haste-interval-elapsed"))
        self._last_haste_action_at = self._time_provider()
        return "executed"

    def _queue_hunt(
        self,
        *,
        loop_route: bool,
        waypoint_interval_seconds: float,
        move_up_hotkey: str,
        move_down_hotkey: str,
        move_left_hotkey: str,
        move_right_hotkey: str,
        waypoints: list[HuntWaypoint],
        has_target: bool,
        queued_actions: list[KeyAction],
        now: float,
        suppressed_actions: list[str],
    ) -> str:
        if has_target:
            suppressed_actions.append("hunt-paused-during-target")
            return "paused-during-target"

        hunt_cycle_action = self._hunt.next_action(
            enabled=True,
            loop_route=loop_route,
            waypoint_interval_seconds=waypoint_interval_seconds,
            move_up_hotkey=move_up_hotkey,
            move_down_hotkey=move_down_hotkey,
            move_left_hotkey=move_left_hotkey,
            move_right_hotkey=move_right_hotkey,
            waypoints=waypoints,
            now=now,
        )

        if hunt_cycle_action.action is not None:
            queued_actions.append(hunt_cycle_action.action)
        else:
            suppressed_actions.append(f"hunt-{hunt_cycle_action.status}")

        return hunt_cycle_action.status
    
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

    def _can_execute_secondary_attack(self, cooldown_seconds: float) -> bool:
        if self._last_secondary_attack_action_at is None:
            return True
        return (self._time_provider() - self._last_secondary_attack_action_at) >= cooldown_seconds

    def _haste_due(self, interval_seconds: float) -> bool:
        if self._last_haste_action_at is None:
            return True
        return (self._time_provider() - self._last_haste_action_at) >= interval_seconds

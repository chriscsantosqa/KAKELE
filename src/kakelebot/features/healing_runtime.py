from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService
from kakelebot.core.game_state import GameStateService
from kakelebot.core.memory import MemoryReadResult, MemoryService
from kakelebot.core.config import HuntWaypoint
from kakelebot.core.input import InputService, KeyAction
from kakelebot.core.vision import BarReading, VisionService
from kakelebot.core.window import WindowInfo
from kakelebot.features.healing import HealingDecision, HealingService
from kakelebot.features.hunt_runtime import HuntCycleAction, HuntRuntime
from kakelebot.features.skill_policy import SecondarySkillPolicyService
from kakelebot.features.targeting import TargetPolicyService


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
    data_source: str
    memory_status: str
    player_position: tuple[int, int, int] | None


class HealingRuntime:
    _MULTI_ACTION_DELAY_SECONDS = 0.0
    _STUCK_CYCLES_FOR_RECOVERY = 4

    def __init__(
        self,
        capture_service: CaptureService,
        vision_service: VisionService,
        healing_service: HealingService,
        input_service: InputService,
        memory_service: MemoryService | None = None,
        game_state_service: GameStateService | None = None,
        target_policy_service: TargetPolicyService | None = None,
        secondary_skill_policy_service: SecondarySkillPolicyService | None = None,
    ) -> None:
        self._capture = capture_service
        self._vision = vision_service
        self._healing = healing_service
        self._input = input_service
        self._memory = memory_service
        self._game_state = game_state_service or GameStateService()
        self._target_policy = target_policy_service or TargetPolicyService()
        self._secondary_skill_policy = secondary_skill_policy_service or SecondarySkillPolicyService()
        self._hunt = HuntRuntime()
        self._time_provider = time.monotonic
        self._recent_target_observations: deque[tuple[bool, str]] = deque(maxlen=12)
        self._last_memory_position: tuple[int, int, int] | None = None
        self._stuck_cycles = 0
        self._last_haste_at: float | None = None
        self._last_attack_at: float | None = None
        self._last_secondary_attack_at: float | None = None

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
        secondary_attack_allowed_target_texts: list[str],
        secondary_attack_blocked_target_texts: list[str],
        secondary_attack_require_target_text_match: bool,
        target_confirmation_cycles: int,
        target_stability_window: int,
        max_target_text_variants: int,
        allowed_target_texts: list[str],
        blocked_target_texts: list[str],
        require_target_text_match: bool,
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
        memory_enabled: bool,
        memory_prefer_for_healing: bool,
        memory_prefer_for_target: bool,
        memory_prefer_for_cavebot: bool,
        memory_process_name: str,
    ) -> HealingCycleResult:

        whole_window_image = self._capture.capture_window(window)

        life_image = self._crop(window, whole_window_image, snapshot.life_bar)
        mana_image = self._crop(window, whole_window_image, snapshot.mana_bar)

        life = self._vision.read_bar_value(life_image)
        mana = self._vision.read_bar_value(mana_image)
        memory_result = self._read_memory_if_enabled(memory_enabled)

        target_img = self._crop(window, whole_window_image, snapshot.target_status)
        target_preview = self._vision.build_target_preview(target_img)

        game_state = self._game_state.build_state(
            life_reading=life,
            mana_reading=mana,
            target_preview=target_preview,
            memory_result=memory_result,
            memory_enabled=memory_enabled,
            memory_prefer_for_healing=memory_prefer_for_healing,
            memory_prefer_for_target=memory_prefer_for_target,
            memory_prefer_for_cavebot=memory_prefer_for_cavebot,
            memory_process_name=memory_process_name,
        )

        life = game_state.vitals.life
        mana = game_state.vitals.mana
        memory_status = game_state.vitals.memory_status
        data_source = game_state.navigation.data_source

        decision = self._healing.evaluate(
            life=life,
            mana=mana,
            life_threshold_percent=life_threshold_percent,
            mana_threshold_percent=mana_threshold_percent,
        )

        actions: list[KeyAction] = []
        suppressed: list[str] = []
        now = self._time_provider()

        target_evaluation = self._target_policy.evaluate(
            target_state=game_state.target,
            recent_observations=self._recent_target_observations,
            confirmation_cycles=target_confirmation_cycles,
            stability_window=target_stability_window,
            max_target_text_variants=max_target_text_variants,
            allowed_target_texts=allowed_target_texts,
            blocked_target_texts=blocked_target_texts,
            require_target_text_match=require_target_text_match,
        )

        valid_target = target_evaluation.valid

        if decision.should_heal_life:
            actions.append(KeyAction(life_hotkey, "heal-life"))

        if decision.should_heal_mana:
            actions.append(KeyAction(mana_hotkey, "heal-mana"))

        haste_status = "disabled"
        if haste_enabled:
            haste_gate = max(haste_interval_seconds, haste_cooldown_seconds)
            if self._can_use_interval(self._last_haste_at, now, haste_gate):
                actions.append(KeyAction(haste_hotkey, "buff-haste"))
                self._last_haste_at = now
                haste_status = "executed"
            else:
                haste_status = "cooldown"

        attack_status = "disabled"
        if attack_enabled:
            if valid_target and self._can_use_interval(self._last_attack_at, now, attack_cooldown_seconds):
                actions.append(KeyAction(attack_hotkey, "attack-primary"))
                self._last_attack_at = now
                attack_status = "executed"
            elif not valid_target:
                attack_status = target_evaluation.failure_reason
            else:
                attack_status = "cooldown"

        secondary_attack_status = "disabled"
        if secondary_attack_enabled:
            secondary_skill_evaluation = self._secondary_skill_policy.evaluate(
                target_evaluation=target_evaluation,
                allowed_target_texts=secondary_attack_allowed_target_texts,
                blocked_target_texts=secondary_attack_blocked_target_texts,
                require_target_text_match=secondary_attack_require_target_text_match,
            )

            allowed_by_primary_rule = True
            if secondary_attack_after_primary_only:
                allowed_by_primary_rule = (
                    self._last_attack_at is not None
                    and (now - self._last_attack_at) <= secondary_attack_combo_window_seconds
                )

            if not secondary_skill_evaluation.allowed:
                secondary_attack_status = secondary_skill_evaluation.reason
            elif not allowed_by_primary_rule:
                secondary_attack_status = "waiting-primary"
            elif self._can_use_interval(
                self._last_secondary_attack_at,
                now,
                secondary_attack_cooldown_seconds,
            ):
                actions.append(KeyAction(secondary_attack_hotkey, "attack-secondary"))
                self._last_secondary_attack_at = now
                secondary_attack_status = "executed"
            else:
                secondary_attack_status = "cooldown"

        hunt_status = "disabled"
        player_position = game_state.navigation.player_position

        if hunt_enabled:
            if valid_target:
                suppressed.append("hunt-paused-during-target")
                hunt_status = "paused-during-target"
            else:
                cycle = self._hunt.next_action(
                    enabled=True,
                    loop_route=hunt_loop_route,
                    waypoint_interval_seconds=hunt_waypoint_interval_seconds,
                    move_up_hotkey=hunt_move_up_hotkey,
                    move_down_hotkey=hunt_move_down_hotkey,
                    move_left_hotkey=hunt_move_left_hotkey,
                    move_right_hotkey=hunt_move_right_hotkey,
                    waypoints=hunt_waypoints,
                    now=self._time_provider(),
                )

                if cycle.action:
                    actions.append(cycle.action)
                else:
                    suppressed.append(f"hunt-{cycle.status}")

                hunt_status = cycle.status
                if memory_prefer_for_cavebot and player_position is not None:
                    recovery_action = self._build_stuck_recovery_action(
                        cycle=cycle,
                        player_position=player_position,
                    )
                    if recovery_action is not None:
                        actions.append(recovery_action)
                        hunt_status = "stuck-recovery"
                        data_source = "memory-hybrid" if data_source != "vision" else "memory-cavebot"

        if actions:
            self._input.execute_many(actions, 0)

        return HealingCycleResult(
            life_reading=life,
            mana_reading=mana,
            decision=decision,
            actions_executed=tuple(actions),
            suppressed_actions=tuple(suppressed),
            haste_status=haste_status,
            attack_status=attack_status,
            secondary_attack_status=secondary_attack_status,
            hunt_status=hunt_status,
            has_target=target_evaluation.has_target,
            target_confirmed=target_evaluation.confirmed,
            target_oscillating=target_evaluation.oscillating,
            target_reason=target_evaluation.target_reason,
            target_text=target_evaluation.target_text,
            data_source=data_source,
            memory_status=memory_status,
            player_position=player_position,
        )

    def _crop(self, window, img, region):
        return img.crop((
            region.left - window.left,
            region.top - window.top,
            region.left - window.left + region.width,
            region.top - window.top + region.height,
        ))

    def _read_memory_if_enabled(self, enabled: bool) -> MemoryReadResult | None:
        if not enabled or self._memory is None:
            return None
        return self._memory.try_get_player_state()

    def _build_stuck_recovery_action(
        self,
        *,
        cycle: HuntCycleAction,
        player_position: tuple[int, int, int],
    ) -> KeyAction | None:
        if cycle.action is None:
            self._last_memory_position = player_position
            self._stuck_cycles = 0
            return None

        if self._last_memory_position == player_position:
            self._stuck_cycles += 1
        else:
            self._stuck_cycles = 0

        self._last_memory_position = player_position

        if self._stuck_cycles < self._STUCK_CYCLES_FOR_RECOVERY:
            return None

        self._stuck_cycles = 0
        return KeyAction(
            key=self._recovery_key_for_direction(cycle.action.key),
            reason="hunt-stuck-recovery",
            hold_seconds=0.035,
        )

    @staticmethod
    def _recovery_key_for_direction(direction_key: str) -> str:
        mapping = {
            "UP": "LEFT",
            "DOWN": "RIGHT",
            "LEFT": "UP",
            "RIGHT": "DOWN",
        }
        normalized = direction_key.strip().upper()
        return mapping.get(normalized, "LEFT")

    @staticmethod
    def _can_use_interval(last_used_at: float | None, now: float, interval_seconds: float) -> bool:
        if last_used_at is None:
            return True
        return (now - last_used_at) >= max(0.0, interval_seconds)

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

from kakelebot.core.calibration import CalibrationService
from kakelebot.core.config import ProfileSettings
from kakelebot.core.window import WindowDiscoveryError, WindowService
from kakelebot.features.healing_runtime import HealingCycleResult, HealingRuntime


@dataclass(frozen=True, slots=True)
class HealingLoopResult:
    cycles_completed: int
    last_cycle: HealingCycleResult | None
    terminated_early: bool
    termination_reason: str | None
    fail_safe_triggered: bool


class HealingLoopRunner:
    _FAILSAFE_DISABLED_ACTIONS_PER_MINUTE = 1000

    def __init__(
        self,
        window_service: WindowService,
        calibration_service: CalibrationService,
        healing_runtime: HealingRuntime,
    ) -> None:
        self._window_service = window_service
        self._calibration_service = calibration_service
        self._healing_runtime = healing_runtime
        self._sleep = time.sleep
        self._time_provider = time.monotonic

    def run(
        self,
        profile: ProfileSettings,
        should_continue: Callable[[], bool] | None = None,
        is_paused: Callable[[], bool] | None = None,
        is_cavebot_active: Callable[[], bool] | None = None,
        on_cycle: Callable[[HealingCycleResult, int], None] | None = None,
    ) -> HealingLoopResult:
        last_cycle: HealingCycleResult | None = None
        cycles_completed = 0
        terminated_early = False
        termination_reason: str | None = None
        fail_safe_triggered = False

        cycle_limit = max(1, profile.healing_loop.bootstrap_cycle_limit)
        continuous_mode = profile.healing_loop.continuous_mode
        cycle_index = 0
        action_times: deque[float] = deque()
        consecutive_ocr_failures = 0
        window_missing_since: float | None = None
        enforce_actions_per_minute_limit = (
            profile.healing_loop.max_actions_per_minute
            < self._FAILSAFE_DISABLED_ACTIONS_PER_MINUTE
        )

        while True:
            cycle_started_at = self._time_provider()

            if should_continue is not None and not should_continue():
                terminated_early = True
                termination_reason = "stopped-by-user"
                break

            while is_paused is not None and is_paused():
                if should_continue is not None and not should_continue():
                    terminated_early = True
                    termination_reason = "stopped-by-user"
                    break
                self._sleep(0.05)

            if terminated_early:
                break

            try:
                window = self._window_service.get_game_window()
                window = self._window_service.activate_game_window(window)
                window_missing_since = None
            except WindowDiscoveryError:
                now = self._time_provider()
                if window_missing_since is None:
                    window_missing_since = now
                if (now - window_missing_since) >= profile.healing_loop.max_window_missing_seconds:
                    terminated_early = True
                    termination_reason = "window-missing-timeout"
                    fail_safe_triggered = True
                    break
                self._sleep(min(0.10, profile.healing_loop.polling_interval_seconds))
                continue

            snapshot = self._calibration_service.build_snapshot(window, profile)
            runtime_cavebot_active = profile.hunt.enabled
            if is_cavebot_active is not None:
                runtime_cavebot_active = is_cavebot_active()

            last_cycle = self._healing_runtime.execute_cycle(
                window=window,
                snapshot=snapshot,
                life_hotkey=profile.hotkeys.heal_life,
                mana_hotkey=profile.hotkeys.heal_mana,
                haste_hotkey=profile.hotkeys.buff_haste,
                attack_hotkey=profile.hotkeys.attack_primary,
                secondary_attack_hotkey=profile.hotkeys.attack_secondary,
                haste_enabled=profile.buffs.haste_enabled,
                haste_interval_seconds=profile.buffs.haste_interval_seconds,
                haste_cooldown_seconds=profile.buffs.haste_cooldown_seconds,
                attack_enabled=profile.combat.attack_enabled,
                attack_cooldown_seconds=profile.combat.attack_cooldown_seconds,
                secondary_attack_enabled=profile.combat.secondary_attack_enabled,
                secondary_attack_cooldown_seconds=profile.combat.secondary_attack_cooldown_seconds,
                secondary_attack_after_primary_only=profile.combat.secondary_attack_after_primary_only,
                secondary_attack_combo_window_seconds=profile.combat.secondary_attack_combo_window_seconds,
                target_confirmation_cycles=profile.combat.target_confirmation_cycles,
                target_stability_window=profile.combat.target_stability_window,
                max_target_text_variants=profile.combat.max_target_text_variants,
                allowed_target_texts=profile.combat.allowed_target_texts,
                blocked_target_texts=profile.combat.blocked_target_texts,
                require_target_text_match=profile.combat.require_target_text_match,
                life_threshold_percent=profile.thresholds.life_percent,
                mana_threshold_percent=profile.thresholds.mana_percent,
                life_cooldown_seconds=profile.healing_loop.life_cooldown_seconds,
                mana_cooldown_seconds=profile.healing_loop.mana_cooldown_seconds,
                hunt_enabled=runtime_cavebot_active,
                hunt_loop_route=profile.hunt.loop_route,
                hunt_waypoint_interval_seconds=profile.hunt.waypoint_interval_seconds,
                hunt_move_up_hotkey=profile.hunt.move_up_hotkey,
                hunt_move_down_hotkey=profile.hunt.move_down_hotkey,
                hunt_move_left_hotkey=profile.hunt.move_left_hotkey,
                hunt_move_right_hotkey=profile.hunt.move_right_hotkey,
                hunt_waypoints=profile.hunt.waypoints,
                window_is_active=window.is_active,
                memory_enabled=profile.memory.enabled,
                memory_prefer_for_healing=profile.memory.prefer_for_healing,
                memory_prefer_for_target=profile.memory.prefer_for_target,
                memory_prefer_for_cavebot=profile.memory.prefer_for_cavebot,
                memory_process_name=profile.memory.process_name,
            )
            cycles_completed += 1
            cycle_index += 1

            if on_cycle is not None:
                on_cycle(last_cycle, cycles_completed)

            if last_cycle.life_reading is None and last_cycle.mana_reading is None:
                consecutive_ocr_failures += 1
            else:
                consecutive_ocr_failures = 0

            if consecutive_ocr_failures >= profile.healing_loop.max_consecutive_ocr_failures:
                terminated_early = True
                termination_reason = "ocr-failure-limit"
                fail_safe_triggered = True
                break

            if enforce_actions_per_minute_limit:
                now = self._time_provider()
                for _ in range(len(last_cycle.actions_executed)):
                    action_times.append(now)
                one_minute_ago = now - 60.0
                while action_times and action_times[0] < one_minute_ago:
                    action_times.popleft()

                if len(action_times) > profile.healing_loop.max_actions_per_minute:
                    terminated_early = True
                    termination_reason = "actions-per-minute-limit"
                    fail_safe_triggered = True
                    break

            if not continuous_mode and cycle_index >= cycle_limit and not runtime_cavebot_active:
                break

            cycle_elapsed = self._time_provider() - cycle_started_at
            remaining_sleep = profile.healing_loop.polling_interval_seconds - cycle_elapsed
            if remaining_sleep > 0:
                self._sleep(remaining_sleep)

        return HealingLoopResult(
            cycles_completed=cycles_completed,
            last_cycle=last_cycle,
            terminated_early=terminated_early,
            termination_reason=termination_reason,
            fail_safe_triggered=fail_safe_triggered,
        )

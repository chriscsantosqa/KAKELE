from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from kakelebot.core.calibration import CalibrationService
from kakelebot.core.config import ProfileSettings
from kakelebot.core.window import WindowService
from kakelebot.features.healing_runtime import HealingCycleResult, HealingRuntime


@dataclass(frozen=True, slots=True)
class HealingLoopResult:
    cycles_completed: int
    last_cycle: HealingCycleResult | None
    terminated_early: bool


class HealingLoopRunner:
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

    def run(
        self,
        profile: ProfileSettings,
        should_continue: Callable[[], bool] | None = None,
        is_paused: Callable[[], bool] | None = None,
    ) -> HealingLoopResult:
        last_cycle: HealingCycleResult | None = None
        cycles_completed = 0
        terminated_early = False

        cycle_limit = max(1, profile.healing_loop.bootstrap_cycle_limit)
        for cycle_index in range(cycle_limit):
            if should_continue is not None and not should_continue():
                terminated_early = True
                break

            while is_paused is not None and is_paused():
                if should_continue is not None and not should_continue():
                    terminated_early = True
                    break
                self._sleep(0.1)

            if terminated_early:
                break

            window = self._window_service.get_game_window()
            snapshot = self._calibration_service.build_snapshot(window, profile)

            last_cycle = self._healing_runtime.execute_cycle(
                snapshot=snapshot,
                life_hotkey=profile.hotkeys.heal_life,
                mana_hotkey=profile.hotkeys.heal_mana,
                life_threshold_percent=profile.thresholds.life_percent,
                mana_threshold_percent=profile.thresholds.mana_percent,
                life_cooldown_seconds=profile.healing_loop.life_cooldown_seconds,
                mana_cooldown_seconds=profile.healing_loop.mana_cooldown_seconds,
                window_is_active=window.is_active,
            )
            cycles_completed += 1

            if cycle_index < cycle_limit - 1:
                self._sleep(profile.healing_loop.polling_interval_seconds)

        return HealingLoopResult(
            cycles_completed=cycles_completed,
            last_cycle=last_cycle,
            terminated_early=terminated_early,
        )

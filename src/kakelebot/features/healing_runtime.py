from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.capture import CaptureService
from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.input import InputService, KeyAction
from kakelebot.core.vision import VisionService, BarReading
from kakelebot.features.healing import HealingDecision, HealingService


@dataclass(frozen=True, slots=True)
class HealingCycleResult:
    life_reading: BarReading | None
    mana_reading: BarReading | None
    decision: HealingDecision
    actions_executed: tuple[KeyAction, ...]


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

    def execute_cycle(
        self,
        snapshot: CalibrationSnapshot,
        life_hotkey: str,
        mana_hotkey: str,
        life_threshold_percent: int,
        mana_threshold_percent: int,
        window_is_active: bool,
    ) -> HealingCycleResult:
        life_image = self._capture.capture(snapshot.life_bar)
        mana_image = self._capture.capture(snapshot.mana_bar)

        life_reading = self._vision.read_bar_value(life_image)
        mana_reading = self._vision.read_bar_value(mana_image)

        decision = self._healing.evaluate(
            life=life_reading,
            mana=mana_reading,
            life_threshold_percent=life_threshold_percent,
            mana_threshold_percent=mana_threshold_percent,
        )

        executed_actions: list[KeyAction] = []
        if window_is_active:
            if decision.should_heal_life:
                action = KeyAction(key=life_hotkey, reason=decision.reason)
                self._input.execute(action)
                executed_actions.append(action)

            if decision.should_heal_mana:
                action = KeyAction(key=mana_hotkey, reason=decision.reason)
                self._input.execute(action)
                executed_actions.append(action)

        return HealingCycleResult(
            life_reading=life_reading,
            mana_reading=mana_reading,
            decision=decision,
            actions_executed=tuple(executed_actions),
        )

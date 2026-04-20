from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService
from kakelebot.core.config import HuntWaypoint
from kakelebot.core.input import InputService, KeyAction
from kakelebot.core.vision import BarReading, VisionService
from kakelebot.core.window import WindowInfo
from kakelebot.features.healing import HealingDecision, HealingService
from kakelebot.features.hunt_runtime import HuntCycleAction, HuntRuntime


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

        # 🔥 NÃO BLOQUEIA MAIS POR WINDOW INACTIVE
        whole_window_image = self._capture.capture_window(window)

        life_image = self._crop(window, whole_window_image, snapshot.life_bar)
        mana_image = self._crop(window, whole_window_image, snapshot.mana_bar)

        life = self._vision.read_bar_value(life_image)
        mana = self._vision.read_bar_value(mana_image)

        decision = self._healing.evaluate(
            life=life,
            mana=mana,
            life_threshold_percent=life_threshold_percent,
            mana_threshold_percent=mana_threshold_percent,
        )

        actions: list[KeyAction] = []
        suppressed: list[str] = []

        # --- TARGET ---
        target_img = self._crop(window, whole_window_image, snapshot.target_status)
        target_preview = self._vision.build_target_preview(target_img)

        has_target = target_preview.has_target
        target_text = target_preview.normalized_text

        self._recent_target_observations.append((has_target, target_text))

        target_confirmed = self._target_confirmed(target_confirmation_cycles)
        target_oscillating = self._target_oscillating(
            target_stability_window,
            max_target_text_variants,
        )

        # ✔️ CORREÇÃO: TARGET REAL
        valid_target = has_target and target_confirmed and not target_oscillating

        # --- HEAL ---
        if decision.should_heal_life:
            actions.append(KeyAction(life_hotkey, "heal-life"))

        if decision.should_heal_mana:
            actions.append(KeyAction(mana_hotkey, "heal-mana"))

        # --- HUNT ---
        hunt_status = "disabled"

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

        if actions:
            self._input.execute_many(actions, 0)

        return HealingCycleResult(
            life_reading=life,
            mana_reading=mana,
            decision=decision,
            actions_executed=tuple(actions),
            suppressed_actions=tuple(suppressed),
            haste_status="",
            attack_status="",
            secondary_attack_status="",
            hunt_status=hunt_status,
            has_target=has_target,
            target_confirmed=target_confirmed,
            target_oscillating=target_oscillating,
            target_reason="",
            target_text=target_text,
        )

    def _crop(self, window, img, region):
        return img.crop((
            region.left - window.left,
            region.top - window.top,
            region.left - window.left + region.width,
            region.top - window.top + region.height,
        ))

    def _target_confirmed(self, cycles: int) -> bool:
        if len(self._recent_target_observations) < cycles:
            return False
        return all(x[0] for x in list(self._recent_target_observations)[-cycles:])

    def _target_oscillating(self, window: int, max_variants: int) -> bool:
        if len(self._recent_target_observations) < window:
            return False

        recent = list(self._recent_target_observations)[-window:]
        flips = sum(
            1 for i in range(1, len(recent))
            if recent[i][0] != recent[i-1][0]
        )

        texts = {t for h, t in recent if h}

        return flips >= 2 or len(texts) > max_variants
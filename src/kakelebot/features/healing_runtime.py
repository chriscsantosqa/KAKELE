from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from kakelebot.core.calibration import CalibrationSnapshot
from kakelebot.core.capture import CaptureService
from kakelebot.core.memory import MemoryReadResult, MemoryService, PlayerState
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
    data_source: str
    memory_status: str
    player_position: tuple[int, int, int] | None
    memory_player_state: PlayerState | None


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
    ) -> None:
        self._capture = capture_service
        self._vision = vision_service
        self._healing = healing_service
        self._input = input_service
        self._memory = memory_service
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
        memory_enabled: bool,
        memory_prefer_for_healing: bool,
        memory_prefer_for_target: bool,
        memory_prefer_for_cavebot: bool,
        memory_process_name: str,
    ) -> HealingCycleResult:

        # 🔥 NÃO BLOQUEIA MAIS POR WINDOW INACTIVE
        whole_window_image = self._capture.capture_window(window)

        life_image = self._crop(window, whole_window_image, snapshot.life_bar)
        mana_image = self._crop(window, whole_window_image, snapshot.mana_bar)

        life = self._vision.read_bar_value(life_image)
        mana = self._vision.read_bar_value(mana_image)
        memory_result = self._read_memory_if_enabled(memory_enabled)
        memory_status = self._memory_status_text(memory_result, memory_enabled, memory_process_name)
        data_source = "vision"

        if (
            memory_prefer_for_healing
            and memory_result is not None
            and memory_result.available
            and memory_result.state is not None
        ):
            life = BarReading(
                current=memory_result.state.hp,
                maximum=memory_result.state.max_hp,
                source_text="memory:hp",
                confidence_ok=True,
            )
            mana = BarReading(
                current=memory_result.state.mp,
                maximum=memory_result.state.max_mp,
                source_text="memory:mp",
                confidence_ok=True,
            )
            data_source = "memory-heal"

        decision = self._healing.evaluate(
            life=life,
            mana=mana,
            life_threshold_percent=life_threshold_percent,
            mana_threshold_percent=mana_threshold_percent,
        )

        actions: list[KeyAction] = []
        suppressed: list[str] = []
        now = self._time_provider()

        # --- TARGET ---
        target_img = self._crop(window, whole_window_image, snapshot.target_status)
        target_preview = self._vision.build_target_preview(target_img)

        has_target = target_preview.has_target
        target_text = target_preview.normalized_text
        target_reason = "vision"

        if (
            memory_prefer_for_target
            and memory_result is not None
            and memory_result.available
            and memory_result.state is not None
        ):
            has_target = memory_result.state.has_target
            target_text = f"memory-target:{memory_result.state.target_id}"
            target_reason = "memory"
            data_source = "memory-target" if data_source == "vision" else "memory-hybrid"

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

        # --- BUFF / ATTACK ---
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
                attack_status = "no-target"
            else:
                attack_status = "cooldown"

        secondary_attack_status = "disabled"
        if secondary_attack_enabled:
            allowed_by_primary_rule = True
            if secondary_attack_after_primary_only:
                allowed_by_primary_rule = (
                    self._last_attack_at is not None
                    and (now - self._last_attack_at) <= secondary_attack_combo_window_seconds
                )

            if not valid_target:
                secondary_attack_status = "no-target"
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

        # --- HUNT ---
        hunt_status = "disabled"

        player_position: tuple[int, int, int] | None = None
        if memory_result is not None and memory_result.available and memory_result.state is not None:
            player_position = (
                memory_result.state.x,
                memory_result.state.y,
                memory_result.state.z,
            )

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
            has_target=has_target,
            target_confirmed=target_confirmed,
            target_oscillating=target_oscillating,
            target_reason=target_reason,
            target_text=target_text,
            data_source=data_source,
            memory_status=memory_status,
            player_position=player_position,
            memory_player_state=memory_result.state if memory_result is not None else None,
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

    def _read_memory_if_enabled(self, enabled: bool) -> MemoryReadResult | None:
        if not enabled or self._memory is None:
            return None
        return self._memory.try_get_player_state()

    @staticmethod
    def _memory_status_text(
        result: MemoryReadResult | None,
        enabled: bool,
        process_name: str,
    ) -> str:
        if not enabled:
            return "memory-disabled"
        if result is None:
            return "memory-service-unavailable"
        if result.available:
            return f"memory-ok:{process_name}"
        return f"memory-failed:{result.error or 'unknown'}"

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

from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.memory import MemoryReadResult
from kakelebot.core.vision import BarReading, TargetPreview


@dataclass(frozen=True, slots=True)
class VitalState:
    life: BarReading | None
    mana: BarReading | None
    data_source: str
    memory_status: str


@dataclass(frozen=True, slots=True)
class TargetState:
    has_target: bool
    target_text: str
    target_reason: str
    data_source: str


@dataclass(frozen=True, slots=True)
class NavigationState:
    player_position: tuple[int, int, int] | None
    data_source: str


@dataclass(frozen=True, slots=True)
class GameState:
    vitals: VitalState
    target: TargetState
    navigation: NavigationState
    memory_result: MemoryReadResult | None


class GameStateService:
    def build_state(
        self,
        *,
        life_reading: BarReading | None,
        mana_reading: BarReading | None,
        target_preview: TargetPreview,
        memory_result: MemoryReadResult | None,
        memory_enabled: bool,
        memory_prefer_for_healing: bool,
        memory_prefer_for_target: bool,
        memory_prefer_for_cavebot: bool,
        memory_process_name: str,
    ) -> GameState:
        memory_status = self._memory_status_text(memory_result, memory_enabled, memory_process_name)

        vitals = self._resolve_vitals(
            life_reading=life_reading,
            mana_reading=mana_reading,
            memory_result=memory_result,
            memory_prefer_for_healing=memory_prefer_for_healing,
            memory_status=memory_status,
        )
        target = self._resolve_target(
            target_preview=target_preview,
            memory_result=memory_result,
            memory_prefer_for_target=memory_prefer_for_target,
            inherited_data_source=vitals.data_source,
        )
        navigation = self._resolve_navigation(
            memory_result=memory_result,
            memory_prefer_for_cavebot=memory_prefer_for_cavebot,
            inherited_data_source=target.data_source,
        )

        return GameState(
            vitals=vitals,
            target=target,
            navigation=navigation,
            memory_result=memory_result,
        )

    def _resolve_vitals(
        self,
        *,
        life_reading: BarReading | None,
        mana_reading: BarReading | None,
        memory_result: MemoryReadResult | None,
        memory_prefer_for_healing: bool,
        memory_status: str,
    ) -> VitalState:
        if (
            memory_prefer_for_healing
            and memory_result is not None
            and memory_result.available
            and memory_result.state is not None
        ):
            return VitalState(
                life=BarReading(
                    current=memory_result.state.hp,
                    maximum=memory_result.state.max_hp,
                    source_text="memory:hp",
                    confidence_ok=True,
                ),
                mana=BarReading(
                    current=memory_result.state.mp,
                    maximum=memory_result.state.max_mp,
                    source_text="memory:mp",
                    confidence_ok=True,
                ),
                data_source="memory-heal",
                memory_status=memory_status,
            )

        return VitalState(
            life=life_reading,
            mana=mana_reading,
            data_source="vision",
            memory_status=memory_status,
        )

    def _resolve_target(
        self,
        *,
        target_preview: TargetPreview,
        memory_result: MemoryReadResult | None,
        memory_prefer_for_target: bool,
        inherited_data_source: str,
    ) -> TargetState:
        if (
            memory_prefer_for_target
            and memory_result is not None
            and memory_result.available
            and memory_result.state is not None
        ):
            return TargetState(
                has_target=memory_result.state.has_target,
                target_text=f"memory-target:{memory_result.state.target_id}",
                target_reason="memory",
                data_source="memory-target" if inherited_data_source == "vision" else "memory-hybrid",
            )

        return TargetState(
            has_target=target_preview.has_target,
            target_text=target_preview.normalized_text,
            target_reason="vision",
            data_source=inherited_data_source,
        )

    def _resolve_navigation(
        self,
        *,
        memory_result: MemoryReadResult | None,
        memory_prefer_for_cavebot: bool,
        inherited_data_source: str,
    ) -> NavigationState:
        if (
            memory_prefer_for_cavebot
            and memory_result is not None
            and memory_result.available
            and memory_result.state is not None
        ):
            return NavigationState(
                player_position=(
                    memory_result.state.x,
                    memory_result.state.y,
                    memory_result.state.z,
                ),
                data_source="memory-cavebot" if inherited_data_source == "vision" else "memory-hybrid",
            )

        return NavigationState(
            player_position=None,
            data_source=inherited_data_source,
        )

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

from __future__ import annotations

from dataclasses import dataclass

from kakelebot.core.config import MemoryAddressSettings, MemorySettings
from kakelebot.core.memory_factory import build_memory_service
from kakelebot.core.memory_validator import MemorySnapshotValidator


@dataclass(frozen=True, slots=True)
class MemoryFieldTestResult:
    field_name: str
    success: bool
    value: int | None
    message: str


class MemoryFieldTester:
    def __init__(self, validator: MemorySnapshotValidator | None = None) -> None:
        self._validator = validator or MemorySnapshotValidator()

    def test_field(
        self,
        *,
        memory_settings: MemorySettings,
        field_name: str,
    ) -> MemoryFieldTestResult:
        if not memory_settings.enabled:
            return MemoryFieldTestResult(
                field_name=field_name,
                success=False,
                value=None,
                message="memory is disabled",
            )

        memory_service = build_memory_service(memory_settings)
        if memory_service is None:
            return MemoryFieldTestResult(
                field_name=field_name,
                success=False,
                value=None,
                message="memory service unavailable",
            )

        result = memory_service.try_get_player_state()
        if not result.available or result.state is None:
            return MemoryFieldTestResult(
                field_name=field_name,
                success=False,
                value=None,
                message=result.error or "memory unavailable",
            )

        value = self._extract_field_value(result.state, field_name)
        if value is None:
            return MemoryFieldTestResult(
                field_name=field_name,
                success=False,
                value=None,
                message="unsupported field",
            )

        validation = self._validator.validate(
            self._build_validation_payload(result.state),
            required_fields=self._required_fields_for(field_name),
        )
        if not validation.is_valid:
            return MemoryFieldTestResult(
                field_name=field_name,
                success=False,
                value=value,
                message="; ".join(validation.reasons),
            )

        return MemoryFieldTestResult(
            field_name=field_name,
            success=True,
            value=value,
            message="ok",
        )

    @staticmethod
    def _extract_field_value(state, field_name: str) -> int | None:
        normalized = field_name.strip().lower()
        mapping = {
            "hp": state.hp,
            "max_hp": state.max_hp,
            "mp": state.mp,
            "max_mp": state.max_mp,
            "x": state.x,
            "y": state.y,
            "z": state.z,
            "has_target": int(state.has_target),
            "target_id": state.target_id,
            "level": state.level,
            "exp": state.exp,
        }
        return mapping.get(normalized)

    @staticmethod
    def _required_fields_for(field_name: str) -> set[str]:
        normalized = field_name.strip().lower()
        mapping = {
            "hp": {"hp", "max_hp"},
            "max_hp": {"hp", "max_hp"},
            "mp": {"mp", "max_mp"},
            "max_mp": {"mp", "max_mp"},
            "x": {"x"},
            "y": {"y"},
            "z": {"z"},
            "has_target": {"has_target", "target_id"},
            "target_id": {"has_target", "target_id"},
            "level": set(),
            "exp": set(),
        }
        return mapping.get(normalized, set())

    @staticmethod
    def _build_validation_payload(state) -> dict[str, int]:
        return {
            "hp": state.hp,
            "max_hp": state.max_hp,
            "mp": state.mp,
            "max_mp": state.max_mp,
            "x": state.x,
            "y": state.y,
            "z": state.z,
            "has_target": int(state.has_target),
            "target_id": state.target_id,
            "level": state.level,
            "exp": state.exp,
        }

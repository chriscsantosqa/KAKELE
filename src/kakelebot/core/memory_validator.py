from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemorySnapshotValidation:
    is_valid: bool
    reasons: tuple[str, ...]


class MemorySnapshotValidator:
    _MAX_REASONABLE_COORDINATE = 1_000_000

    def validate(self, data: dict[str, int], *, required_fields: set[str] | None = None) -> MemorySnapshotValidation:
        reasons: list[str] = []
        required = required_fields or {
            "hp",
            "max_hp",
            "mp",
            "max_mp",
            "x",
            "y",
            "z",
            "has_target",
            "target_id",
        }

        hp = int(data.get("hp", 0))
        max_hp = int(data.get("max_hp", 0))
        mp = int(data.get("mp", 0))
        max_mp = int(data.get("max_mp", 0))
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        z = int(data.get("z", 0))
        has_target = int(data.get("has_target", 0))
        target_id = int(data.get("target_id", 0))

        if {"hp", "max_hp"} & required:
            if max_hp <= 0:
                reasons.append("max_hp must be greater than zero")
            if hp < 0:
                reasons.append("hp must be non-negative")
            if max_hp > 0 and hp > max_hp:
                reasons.append("hp cannot be greater than max_hp")

        if {"mp", "max_mp"} & required:
            if max_mp <= 0:
                reasons.append("max_mp must be greater than zero")
            if mp < 0:
                reasons.append("mp must be non-negative")
            if max_mp > 0 and mp > max_mp:
                reasons.append("mp cannot be greater than max_mp")

        for name, value in (("x", x), ("y", y), ("z", z)):
            if name in required and abs(value) > self._MAX_REASONABLE_COORDINATE:
                reasons.append(f"{name} is outside the reasonable range")

        if "has_target" in required or "target_id" in required:
            if has_target not in (0, 1):
                reasons.append("has_target must be 0 or 1")
            if has_target == 0 and target_id < 0:
                reasons.append("target_id must be non-negative when there is no target")
            if has_target == 1 and target_id <= 0:
                reasons.append("target_id must be positive when has_target is enabled")

        return MemorySnapshotValidation(
            is_valid=not reasons,
            reasons=tuple(reasons),
        )

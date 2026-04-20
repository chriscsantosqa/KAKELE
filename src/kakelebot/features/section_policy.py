from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouteSectionPolicy:
    section: str
    allow_primary_attack: bool
    allow_secondary_attack: bool
    pause_hunt_during_target: bool


class SectionPolicyService:
    def resolve(self, section: str) -> RouteSectionPolicy:
        normalized = section.strip().lower() or "hunt"
        if normalized == "refill":
            return RouteSectionPolicy(
                section="refill",
                allow_primary_attack=False,
                allow_secondary_attack=False,
                pause_hunt_during_target=False,
            )
        if normalized == "escape":
            return RouteSectionPolicy(
                section="escape",
                allow_primary_attack=False,
                allow_secondary_attack=False,
                pause_hunt_during_target=False,
            )
        return RouteSectionPolicy(
            section=normalized,
            allow_primary_attack=True,
            allow_secondary_attack=True,
            pause_hunt_during_target=True,
        )

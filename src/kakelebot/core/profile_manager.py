from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from kakelebot.core.config import AppSettings, ProfileSettings, load_profile, save_profile


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    name: str
    path: Path


@dataclass(frozen=True, slots=True)
class ProfilePreset:
    key: str
    label: str
    description: str
    expected_width: int
    expected_height: int
    ui_scale: float


class ProfileManager:
    PRESETS: tuple[ProfilePreset, ...] = (
        ProfilePreset(
            key="heal_safe",
            label="Heal Safe",
            description="Foco em sustain, sem ataque ofensivo ativo.",
            expected_width=1366,
            expected_height=768,
            ui_scale=1.0,
        ),
        ProfilePreset(
            key="hunt_basic",
            label="Hunt Basic",
            description="Ataque primario estavel com haste ligada.",
            expected_width=1366,
            expected_height=768,
            ui_scale=1.0,
        ),
        ProfilePreset(
            key="combo_aggressive",
            label="Combo Aggressive",
            description="Ataque primario e secundario com janela de combo.",
            expected_width=1920,
            expected_height=1080,
            ui_scale=1.0,
        ),
    )

    def __init__(
        self,
        profiles_dir: Path,
        settings: AppSettings,
        settings_path: Path,
    ) -> None:
        self._profiles_dir = profiles_dir
        self._settings = settings
        self._settings_path = settings_path
        self._profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> list[ProfileRecord]:
        records = [
            ProfileRecord(name=path.stem, path=path)
            for path in sorted(self._profiles_dir.glob("*.json"))
        ]
        return records

    def list_presets(self) -> tuple[ProfilePreset, ...]:
        return self.PRESETS

    def load(self, profile_name: str) -> tuple[ProfileSettings, Path]:
        normalized_name = self.normalize_name(profile_name)
        profile_path = self._profiles_dir / f"{normalized_name}.json"
        profile = load_profile(profile_path)
        self.set_active_profile(profile.name)
        return profile, profile_path

    def save_current(self, profile: ProfileSettings, profile_path: Path) -> None:
        save_profile(profile_path, profile)
        self.set_active_profile(profile.name)

    def save_as(self, source_profile: ProfileSettings, new_profile_name: str) -> tuple[ProfileSettings, Path]:
        normalized_name = self.normalize_name(new_profile_name)
        profile_path = self._profiles_dir / f"{normalized_name}.json"
        new_profile = copy.deepcopy(source_profile)
        new_profile.name = normalized_name
        save_profile(profile_path, new_profile)
        self.set_active_profile(normalized_name)
        return new_profile, profile_path

    def save_as_preset(
        self,
        source_profile: ProfileSettings,
        preset_key: str,
        new_profile_name: str,
    ) -> tuple[ProfileSettings, Path]:
        normalized_name = self.normalize_name(new_profile_name)
        profile_path = self._profiles_dir / f"{normalized_name}.json"
        new_profile = copy.deepcopy(source_profile)
        new_profile.name = normalized_name
        self._apply_preset(new_profile, preset_key)
        save_profile(profile_path, new_profile)
        self.set_active_profile(normalized_name)
        return new_profile, profile_path

    def apply_preset_to_current(self, profile: ProfileSettings, preset_key: str, profile_path: Path) -> None:
        self._apply_preset(profile, preset_key)
        save_profile(profile_path, profile)
        self.set_active_profile(profile.name)

    def delete(self, profile_name: str) -> str | None:
        normalized_name = self.normalize_name(profile_name)
        records = self.list_profiles()
        if len(records) <= 1:
            raise ValueError("At least one profile must remain.")

        profile_path = self._profiles_dir / f"{normalized_name}.json"
        if not profile_path.exists():
            raise ValueError("Profile does not exist.")

        profile_path.unlink()

        active_profile = self._settings.runtime.active_profile
        if active_profile == normalized_name:
            remaining = [record.name for record in self.list_profiles() if record.name != normalized_name]
            fallback = remaining[0] if remaining else None
            if fallback is not None:
                self.set_active_profile(fallback)
            return fallback

        return active_profile

    def set_active_profile(self, profile_name: str) -> None:
        normalized_name = self.normalize_name(profile_name)
        self._settings.runtime.active_profile = normalized_name
        self._settings.save(self._settings_path)

    def _apply_preset(self, profile: ProfileSettings, preset_key: str) -> None:
        normalized_key = preset_key.strip().lower()
        if normalized_key == "heal_safe":
            self._apply_heal_safe(profile)
            return
        if normalized_key == "hunt_basic":
            self._apply_hunt_basic(profile)
            return
        if normalized_key == "combo_aggressive":
            self._apply_combo_aggressive(profile)
            return
        raise ValueError("Unknown preset.")

    @classmethod
    def _preset_by_key(cls, preset_key: str) -> ProfilePreset:
        normalized_key = preset_key.strip().lower()
        for preset in cls.PRESETS:
            if preset.key == normalized_key:
                return preset
        raise ValueError("Unknown preset.")

    @classmethod
    def _apply_resolution_context(cls, profile: ProfileSettings, preset_key: str) -> None:
        preset = cls._preset_by_key(preset_key)
        profile.resolution_width = preset.expected_width
        profile.resolution_height = preset.expected_height
        profile.ui_scale = preset.ui_scale

    @classmethod
    def _apply_heal_safe(cls, profile: ProfileSettings) -> None:
        cls._apply_resolution_context(profile, "heal_safe")

        profile.buffs.haste_enabled = False
        profile.buffs.haste_interval_seconds = 30.0
        profile.buffs.haste_cooldown_seconds = 1.0

        profile.combat.attack_enabled = False
        profile.combat.attack_cooldown_seconds = 0.5
        profile.combat.secondary_attack_enabled = False
        profile.combat.secondary_attack_cooldown_seconds = 2.0
        profile.combat.secondary_attack_after_primary_only = True
        profile.combat.secondary_attack_combo_window_seconds = 1.0
        profile.combat.target_confirmation_cycles = 3
        profile.combat.target_stability_window = 5
        profile.combat.max_target_text_variants = 1

        profile.healing_loop.continuous_mode = True
        profile.healing_loop.polling_interval_seconds = 0.35

    @classmethod
    def _apply_hunt_basic(cls, profile: ProfileSettings) -> None:
        cls._apply_resolution_context(profile, "hunt_basic")

        profile.buffs.haste_enabled = True
        profile.buffs.haste_interval_seconds = 20.0
        profile.buffs.haste_cooldown_seconds = 1.0

        profile.combat.attack_enabled = True
        profile.combat.attack_cooldown_seconds = 0.35
        profile.combat.secondary_attack_enabled = False
        profile.combat.secondary_attack_cooldown_seconds = 2.0
        profile.combat.secondary_attack_after_primary_only = True
        profile.combat.secondary_attack_combo_window_seconds = 1.0
        profile.combat.target_confirmation_cycles = 2
        profile.combat.target_stability_window = 4
        profile.combat.max_target_text_variants = 2

        profile.healing_loop.continuous_mode = True
        profile.healing_loop.polling_interval_seconds = 0.25

    @classmethod
    def _apply_combo_aggressive(cls, profile: ProfileSettings) -> None:
        cls._apply_resolution_context(profile, "combo_aggressive")

        profile.buffs.haste_enabled = True
        profile.buffs.haste_interval_seconds = 18.0
        profile.buffs.haste_cooldown_seconds = 1.0

        profile.combat.attack_enabled = True
        profile.combat.attack_cooldown_seconds = 0.25
        profile.combat.secondary_attack_enabled = True
        profile.combat.secondary_attack_cooldown_seconds = 1.2
        profile.combat.secondary_attack_after_primary_only = True
        profile.combat.secondary_attack_combo_window_seconds = 0.8
        profile.combat.target_confirmation_cycles = 2
        profile.combat.target_stability_window = 4
        profile.combat.max_target_text_variants = 2

        profile.healing_loop.continuous_mode = True
        profile.healing_loop.polling_interval_seconds = 0.2

    @staticmethod
    def normalize_name(raw_name: str) -> str:
        name = raw_name.strip()
        if not name:
            raise ValueError("Profile name cannot be empty.")
        if name.endswith(".json"):
            name = name[:-5]
        invalid_characters = set('\\/:*?"<>|')
        if any(char in invalid_characters for char in name):
            raise ValueError("Profile name contains invalid filesystem characters.")
        return name

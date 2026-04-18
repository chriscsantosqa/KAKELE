from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from kakelebot.core.config import AppSettings, ProfileSettings, load_profile, save_profile


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    name: str
    path: Path


class ProfileManager:
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

    def set_active_profile(self, profile_name: str) -> None:
        normalized_name = self.normalize_name(profile_name)
        self._settings.runtime.active_profile = normalized_name
        self._settings.save(self._settings_path)

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

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


DEFAULT_PROFILE_NAME = "default"


@dataclass(slots=True)
class RuntimeSettings:
    debug: bool = True
    log_level: str = "INFO"
    active_profile: str = DEFAULT_PROFILE_NAME


@dataclass(slots=True)
class HotkeysSettings:
    start_stop: str = "F8"
    pause_resume: str = "F9"
    heal_life: str = "F1"
    heal_mana: str = "F2"
    buff_haste: str = "F3"


@dataclass(slots=True)
class ThresholdSettings:
    life_percent: int = 60
    mana_percent: int = 40
    haste_interval_seconds: int = 30


@dataclass(slots=True)
class ProfileSettings:
    name: str = DEFAULT_PROFILE_NAME
    resolution_width: int = 0
    resolution_height: int = 0
    ui_scale: float = 1.0
    hotkeys: HotkeysSettings = field(default_factory=HotkeysSettings)
    thresholds: ThresholdSettings = field(default_factory=ThresholdSettings)


@dataclass(slots=True)
class AppSettings:
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        if not path.exists():
            settings = cls()
            settings.save(path)
            return settings

        raw = json.loads(path.read_text(encoding="utf-8"))
        runtime = RuntimeSettings(**raw.get("runtime", {}))
        return cls(runtime=runtime)


def save_profile(path: Path, profile: ProfileSettings) -> None:
    path.write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")


def load_profile(path: Path) -> ProfileSettings:
    if not path.exists():
        profile = ProfileSettings()
        save_profile(path, profile)
        return profile

    raw = json.loads(path.read_text(encoding="utf-8"))
    hotkeys = HotkeysSettings(**raw.get("hotkeys", {}))
    thresholds = ThresholdSettings(**raw.get("thresholds", {}))

    return ProfileSettings(
        name=raw.get("name", DEFAULT_PROFILE_NAME),
        resolution_width=raw.get("resolution_width", 0),
        resolution_height=raw.get("resolution_height", 0),
        ui_scale=raw.get("ui_scale", 1.0),
        hotkeys=hotkeys,
        thresholds=thresholds,
    )

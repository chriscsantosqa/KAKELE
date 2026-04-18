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
class NormalizedRegionSettings:
    left_ratio: float
    top_ratio: float
    width_ratio: float
    height_ratio: float


@dataclass(slots=True)
class RoiSettings:
    life_bar: NormalizedRegionSettings = field(
        default_factory=lambda: NormalizedRegionSettings(0.078, 0.088, 0.210, 0.065)
    )
    mana_bar: NormalizedRegionSettings = field(
        default_factory=lambda: NormalizedRegionSettings(0.078, 0.157, 0.210, 0.065)
    )
    target_status: NormalizedRegionSettings = field(
        default_factory=lambda: NormalizedRegionSettings(0.150, 0.245, 0.110, 0.050)
    )
    minimap: NormalizedRegionSettings = field(
        default_factory=lambda: NormalizedRegionSettings(0.640, 0.045, 0.310, 0.290)
    )


@dataclass(slots=True)
class ProfileSettings:
    name: str = DEFAULT_PROFILE_NAME
    resolution_width: int = 0
    resolution_height: int = 0
    ui_scale: float = 1.0
    hotkeys: HotkeysSettings = field(default_factory=HotkeysSettings)
    thresholds: ThresholdSettings = field(default_factory=ThresholdSettings)
    rois: RoiSettings = field(default_factory=RoiSettings)


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


def _load_normalized_region(raw: dict, fallback: NormalizedRegionSettings) -> NormalizedRegionSettings:
    return NormalizedRegionSettings(
        left_ratio=raw.get("left_ratio", fallback.left_ratio),
        top_ratio=raw.get("top_ratio", fallback.top_ratio),
        width_ratio=raw.get("width_ratio", fallback.width_ratio),
        height_ratio=raw.get("height_ratio", fallback.height_ratio),
    )


def _load_rois(raw: dict) -> RoiSettings:
    defaults = RoiSettings()
    return RoiSettings(
        life_bar=_load_normalized_region(raw.get("life_bar", {}), defaults.life_bar),
        mana_bar=_load_normalized_region(raw.get("mana_bar", {}), defaults.mana_bar),
        target_status=_load_normalized_region(raw.get("target_status", {}), defaults.target_status),
        minimap=_load_normalized_region(raw.get("minimap", {}), defaults.minimap),
    )


def load_profile(path: Path) -> ProfileSettings:
    if not path.exists():
        profile = ProfileSettings()
        save_profile(path, profile)
        return profile

    raw = json.loads(path.read_text(encoding="utf-8"))
    hotkeys = HotkeysSettings(**raw.get("hotkeys", {}))
    thresholds = ThresholdSettings(**raw.get("thresholds", {}))
    rois = _load_rois(raw.get("rois", {}))

    return ProfileSettings(
        name=raw.get("name", DEFAULT_PROFILE_NAME),
        resolution_width=raw.get("resolution_width", 0),
        resolution_height=raw.get("resolution_height", 0),
        ui_scale=raw.get("ui_scale", 1.0),
        hotkeys=hotkeys,
        thresholds=thresholds,
        rois=rois,
    )

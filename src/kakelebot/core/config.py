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
class AiVisionSettings:
    enabled: bool = False
    provider: str = "openai_compatible"
    base_url: str = "https://api.openai.com"
    endpoint_path: str = "/v1/chat/completions"
    model: str = ""
    api_key_env_var: str = "OPENAI_API_KEY"
    timeout_seconds: float = 45.0
    allow_auto_apply_roi_suggestions: bool = False


@dataclass(slots=True)
class HotkeysSettings:
    start_stop: str = "F8"
    pause_resume: str = "F9"
    heal_life: str = "F1"
    heal_mana: str = "F2"
    buff_haste: str = "F3"
    attack_primary: str = "F4"
    attack_secondary: str = "F5"


@dataclass(slots=True)
class ThresholdSettings:
    life_percent: int = 60
    mana_percent: int = 40


@dataclass(slots=True)
class BuffSettings:
    haste_enabled: bool = False
    haste_interval_seconds: float = 30.0
    haste_cooldown_seconds: float = 1.0


@dataclass(slots=True)
class CombatSettings:
    attack_enabled: bool = False
    attack_cooldown_seconds: float = 0.5
    secondary_attack_enabled: bool = False
    secondary_attack_cooldown_seconds: float = 2.0
    secondary_attack_after_primary_only: bool = True
    secondary_attack_combo_window_seconds: float = 1.0
    target_confirmation_cycles: int = 2
    target_stability_window: int = 4
    max_target_text_variants: int = 2


@dataclass(slots=True)
class HealingLoopSettings:
    polling_interval_seconds: float = 0.5
    life_cooldown_seconds: float = 1.0
    mana_cooldown_seconds: float = 1.0
    bootstrap_cycle_limit: int = 3
    continuous_mode: bool = False
    max_actions_per_minute: int = 30
    max_consecutive_ocr_failures: int = 10
    max_window_missing_seconds: float = 15.0


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
    buffs: BuffSettings = field(default_factory=BuffSettings)
    combat: CombatSettings = field(default_factory=CombatSettings)
    healing_loop: HealingLoopSettings = field(default_factory=HealingLoopSettings)
    rois: RoiSettings = field(default_factory=RoiSettings)


@dataclass(slots=True)
class AppSettings:
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    ai_vision: AiVisionSettings = field(default_factory=AiVisionSettings)

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
        ai_vision = AiVisionSettings(**raw.get("ai_vision", {}))
        return cls(runtime=runtime, ai_vision=ai_vision)


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


def _load_buffs(raw: dict) -> BuffSettings:
    defaults = BuffSettings()
    return BuffSettings(
        haste_enabled=raw.get("haste_enabled", defaults.haste_enabled),
        haste_interval_seconds=raw.get("haste_interval_seconds", defaults.haste_interval_seconds),
        haste_cooldown_seconds=raw.get("haste_cooldown_seconds", defaults.haste_cooldown_seconds),
    )


def _load_combat(raw: dict) -> CombatSettings:
    defaults = CombatSettings()
    return CombatSettings(
        attack_enabled=raw.get("attack_enabled", defaults.attack_enabled),
        attack_cooldown_seconds=raw.get("attack_cooldown_seconds", defaults.attack_cooldown_seconds),
        secondary_attack_enabled=raw.get(
            "secondary_attack_enabled", defaults.secondary_attack_enabled
        ),
        secondary_attack_cooldown_seconds=raw.get(
            "secondary_attack_cooldown_seconds", defaults.secondary_attack_cooldown_seconds
        ),
        secondary_attack_after_primary_only=raw.get(
            "secondary_attack_after_primary_only", defaults.secondary_attack_after_primary_only
        ),
        secondary_attack_combo_window_seconds=raw.get(
            "secondary_attack_combo_window_seconds", defaults.secondary_attack_combo_window_seconds
        ),
        target_confirmation_cycles=raw.get(
            "target_confirmation_cycles", defaults.target_confirmation_cycles
        ),
        target_stability_window=raw.get(
            "target_stability_window", defaults.target_stability_window
        ),
        max_target_text_variants=raw.get(
            "max_target_text_variants", defaults.max_target_text_variants
        ),
    )


def _load_healing_loop(raw: dict) -> HealingLoopSettings:
    defaults = HealingLoopSettings()
    return HealingLoopSettings(
        polling_interval_seconds=raw.get(
            "polling_interval_seconds", defaults.polling_interval_seconds
        ),
        life_cooldown_seconds=raw.get(
            "life_cooldown_seconds", defaults.life_cooldown_seconds
        ),
        mana_cooldown_seconds=raw.get(
            "mana_cooldown_seconds", defaults.mana_cooldown_seconds
        ),
        bootstrap_cycle_limit=raw.get(
            "bootstrap_cycle_limit", defaults.bootstrap_cycle_limit
        ),
        continuous_mode=raw.get(
            "continuous_mode", defaults.continuous_mode
        ),
        max_actions_per_minute=raw.get(
            "max_actions_per_minute", defaults.max_actions_per_minute
        ),
        max_consecutive_ocr_failures=raw.get(
            "max_consecutive_ocr_failures", defaults.max_consecutive_ocr_failures
        ),
        max_window_missing_seconds=raw.get(
            "max_window_missing_seconds", defaults.max_window_missing_seconds
        ),
    )


def load_profile(path: Path) -> ProfileSettings:
    if not path.exists():
        profile = ProfileSettings()
        save_profile(path, profile)
        return profile

    raw = json.loads(path.read_text(encoding="utf-8"))
    hotkeys = HotkeysSettings(**raw.get("hotkeys", {}))
    thresholds = ThresholdSettings(**raw.get("thresholds", {}))
    buffs = _load_buffs(raw.get("buffs", {}))
    combat = _load_combat(raw.get("combat", {}))
    healing_loop = _load_healing_loop(raw.get("healing_loop", {}))
    rois = _load_rois(raw.get("rois", {}))

    return ProfileSettings(
        name=raw.get("name", DEFAULT_PROFILE_NAME),
        resolution_width=raw.get("resolution_width", 0),
        resolution_height=raw.get("resolution_height", 0),
        ui_scale=raw.get("ui_scale", 1.0),
        hotkeys=hotkeys,
        thresholds=thresholds,
        buffs=buffs,
        combat=combat,
        healing_loop=healing_loop,
        rois=rois,
    )

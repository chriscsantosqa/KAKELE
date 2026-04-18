from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kakelebot.core.config import AppSettings, ProfileSettings, load_profile
from kakelebot.core.logging_config import configure_logging
from kakelebot.core.paths import AppPaths


@dataclass(slots=True)
class RuntimeContext:
    paths: AppPaths
    settings: AppSettings
    profile: ProfileSettings
    log_file: Path


class RuntimeBootstrap:
    def __init__(self, home: Path | None = None) -> None:
        self._home = home

    def initialize(self) -> RuntimeContext:
        paths = AppPaths.build(self._home)
        paths.create_directories()

        settings_path = paths.root / "settings.json"
        settings = AppSettings.load(settings_path)

        profile_path = paths.profiles / f"{settings.runtime.active_profile}.json"
        profile = load_profile(profile_path)

        log_file = configure_logging(paths.logs, settings.runtime.log_level)

        return RuntimeContext(
            paths=paths,
            settings=settings,
            profile=profile,
            log_file=log_file,
        )

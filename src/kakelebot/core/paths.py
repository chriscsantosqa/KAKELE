from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_FOLDER_NAME = ".kakelebot"


@dataclass(frozen=True, slots=True)
class AppPaths:
    root: Path
    logs: Path
    profiles: Path
    cache: Path

    @classmethod
    def build(cls, home: Path | None = None) -> "AppPaths":
        base_home = home or Path.home()
        root = base_home / APP_FOLDER_NAME
        return cls(
            root=root,
            logs=root / "logs",
            profiles=root / "profiles",
            cache=root / "cache",
        )

    def create_directories(self) -> None:
        for directory in (self.root, self.logs, self.profiles, self.cache):
            directory.mkdir(parents=True, exist_ok=True)

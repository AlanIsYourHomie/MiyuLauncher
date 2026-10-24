from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "MiyuLauncher"


@dataclass(frozen=True)
class LauncherPaths:
    root: Path
    instance: Path
    runtime: Path
    cache: Path
    downloads: Path
    logs: Path

    def create(self) -> None:
        for path in (
            self.root,
            self.instance,
            self.runtime,
            self.cache,
            self.downloads,
            self.logs,
        ):
            path.mkdir(parents=True, exist_ok=True)


def get_launcher_paths() -> LauncherPaths:
    """Return the directories managed by MiyuLauncher for the current user."""
    local_app_data = os.getenv("LOCALAPPDATA")

    if local_app_data:
        root = Path(local_app_data) / APP_NAME
    else:
        root = Path.home() / f".{APP_NAME.lower()}"

    return LauncherPaths(
        root=root,
        instance=root / "instance",
        runtime=root / "runtime",
        cache=root / "cache",
        downloads=root / "downloads",
        logs=root / "logs",
    )

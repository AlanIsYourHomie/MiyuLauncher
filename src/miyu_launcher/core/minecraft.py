from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MinecraftVersion:
    version_id: str
    directory: Path
    json_file: Path
    jar_file: Path | None
    version_type: str | None
    main_class: str | None
    inherits_from: str | None
    client_download_url: str | None
    client_download_sha1: str | None
    asset_index_id: str | None
    java_major_version: int | None
    libraries_count: int
    has_modern_arguments: bool
    has_legacy_arguments: bool


@dataclass(frozen=True)
class MinecraftInstallation:
    root: Path
    source: str
    versions: tuple[MinecraftVersion, ...]


def _default_minecraft_roots() -> list[tuple[Path, str]]:
    roots: list[tuple[Path, str]] = []

    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append((Path(appdata) / ".minecraft", "Official launcher / APPDATA"))

    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        profile = Path(userprofile)
        roots.extend(
            [
                (profile / "AppData" / "Roaming" / ".minecraft", "User profile"),
                (profile / "curseforge" / "minecraft" / "Instances", "CurseForge instances"),
                (profile / "AppData" / "Roaming" / "PrismLauncher" / "instances", "Prism Launcher instances"),
            ]
        )

    return roots


def _read_version(version_dir: Path) -> MinecraftVersion | None:
    version_id = version_dir.name
    json_file = version_dir / f"{version_id}.json"

    if not json_file.is_file():
        return None

    try:
        data = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    jar_file = version_dir / f"{version_id}.jar"

    downloads = data.get("downloads") if isinstance(data.get("downloads"), dict) else {}
    client_download = downloads.get("client") if isinstance(downloads.get("client"), dict) else {}

    asset_index = data.get("assetIndex") if isinstance(data.get("assetIndex"), dict) else {}
    java_version = data.get("javaVersion") if isinstance(data.get("javaVersion"), dict) else {}
    libraries = data.get("libraries") if isinstance(data.get("libraries"), list) else []
    arguments = data.get("arguments") if isinstance(data.get("arguments"), dict) else None

    java_major = java_version.get("majorVersion")
    if not isinstance(java_major, int):
        java_major = None

    return MinecraftVersion(
        version_id=str(data.get("id") or version_id),
        directory=version_dir,
        json_file=json_file,
        jar_file=jar_file if jar_file.is_file() else None,
        version_type=data.get("type"),
        main_class=data.get("mainClass"),
        inherits_from=data.get("inheritsFrom"),
        client_download_url=client_download.get("url") if isinstance(client_download.get("url"), str) else None,
        client_download_sha1=client_download.get("sha1") if isinstance(client_download.get("sha1"), str) else None,
        asset_index_id=asset_index.get("id") if isinstance(asset_index.get("id"), str) else None,
        java_major_version=java_major,
        libraries_count=len(libraries),
        has_modern_arguments=arguments is not None,
        has_legacy_arguments=isinstance(data.get("minecraftArguments"), str),
    )


def _find_versions_in_standard_root(root: Path) -> tuple[MinecraftVersion, ...]:
    versions_dir = root / "versions"
    if not versions_dir.is_dir():
        return ()

    versions: list[MinecraftVersion] = []

    for version_dir in versions_dir.iterdir():
        if not version_dir.is_dir():
            continue

        version = _read_version(version_dir)
        if version is not None:
            versions.append(version)

    return tuple(sorted(versions, key=lambda item: item.version_id.lower()))


def _looks_like_standard_minecraft_root(root: Path) -> bool:
    return (root / "versions").is_dir() or (root / "assets").is_dir() or (root / "libraries").is_dir()


def find_minecraft_installations() -> list[MinecraftInstallation]:
    installations: list[MinecraftInstallation] = []
    seen: set[str] = set()

    for root, source in _default_minecraft_roots():
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root

        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)

        if not resolved.exists():
            continue

        # The first implementation intentionally supports standard Minecraft roots.
        # Third-party launcher instance formats will be handled separately later.
        if not _looks_like_standard_minecraft_root(resolved):
            continue

        installations.append(
            MinecraftInstallation(
                root=resolved,
                source=source,
                versions=_find_versions_in_standard_root(resolved),
            )
        )

    return installations


def find_default_minecraft_installation() -> MinecraftInstallation | None:
    installations = find_minecraft_installations()
    return installations[0] if installations else None

from __future__ import annotations

import json
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path

from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion


@dataclass(frozen=True)
class ResolvedLibrary:
    name: str
    path: Path | None
    url: str | None
    sha1: str | None
    size: int | None
    required: bool
    present: bool
    is_native: bool


@dataclass(frozen=True)
class LibraryResolution:
    libraries: tuple[ResolvedLibrary, ...]
    classpath_entries: tuple[Path, ...]
    missing_required: tuple[ResolvedLibrary, ...]
    native_libraries: tuple[ResolvedLibrary, ...]

    @property
    def ready(self) -> bool:
        return not self.missing_required

    @property
    def classpath(self) -> str:
        return os.pathsep.join(str(path) for path in self.classpath_entries)


def _load_json(version: MinecraftVersion) -> dict:
    try:
        data = json.loads(version.json_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo leer {version.json_file}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"El JSON de {version.version_id} no es válido.")

    return data


def _windows_arch_tokens() -> tuple[str, str]:
    machine = platform.machine().lower()
    arch = "64" if machine in {"amd64", "x86_64", "arm64", "aarch64"} else "32"
    native_arch = "arm64" if machine in {"arm64", "aarch64"} else arch
    return arch, native_arch


def _rule_matches(rule: dict) -> bool:
    os_rule = rule.get("os")
    if isinstance(os_rule, dict):
        name = os_rule.get("name")
        if isinstance(name, str) and name != "windows":
            return False

        arch_pattern = os_rule.get("arch")
        if isinstance(arch_pattern, str):
            machine = platform.machine().lower()
            if re.fullmatch(arch_pattern, machine) is None:
                return False

        version_pattern = os_rule.get("version")
        if isinstance(version_pattern, str):
            win_version = platform.version()
            if re.search(version_pattern, win_version) is None:
                return False

    features = rule.get("features")
    if isinstance(features, dict):
        # Features are launch-profile specific (demo mode, custom resolution, etc.).
        # MiyuLauncher currently treats unspecified features as false.
        for value in features.values():
            if value is True:
                return False

    return True


def _is_allowed(library: dict) -> bool:
    rules = library.get("rules")
    if not isinstance(rules, list) or not rules:
        return True

    allowed = False
    for rule in rules:
        if not isinstance(rule, dict) or not _rule_matches(rule):
            continue
        action = rule.get("action")
        allowed = action == "allow"

    return allowed


def _artifact_from_maven_name(name: str, libraries_root: Path) -> Path | None:
    # group:artifact:version[:classifier]
    parts = name.split(":")
    if len(parts) < 3:
        return None

    group, artifact, version = parts[:3]
    classifier = parts[3] if len(parts) > 3 else None
    filename = f"{artifact}-{version}"
    if classifier:
        filename += f"-{classifier}"
    filename += ".jar"

    return libraries_root / Path(*group.split(".")) / artifact / version / filename


def _resolve_native_classifier(library: dict) -> str | None:
    natives = library.get("natives")
    if not isinstance(natives, dict):
        return None

    value = natives.get("windows")
    if not isinstance(value, str):
        return None

    arch, native_arch = _windows_arch_tokens()
    return value.replace("${arch}", arch).replace("${os_arch}", native_arch)


def resolve_libraries(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
) -> LibraryResolution:
    data = _load_json(version)
    libraries_data = data.get("libraries")
    if not isinstance(libraries_data, list):
        libraries_data = []

    resolved: list[ResolvedLibrary] = []
    classpath_entries: list[Path] = []
    missing_required: list[ResolvedLibrary] = []
    native_libraries: list[ResolvedLibrary] = []

    libraries_root = installation.root / "libraries"

    for library in libraries_data:
        if not isinstance(library, dict) or not _is_allowed(library):
            continue

        name = library.get("name")
        if not isinstance(name, str):
            name = "unknown"

        downloads = library.get("downloads")
        downloads = downloads if isinstance(downloads, dict) else {}

        artifact = downloads.get("artifact")
        artifact = artifact if isinstance(artifact, dict) else None

        if artifact is not None:
            relative = artifact.get("path")
            path = libraries_root / relative if isinstance(relative, str) else _artifact_from_maven_name(name, libraries_root)
            url = artifact.get("url") if isinstance(artifact.get("url"), str) else None
            sha1 = artifact.get("sha1") if isinstance(artifact.get("sha1"), str) else None
            size = artifact.get("size") if isinstance(artifact.get("size"), int) else None

            item = ResolvedLibrary(
                name=name,
                path=path,
                url=url,
                sha1=sha1,
                size=size,
                required=True,
                present=path.is_file() if path is not None else False,
                is_native=False,
            )
            resolved.append(item)

            if item.present and item.path is not None:
                classpath_entries.append(item.path)
            elif not item.present:
                missing_required.append(item)

        elif not isinstance(library.get("natives"), dict):
            path = _artifact_from_maven_name(name, libraries_root)
            item = ResolvedLibrary(
                name=name,
                path=path,
                url=None,
                sha1=None,
                size=None,
                required=True,
                present=path.is_file() if path is not None else False,
                is_native=False,
            )
            resolved.append(item)
            if item.present and item.path is not None:
                classpath_entries.append(item.path)
            elif not item.present:
                missing_required.append(item)

        classifier = _resolve_native_classifier(library)
        if classifier:
            classifiers = downloads.get("classifiers")
            classifiers = classifiers if isinstance(classifiers, dict) else {}
            native_download = classifiers.get(classifier)
            native_download = native_download if isinstance(native_download, dict) else None

            if native_download is not None:
                relative = native_download.get("path")
                path = libraries_root / relative if isinstance(relative, str) else None
                url = native_download.get("url") if isinstance(native_download.get("url"), str) else None
                sha1 = native_download.get("sha1") if isinstance(native_download.get("sha1"), str) else None
                size = native_download.get("size") if isinstance(native_download.get("size"), int) else None

                native = ResolvedLibrary(
                    name=f"{name}:{classifier}",
                    path=path,
                    url=url,
                    sha1=sha1,
                    size=size,
                    required=True,
                    present=path.is_file() if path is not None else False,
                    is_native=True,
                )
                resolved.append(native)
                native_libraries.append(native)
                if not native.present:
                    missing_required.append(native)

    client_jar = version.directory / f"{version.version_id}.jar"
    if client_jar.is_file():
        classpath_entries.append(client_jar)

    # Keep order, remove duplicates.
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in classpath_entries:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)

    return LibraryResolution(
        libraries=tuple(resolved),
        classpath_entries=tuple(deduped),
        missing_required=tuple(missing_required),
        native_libraries=tuple(native_libraries),
    )

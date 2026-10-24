from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from miyu_launcher.core.java import JavaInstallation, select_java
from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion
from miyu_launcher.core.runtime import find_managed_runtime


@dataclass(frozen=True)
class ResolvedMinecraftVersion:
    version: MinecraftVersion
    installation_root: Path
    java: JavaInstallation | None
    java_source: str | None
    required_java_major: int | None
    java_compatible: bool
    client_jar: Path
    client_jar_exists: bool
    client_download_url: str | None
    assets_root: Path
    asset_index_id: str | None
    libraries_root: Path
    declared_libraries: int
    main_class: str | None
    uses_modern_arguments: bool
    inherits_from: str | None

    @property
    def ready_for_launch(self) -> bool:
        return (
            self.java_compatible
            and self.client_jar_exists
            and self.main_class is not None
        )


def _load_version_json(version: MinecraftVersion) -> dict:
    try:
        data = json.loads(version.json_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo leer el JSON de {version.version_id}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"El JSON de {version.version_id} no contiene un objeto válido.")

    return data


def _select_java_for_version(required_java: int | None) -> tuple[JavaInstallation | None, str | None]:
    """Prefer MiyuLauncher's managed runtime, then fall back to system Java."""

    if required_java is not None:
        managed = find_managed_runtime(required_java)
        if managed is not None:
            return managed.installation, "MiyuLauncher managed runtime"

        system_java = select_java(required_java)
        if system_java is not None:
            return system_java, "System Java"

        return None, None

    system_java = select_java()
    if system_java is not None:
        return system_java, "System Java"

    return None, None


def resolve_version(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
) -> ResolvedMinecraftVersion:
    """Resolve local resources and the Java runtime required by a Minecraft version.

    This stage is read-only. Managed runtimes are preferred when already installed,
    but this function never downloads or modifies anything.
    """

    _load_version_json(version)

    required_java = version.java_major_version
    java, java_source = _select_java_for_version(required_java)
    java_compatible = java is not None and (
        required_java is None or java.major == required_java
    )

    client_jar = version.directory / f"{version.version_id}.jar"

    return ResolvedMinecraftVersion(
        version=version,
        installation_root=installation.root,
        java=java,
        java_source=java_source,
        required_java_major=required_java,
        java_compatible=java_compatible,
        client_jar=client_jar,
        client_jar_exists=client_jar.is_file(),
        client_download_url=version.client_download_url,
        assets_root=installation.root / "assets",
        asset_index_id=version.asset_index_id,
        libraries_root=installation.root / "libraries",
        declared_libraries=version.libraries_count,
        main_class=version.main_class,
        uses_modern_arguments=version.has_modern_arguments,
        inherits_from=version.inherits_from,
    )


def resolve_all_versions(
    installation: MinecraftInstallation,
) -> tuple[ResolvedMinecraftVersion, ...]:
    return tuple(resolve_version(installation, version) for version in installation.versions)

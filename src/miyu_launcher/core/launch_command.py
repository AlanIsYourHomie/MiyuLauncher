from __future__ import annotations

import json
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path

from miyu_launcher.core.libraries import resolve_libraries
from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion
from miyu_launcher.core.version_resolver import resolve_version


@dataclass(frozen=True)
class LaunchProfile:
    username: str = "MiyuPlayer"
    uuid: str = "00000000000000000000000000000000"
    access_token: str = "0"
    user_type: str = "msa"
    xuid: str = ""
    client_id: str = ""


@dataclass(frozen=True)
class LaunchCommand:
    executable: Path
    jvm_arguments: tuple[str, ...]
    main_class: str
    game_arguments: tuple[str, ...]
    command: tuple[str, ...]
    game_directory: Path
    natives_directory: Path
    classpath: str


def _load_json(version: MinecraftVersion) -> dict:
    try:
        data = json.loads(version.json_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo leer {version.json_file}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"El JSON de {version.version_id} no es válido.")
    return data


def _rule_matches(rule: dict, features: dict[str, bool]) -> bool:
    os_rule = rule.get("os")
    if isinstance(os_rule, dict):
        name = os_rule.get("name")
        if isinstance(name, str) and name != "windows":
            return False

        arch = os_rule.get("arch")
        if isinstance(arch, str) and re.fullmatch(arch, platform.machine().lower()) is None:
            return False

        version = os_rule.get("version")
        if isinstance(version, str) and re.search(version, platform.version()) is None:
            return False

    feature_rule = rule.get("features")
    if isinstance(feature_rule, dict):
        for key, expected in feature_rule.items():
            if bool(features.get(key, False)) != bool(expected):
                return False

    return True


def _is_allowed(entry: dict, features: dict[str, bool]) -> bool:
    rules = entry.get("rules")
    if not isinstance(rules, list) or not rules:
        return True

    allowed = False
    for rule in rules:
        if not isinstance(rule, dict) or not _rule_matches(rule, features):
            continue
        allowed = rule.get("action") == "allow"
    return allowed


def _expand_argument(value: str, variables: dict[str, str]) -> str:
    result = value
    for key, replacement in variables.items():
        result = result.replace("${" + key + "}", replacement)
    return result


def _collect_arguments(entries: object, variables: dict[str, str], features: dict[str, bool]) -> list[str]:
    if not isinstance(entries, list):
        return []

    result: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            result.append(_expand_argument(entry, variables))
            continue

        if not isinstance(entry, dict) or not _is_allowed(entry, features):
            continue

        value = entry.get("value")
        if isinstance(value, str):
            result.append(_expand_argument(value, variables))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    result.append(_expand_argument(item, variables))

    return result


def build_launch_command(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
    *,
    profile: LaunchProfile | None = None,
    game_directory: Path | None = None,
    memory_mb: int = 4096,
) -> LaunchCommand:
    profile = profile or LaunchProfile()
    data = _load_json(version)
    resolved = resolve_version(installation, version)
    libraries = resolve_libraries(installation, version)

    if resolved.java is None or not resolved.java_compatible:
        raise ValueError(f"No hay un Java compatible para {version.version_id}.")
    if not libraries.ready:
        raise ValueError(f"Faltan {len(libraries.missing_required)} librerías para {version.version_id}.")
    if not resolved.client_jar_exists:
        raise ValueError(f"Falta el client jar de {version.version_id}.")
    if not resolved.main_class:
        raise ValueError(f"{version.version_id} no declara mainClass.")

    game_dir = game_directory or installation.root
    natives_dir = installation.root / "versions" / version.version_id / "natives"
    assets_root = installation.root / "assets"
    classpath = libraries.classpath

    variables = {
        "auth_player_name": profile.username,
        "version_name": version.version_id,
        "game_directory": str(game_dir),
        "assets_root": str(assets_root),
        "assets_index_name": resolved.asset_index_id or "",
        "auth_uuid": profile.uuid,
        "auth_access_token": profile.access_token,
        "clientid": profile.client_id,
        "auth_xuid": profile.xuid,
        "user_type": profile.user_type,
        "version_type": version.version_type or "release",
        "natives_directory": str(natives_dir),
        "launcher_name": "MiyuLauncher",
        "launcher_version": "0.1.0-dev",
        "classpath": classpath,
        "classpath_separator": os.pathsep,
        "library_directory": str(installation.root / "libraries"),
    }

    features = {
        "is_demo_user": False,
        "has_custom_resolution": False,
        "has_quick_plays_support": False,
        "is_quick_play_singleplayer": False,
        "is_quick_play_multiplayer": False,
        "is_quick_play_realms": False,
    }

    arguments = data.get("arguments")
    if not isinstance(arguments, dict):
        raise ValueError(f"{version.version_id} no usa el formato moderno de argumentos.")

    jvm_args = _collect_arguments(arguments.get("jvm"), variables, features)
    game_args = _collect_arguments(arguments.get("game"), variables, features)

    # Keep a launcher-controlled memory limit even if Mojang's JSON does not include one.
    if not any(arg.startswith("-Xmx") for arg in jvm_args):
        jvm_args.insert(0, f"-Xmx{memory_mb}M")
    if not any(arg.startswith("-Xms") for arg in jvm_args):
        jvm_args.insert(0, "-Xms512M")

    command = (
        str(resolved.java.executable),
        *jvm_args,
        resolved.main_class,
        *game_args,
    )

    return LaunchCommand(
        executable=resolved.java.executable,
        jvm_arguments=tuple(jvm_args),
        main_class=resolved.main_class,
        game_arguments=tuple(game_args),
        command=tuple(command),
        game_directory=game_dir,
        natives_directory=natives_dir,
        classpath=classpath,
    )

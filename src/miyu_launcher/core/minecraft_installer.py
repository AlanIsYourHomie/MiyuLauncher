from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from miyu_launcher.core.libraries import ResolvedLibrary, resolve_libraries
from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion


USER_AGENT = "MiyuLauncher/0.1.0-dev"


class MinecraftInstallError(RuntimeError):
    pass


class MinecraftDownloadError(MinecraftInstallError):
    pass


class MinecraftVerificationError(MinecraftInstallError):
    pass


@dataclass(frozen=True)
class DownloadTask:
    label: str
    destination: Path
    url: str
    sha1: str | None
    size: int | None


@dataclass(frozen=True)
class InstallPlan:
    version_id: str
    tasks: tuple[DownloadTask, ...]

    @property
    def total_files(self) -> int:
        return len(self.tasks)

    @property
    def total_bytes(self) -> int | None:
        sizes = [task.size for task in self.tasks if task.size is not None]
        if len(sizes) != len(self.tasks):
            return None
        return sum(sizes)


ProgressCallback = Callable[[int, int, DownloadTask], None]


def _load_version_json(version: MinecraftVersion) -> dict:
    try:
        data = json.loads(version.json_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MinecraftInstallError(f"No se pudo leer {version.json_file}: {exc}") from exc

    if not isinstance(data, dict):
        raise MinecraftInstallError(f"El JSON de {version.version_id} no es válido.")

    return data


def _sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _library_task(item: ResolvedLibrary) -> DownloadTask | None:
    if item.present or item.path is None or not item.url:
        return None

    return DownloadTask(
        label=item.name,
        destination=item.path,
        url=item.url,
        sha1=item.sha1,
        size=item.size,
    )


def build_install_plan(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
) -> InstallPlan:
    tasks: list[DownloadTask] = []

    library_resolution = resolve_libraries(installation, version)
    for item in library_resolution.missing_required:
        task = _library_task(item)
        if task is None:
            if item.path is not None and not item.present:
                raise MinecraftInstallError(
                    f"Falta {item.name}, pero el JSON no contiene una URL de descarga."
                )
            continue
        tasks.append(task)

    client_jar = version.directory / f"{version.version_id}.jar"
    if not client_jar.is_file():
        data = _load_version_json(version)
        downloads = data.get("downloads") if isinstance(data.get("downloads"), dict) else {}
        client = downloads.get("client") if isinstance(downloads.get("client"), dict) else {}
        url = client.get("url")
        sha1 = client.get("sha1")
        size = client.get("size")

        if not isinstance(url, str) or not url:
            raise MinecraftInstallError(
                f"{version.version_id} no tiene client jar local ni URL de descarga."
            )

        tasks.append(
            DownloadTask(
                label=f"Minecraft client {version.version_id}",
                destination=client_jar,
                url=url,
                sha1=sha1 if isinstance(sha1, str) else None,
                size=size if isinstance(size, int) else None,
            )
        )

    # Keep order, remove duplicate destinations.
    deduped: list[DownloadTask] = []
    seen: set[str] = set()
    for task in tasks:
        key = str(task.destination).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(task)

    return InstallPlan(version_id=version.version_id, tasks=tuple(deduped))


def _download_task(task: DownloadTask) -> None:
    task.destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = task.destination.with_suffix(task.destination.suffix + ".part")
    temporary.unlink(missing_ok=True)

    request = urllib.request.Request(task.url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=30) as response, temporary.open("wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        temporary.unlink(missing_ok=True)
        raise MinecraftDownloadError(f"Falló la descarga de {task.label}: {exc}") from exc

    if task.sha1 is not None:
        actual = _sha1(temporary)
        if actual.lower() != task.sha1.lower():
            temporary.unlink(missing_ok=True)
            raise MinecraftVerificationError(
                f"El SHA-1 de {task.label} no coincide con el publicado."
            )

    temporary.replace(task.destination)


def install_version_dependencies(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
    *,
    progress: ProgressCallback | None = None,
) -> InstallPlan:
    plan = build_install_plan(installation, version)

    total = len(plan.tasks)
    for index, task in enumerate(plan.tasks, start=1):
        if progress is not None:
            progress(index, total, task)
        _download_task(task)

    return plan

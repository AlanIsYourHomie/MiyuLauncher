from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from miyu_launcher.core.java import JavaInstallation, inspect_java
from miyu_launcher.core.paths import LauncherPaths, get_launcher_paths


ADOPTIUM_API = "https://api.adoptium.net/v3"
USER_AGENT = "MiyuLauncher/0.1.0-dev"


class RuntimeErrorBase(RuntimeError):
    """Base exception for managed Java runtime operations."""


class RuntimeUnavailableError(RuntimeErrorBase):
    pass


class RuntimeDownloadError(RuntimeErrorBase):
    pass


class RuntimeVerificationError(RuntimeErrorBase):
    pass


class RuntimeInstallError(RuntimeErrorBase):
    pass


@dataclass(frozen=True)
class RuntimePackage:
    java_major: int
    vendor: str
    image_type: str
    architecture: str
    os_name: str
    release_name: str | None
    version: str | None
    filename: str
    url: str
    sha256: str
    size: int | None


@dataclass(frozen=True)
class ManagedRuntime:
    java_major: int
    root: Path
    executable: Path
    installation: JavaInstallation


ProgressCallback = Callable[[int, int | None], None]


def _platform_name() -> str:
    if os.name == "nt":
        return "windows"
    raise RuntimeUnavailableError("MiyuLauncher solo administra runtimes de Windows por ahora.")


def _architecture_name() -> str:
    machine = os.environ.get("PROCESSOR_ARCHITECTURE", "").lower()
    wow64 = os.environ.get("PROCESSOR_ARCHITEW6432", "").lower()
    value = wow64 or machine

    if value in {"amd64", "x86_64"}:
        return "x64"
    if value in {"arm64", "aarch64"}:
        return "aarch64"
    if value in {"x86", "i386", "i686"}:
        return "x86"

    # Windows 64-bit is the primary target for the project.
    return "x64"


def _runtime_dir(paths: LauncherPaths, java_major: int) -> Path:
    return paths.runtime / f"java-{java_major}"


def find_managed_runtime(
    java_major: int,
    paths: LauncherPaths | None = None,
) -> ManagedRuntime | None:
    paths = paths or get_launcher_paths()
    root = _runtime_dir(paths, java_major)
    executable = root / "bin" / "java.exe"

    installation = inspect_java(executable)
    if installation is None or installation.major != java_major:
        return None

    return ManagedRuntime(
        java_major=java_major,
        root=root,
        executable=installation.executable,
        installation=installation,
    )


def _request_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeDownloadError(f"No se pudo consultar Adoptium: {exc}") from exc


def get_latest_runtime_package(
    java_major: int,
    *,
    image_type: str = "jre",
) -> RuntimePackage:
    os_name = _platform_name()
    architecture = _architecture_name()

    query = urllib.parse.urlencode(
        {
            "architecture": architecture,
            "image_type": image_type,
            "os": os_name,
            "vendor": "eclipse",
        }
    )
    url = f"{ADOPTIUM_API}/assets/latest/{java_major}/hotspot?{query}"
    payload = _request_json(url)

    if not isinstance(payload, list) or not payload:
        raise RuntimeUnavailableError(
            f"Adoptium no devolvió un runtime Java {java_major} para {os_name}/{architecture}."
        )

    asset = payload[0]
    if not isinstance(asset, dict):
        raise RuntimeUnavailableError("La respuesta de Adoptium no tiene el formato esperado.")

    binary = asset.get("binary")
    if not isinstance(binary, dict):
        raise RuntimeUnavailableError("La respuesta de Adoptium no contiene un binario.")

    package = binary.get("package")
    if not isinstance(package, dict):
        raise RuntimeUnavailableError("La respuesta de Adoptium no contiene un paquete descargable.")

    download_url = package.get("link")
    checksum = package.get("checksum")
    filename = package.get("name")

    if not all(isinstance(value, str) and value for value in (download_url, checksum, filename)):
        raise RuntimeUnavailableError("Faltan URL, checksum o nombre del paquete Java.")

    size = package.get("size")
    if not isinstance(size, int):
        size = None

    version_data = asset.get("version")
    semantic_version = None
    if isinstance(version_data, dict):
        value = version_data.get("semver")
        if isinstance(value, str):
            semantic_version = value

    release_name = asset.get("release_name")
    if not isinstance(release_name, str):
        release_name = None

    return RuntimePackage(
        java_major=java_major,
        vendor="Eclipse Temurin",
        image_type=image_type,
        architecture=architecture,
        os_name=os_name,
        release_name=release_name,
        version=semantic_version,
        filename=filename,
        url=download_url,
        sha256=checksum.lower(),
        size=size,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_file(
    url: str,
    destination: Path,
    progress: ProgressCallback | None = None,
) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=30) as response, destination.open("wb") as file:
            total_header = response.headers.get("Content-Length")
            total = int(total_header) if total_header and total_header.isdigit() else None
            downloaded = 0

            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
                downloaded += len(chunk)
                if progress is not None:
                    progress(downloaded, total)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeDownloadError(f"Falló la descarga del runtime Java: {exc}") from exc


def _extract_runtime(archive: Path, destination: Path) -> None:
    try:
        with tempfile.TemporaryDirectory(prefix="miyu-java-extract-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            with zipfile.ZipFile(archive) as zip_file:
                zip_file.extractall(temp_dir)

            children = [child for child in temp_dir.iterdir() if child.name != "__MACOSX"]
            source_root = children[0] if len(children) == 1 and children[0].is_dir() else temp_dir

            if destination.exists():
                shutil.rmtree(destination)

            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_root, destination)
    except (OSError, zipfile.BadZipFile) as exc:
        raise RuntimeInstallError(f"No se pudo extraer el runtime Java: {exc}") from exc


def install_managed_runtime(
    java_major: int,
    paths: LauncherPaths | None = None,
    *,
    progress: ProgressCallback | None = None,
    force: bool = False,
) -> ManagedRuntime:
    paths = paths or get_launcher_paths()
    paths.create()

    existing = find_managed_runtime(java_major, paths)
    if existing is not None and not force:
        return existing

    package = get_latest_runtime_package(java_major)
    archive = paths.downloads / package.filename
    target = _runtime_dir(paths, java_major)

    _download_file(package.url, archive, progress)

    actual_checksum = _sha256(archive)
    if actual_checksum.lower() != package.sha256.lower():
        archive.unlink(missing_ok=True)
        raise RuntimeVerificationError(
            "El SHA-256 del runtime descargado no coincide con el publicado por Adoptium."
        )

    _extract_runtime(archive, target)
    archive.unlink(missing_ok=True)

    runtime = find_managed_runtime(java_major, paths)
    if runtime is None:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        raise RuntimeInstallError(
            f"El runtime se extrajo, pero Java {java_major} no pudo validarse."
        )

    metadata = {
        "java_major": java_major,
        "vendor": package.vendor,
        "release_name": package.release_name,
        "version": runtime.installation.version,
        "sha256": package.sha256,
        "source_url": package.url,
    }
    try:
        (target / "miyu-runtime.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        # Metadata is useful for diagnostics, but it is not required to run Java.
        pass

    return runtime


def ensure_managed_runtime(
    java_major: int,
    paths: LauncherPaths | None = None,
    *,
    progress: ProgressCallback | None = None,
) -> ManagedRuntime:
    runtime = find_managed_runtime(java_major, paths)
    if runtime is not None:
        return runtime
    return install_managed_runtime(java_major, paths, progress=progress)

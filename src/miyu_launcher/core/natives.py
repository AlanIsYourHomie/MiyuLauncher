from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from miyu_launcher.core.libraries import LibraryResolution, ResolvedLibrary
from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion


class NativeError(RuntimeError):
    pass


@dataclass(frozen=True)
class NativeExtraction:
    native_jars: tuple[Path, ...]
    destination: Path
    extracted_files: tuple[Path, ...]


def _looks_like_native_jar(library: ResolvedLibrary) -> bool:
    if library.path is None or not library.present:
        return False
    name = library.name.lower()
    filename = library.path.name.lower()
    return (
        library.is_native
        or "natives-windows" in name
        or "natives-windows" in filename
        or "native-windows" in name
        or "native-windows" in filename
    )


def find_native_jars(resolution: LibraryResolution) -> tuple[Path, ...]:
    jars: list[Path] = []
    seen: set[str] = set()
    for library in resolution.libraries:
        if not _looks_like_native_jar(library) or library.path is None:
            continue
        key = str(library.path).lower()
        if key in seen:
            continue
        seen.add(key)
        jars.append(library.path)
    return tuple(jars)


def extract_natives(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
    resolution: LibraryResolution,
) -> NativeExtraction:
    destination = installation.root / "versions" / version.version_id / "natives"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    native_jars = find_native_jars(resolution)
    extracted: list[Path] = []

    for jar in native_jars:
        try:
            with zipfile.ZipFile(jar) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    normalized = member.filename.replace("\\", "/")
                    upper = normalized.upper()
                    if normalized.startswith("META-INF/"):
                        continue
                    if not upper.endswith((".DLL", ".SO", ".DYLIB")):
                        continue

                    target = destination / Path(normalized).name
                    with archive.open(member) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted.append(target)
        except (OSError, zipfile.BadZipFile) as exc:
            raise NativeError(f"No se pudieron extraer natives desde {jar}: {exc}") from exc

    return NativeExtraction(
        native_jars=native_jars,
        destination=destination,
        extracted_files=tuple(extracted),
    )

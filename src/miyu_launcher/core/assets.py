from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion


USER_AGENT = "MiyuLauncher/0.1.0-dev"
ASSET_BASE_URL = "https://resources.download.minecraft.net"


class AssetError(RuntimeError):
    pass


@dataclass(frozen=True)
class AssetIndexInfo:
    asset_id: str
    url: str
    sha1: str | None
    size: int | None
    path: Path


@dataclass(frozen=True)
class AssetObject:
    logical_name: str
    sha1: str
    size: int | None
    path: Path
    url: str
    present: bool


@dataclass(frozen=True)
class AssetResolution:
    index: AssetIndexInfo
    index_present: bool
    objects: tuple[AssetObject, ...]
    missing: tuple[AssetObject, ...]

    @property
    def ready(self) -> bool:
        return self.index_present and not self.missing


ProgressCallback = Callable[[int, int | None, str], None]


def _load_version_json(version: MinecraftVersion) -> dict:
    try:
        data = json.loads(version.json_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AssetError(f"No se pudo leer {version.json_file}: {exc}") from exc
    if not isinstance(data, dict):
        raise AssetError(f"El JSON de {version.version_id} no es válido.")
    return data


def get_asset_index_info(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
) -> AssetIndexInfo:
    data = _load_version_json(version)
    raw = data.get("assetIndex")
    if not isinstance(raw, dict):
        raise AssetError(f"{version.version_id} no declara assetIndex.")

    asset_id = raw.get("id")
    url = raw.get("url")
    if not isinstance(asset_id, str) or not isinstance(url, str):
        raise AssetError(f"El assetIndex de {version.version_id} está incompleto.")

    sha1 = raw.get("sha1") if isinstance(raw.get("sha1"), str) else None
    size = raw.get("size") if isinstance(raw.get("size"), int) else None
    path = installation.root / "assets" / "indexes" / f"{asset_id}.json"
    return AssetIndexInfo(asset_id=asset_id, url=url, sha1=sha1, size=size, path=path)


def _sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response, temp.open("wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
        temp.replace(destination)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        temp.unlink(missing_ok=True)
        raise AssetError(f"Falló la descarga de {url}: {exc}") from exc


def ensure_asset_index(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
) -> AssetIndexInfo:
    info = get_asset_index_info(installation, version)
    valid = info.path.is_file()
    if valid and info.sha1:
        try:
            valid = _sha1(info.path).lower() == info.sha1.lower()
        except OSError:
            valid = False

    if not valid:
        _download(info.url, info.path)
        if info.sha1 and _sha1(info.path).lower() != info.sha1.lower():
            info.path.unlink(missing_ok=True)
            raise AssetError("El SHA-1 del asset index no coincide con el publicado por Mojang.")

    return info


def resolve_assets(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
    *,
    ensure_index: bool = False,
) -> AssetResolution:
    info = ensure_asset_index(installation, version) if ensure_index else get_asset_index_info(installation, version)
    if not info.path.is_file():
        return AssetResolution(index=info, index_present=False, objects=(), missing=())

    try:
        payload = json.loads(info.path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AssetError(f"No se pudo leer el asset index {info.path}: {exc}") from exc

    raw_objects = payload.get("objects") if isinstance(payload, dict) else None
    if not isinstance(raw_objects, dict):
        raise AssetError("El asset index no contiene una tabla de objects válida.")

    objects: list[AssetObject] = []
    missing: list[AssetObject] = []
    object_root = installation.root / "assets" / "objects"

    for logical_name, raw in raw_objects.items():
        if not isinstance(logical_name, str) or not isinstance(raw, dict):
            continue
        sha1 = raw.get("hash")
        if not isinstance(sha1, str) or len(sha1) < 2:
            continue
        size = raw.get("size") if isinstance(raw.get("size"), int) else None
        path = object_root / sha1[:2] / sha1
        url = f"{ASSET_BASE_URL}/{sha1[:2]}/{sha1}"
        item = AssetObject(
            logical_name=logical_name,
            sha1=sha1,
            size=size,
            path=path,
            url=url,
            present=path.is_file(),
        )
        objects.append(item)
        if not item.present:
            missing.append(item)

    return AssetResolution(
        index=info,
        index_present=True,
        objects=tuple(objects),
        missing=tuple(missing),
    )


def install_missing_assets(
    installation: MinecraftInstallation,
    version: MinecraftVersion,
    *,
    progress: ProgressCallback | None = None,
) -> AssetResolution:
    resolution = resolve_assets(installation, version, ensure_index=True)
    missing = list(resolution.missing)
    total = len(missing)

    for index, asset in enumerate(missing, start=1):
        if progress is not None:
            progress(index - 1, total, asset.logical_name)
        _download(asset.url, asset.path)
        if _sha1(asset.path).lower() != asset.sha1.lower():
            asset.path.unlink(missing_ok=True)
            raise AssetError(f"SHA-1 inválido para asset {asset.logical_name}.")

    if progress is not None:
        progress(total, total, "completado")

    return resolve_assets(installation, version)

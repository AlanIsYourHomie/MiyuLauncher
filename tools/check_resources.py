from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.assets import install_missing_assets, resolve_assets
from miyu_launcher.core.libraries import resolve_libraries
from miyu_launcher.core.minecraft import find_default_minecraft_installation
from miyu_launcher.core.natives import extract_natives, find_native_jars


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()

    installation = find_default_minecraft_installation()
    if installation is None:
        print("No se encontró una instalación estándar de Minecraft.")
        return

    version = next((v for v in installation.versions if v.version_id == args.version), None)
    if version is None:
        print(f"No se encontró la versión {args.version}.")
        return

    libraries = resolve_libraries(installation, version)
    native_jars = find_native_jars(libraries)

    try:
        assets = resolve_assets(installation, version, ensure_index=args.install)
    except Exception as exc:
        print(f"Error al resolver assets: {exc}")
        return

    print(f"Versión: {version.version_id}")
    print(f"Asset index: {assets.index.asset_id}")
    print(f"Asset index presente: {'sí' if assets.index_present else 'no'}")
    print(f"Assets conocidos: {len(assets.objects)}")
    print(f"Assets faltantes: {len(assets.missing)}")
    missing_size = sum(item.size or 0 for item in assets.missing)
    print(f"Tamaño faltante conocido: {missing_size / 1024 / 1024:.1f} MB")
    print(f"JARs nativos detectados: {len(native_jars)}")
    for jar in native_jars[:8]:
        print(f"  - {jar.name}")

    if not args.install:
        print("\nInspección correcta. Para completar recursos ejecuta:")
        print(f"python tools/check_resources.py {version.version_id} --install")
        return

    print("\nInstalando assets...")
    last_percent = -1

    def progress(done: int, total: int | None, name: str) -> None:
        nonlocal last_percent
        if not total:
            return
        percent = int(done * 100 / total)
        if percent != last_percent and (percent % 5 == 0 or done == total):
            print(f"Assets: {done}/{total} ({percent}%)")
            last_percent = percent

    assets = install_missing_assets(installation, version, progress=progress)
    print(f"Assets listos: {'sí' if assets.ready else 'no'}")

    print("Extrayendo natives...")
    extraction = extract_natives(installation, version, libraries)
    print(f"JARs nativos usados: {len(extraction.native_jars)}")
    print(f"Archivos nativos extraídos: {len(extraction.extracted_files)}")
    print(f"Directorio natives: {extraction.destination}")


if __name__ == "__main__":
    main()

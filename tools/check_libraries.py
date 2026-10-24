from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.libraries import resolve_libraries
from miyu_launcher.core.minecraft import find_default_minecraft_installation


def _yes_no(value: bool) -> str:
    return "sí" if value else "no"


def main() -> None:
    installation = find_default_minecraft_installation()
    if installation is None:
        print("No se encontró una instalación estándar de Minecraft.")
        return

    print(f"Instalación: {installation.root}\n")

    for version in installation.versions:
        resolution = resolve_libraries(installation, version)
        print(f"- {version.version_id}")
        print(f"    librerías aplicables: {len(resolution.libraries)}")
        print(f"    entradas classpath presentes: {len(resolution.classpath_entries)}")
        print(f"    natives aplicables: {len(resolution.native_libraries)}")
        print(f"    faltantes requeridas: {len(resolution.missing_required)}")
        print(f"    classpath listo: {_yes_no(resolution.ready)}")

        if resolution.missing_required:
            print("    primeras faltantes:")
            for item in resolution.missing_required[:8]:
                location = str(item.path) if item.path is not None else "ruta desconocida"
                print(f"      - {item.name}")
                print(f"        {location}")

        print()


if __name__ == "__main__":
    main()

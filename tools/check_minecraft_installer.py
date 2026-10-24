from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.minecraft import find_default_minecraft_installation
from miyu_launcher.core.minecraft_installer import (
    MinecraftInstallError,
    build_install_plan,
    install_version_dependencies,
)


def _find_version(version_id: str):
    installation = find_default_minecraft_installation()
    if installation is None:
        raise MinecraftInstallError("No se encontró una instalación estándar de Minecraft.")

    for version in installation.versions:
        if version.version_id == version_id:
            return installation, version

    raise MinecraftInstallError(f"No se encontró la versión {version_id}.")


def _format_size(value: int | None) -> str:
    if value is None:
        return "desconocido"
    return f"{value / (1024 * 1024):.1f} MB"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="ID exacto de la versión, por ejemplo 26.3")
    parser.add_argument("--install", action="store_true", help="Descargar e instalar los archivos faltantes")
    args = parser.parse_args()

    try:
        installation, version = _find_version(args.version)
        plan = build_install_plan(installation, version)
    except MinecraftInstallError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    print(f"Versión: {version.version_id}")
    print(f"Archivos faltantes descargables: {plan.total_files}")
    print(f"Tamaño total conocido: {_format_size(plan.total_bytes)}")

    if plan.tasks:
        print("\nPrimeras tareas:")
        for task in plan.tasks[:10]:
            print(f"  - {task.label}")
            print(f"    {_format_size(task.size)}")
            print(f"    -> {task.destination}")
    else:
        print("\nNo falta ningún archivo de cliente/librerías.")

    if not args.install:
        print("\nSolo se generó el plan. Para instalar:")
        print(f"python tools/check_minecraft_installer.py {version.version_id} --install")
        return

    if not plan.tasks:
        return

    print("\nInstalando dependencias...")

    def progress(index, total, task):
        print(f"[{index}/{total}] {task.label}")

    try:
        install_version_dependencies(installation, version, progress=progress)
    except MinecraftInstallError as exc:
        print(f"\nError: {exc}")
        raise SystemExit(1)

    print("\nInstalación de cliente/librerías completada.")


if __name__ == "__main__":
    main()

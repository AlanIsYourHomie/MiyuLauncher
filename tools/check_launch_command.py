from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.launch_command import build_launch_command
from miyu_launcher.core.minecraft import find_default_minecraft_installation


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python tools/check_launch_command.py <version>")
        raise SystemExit(2)

    version_id = sys.argv[1]
    installation = find_default_minecraft_installation()
    if installation is None:
        print("No se encontró una instalación estándar de Minecraft.")
        raise SystemExit(1)

    version = next((item for item in installation.versions if item.version_id == version_id), None)
    if version is None:
        print(f"No se encontró la versión {version_id}.")
        raise SystemExit(1)

    launch = build_launch_command(installation, version)

    print(f"Versión: {version_id}")
    print(f"Java: {launch.executable}")
    print(f"Main class: {launch.main_class}")
    print(f"Game dir: {launch.game_directory}")
    print(f"Natives: {launch.natives_directory}")
    print(f"Entradas JVM: {len(launch.jvm_arguments)}")
    print(f"Entradas juego: {len(launch.game_arguments)}")
    print(f"Classpath chars: {len(launch.classpath)}")
    print(f"Argumentos totales: {len(launch.command)}")
    print()
    print("Primeros argumentos JVM:")
    for arg in launch.jvm_arguments[:12]:
        print(f"  {arg}")
    print()
    print("Primeros argumentos de juego:")
    for arg in launch.game_arguments[:14]:
        if "token" in arg.lower():
            print("  <oculto>")
        else:
            print(f"  {arg}")
    print()
    print("Comando construido correctamente. No se ejecutó Minecraft.")


if __name__ == "__main__":
    main()

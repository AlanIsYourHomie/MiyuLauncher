from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.minecraft import find_minecraft_installations


def main() -> None:
    installations = find_minecraft_installations()

    if not installations:
        print("No se encontraron instalaciones estándar de Minecraft.")
        return

    print(f"Se encontraron {len(installations)} instalación(es) de Minecraft:\n")

    for index, installation in enumerate(installations, start=1):
        print(f"[{index}] {installation.root}")
        print(f"    Fuente: {installation.source}")
        print(f"    Versiones detectadas: {len(installation.versions)}")

        for version in installation.versions:
            jar_status = "sí" if version.jar_file is not None else "no"
            print(
                f"      - {version.version_id} | tipo={version.version_type or 'desconocido'} | "
                f"jar={jar_status} | inherits={version.inherits_from or '-'}"
            )

        print()


if __name__ == "__main__":
    main()

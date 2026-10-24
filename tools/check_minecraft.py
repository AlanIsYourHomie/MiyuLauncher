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
            downloadable_client = "sí" if version.client_download_url else "no"
            java_required = str(version.java_major_version) if version.java_major_version else "-"
            args_mode = (
                "modernos"
                if version.has_modern_arguments
                else "legacy"
                if version.has_legacy_arguments
                else "-"
            )

            print(f"      - {version.version_id}")
            print(f"          tipo: {version.version_type or 'desconocido'}")
            print(f"          jar local: {jar_status}")
            print(f"          cliente descargable: {downloadable_client}")
            print(f"          Java requerido: {java_required}")
            print(f"          asset index: {version.asset_index_id or '-'}")
            print(f"          librerías declaradas: {version.libraries_count}")
            print(f"          argumentos: {args_mode}")
            print(f"          main class: {version.main_class or '-'}")
            print(f"          inherits: {version.inherits_from or '-'}")

        print()


if __name__ == "__main__":
    main()

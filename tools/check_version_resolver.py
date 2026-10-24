from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.minecraft import find_default_minecraft_installation
from miyu_launcher.core.version_resolver import resolve_all_versions


def _yes_no(value: bool) -> str:
    return "sí" if value else "no"


def main() -> None:
    installation = find_default_minecraft_installation()

    if installation is None:
        print("No se encontró una instalación estándar de Minecraft.")
        return

    print(f"Instalación: {installation.root}\n")

    for resolved in resolve_all_versions(installation):
        java = resolved.java
        java_text = (
            f"Java {java.version} ({java.executable})"
            if java is not None
            else "no encontrado"
        )

        print(f"- {resolved.version.version_id}")
        print(f"    Java requerido: {resolved.required_java_major or 'desconocido'}")
        print(f"    Java seleccionado: {java_text}")
        print(f"    Java compatible: {_yes_no(resolved.java_compatible)}")
        print(f"    client jar presente: {_yes_no(resolved.client_jar_exists)}")
        print(f"    cliente descargable: {_yes_no(resolved.client_download_url is not None)}")
        print(f"    asset index: {resolved.asset_index_id or '-'}")
        print(f"    librerías declaradas: {resolved.declared_libraries}")
        print(f"    main class: {resolved.main_class or '-'}")
        print(f"    argumentos modernos: {_yes_no(resolved.uses_modern_arguments)}")
        print(f"    listo para lanzamiento local: {_yes_no(resolved.ready_for_launch)}")
        print()


if __name__ == "__main__":
    main()

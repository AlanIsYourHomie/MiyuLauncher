from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.runtime import (
    RuntimeErrorBase,
    find_managed_runtime,
    get_latest_runtime_package,
    install_managed_runtime,
)


def _format_size(size: int | None) -> str:
    if size is None:
        return "desconocido"
    return f"{size / (1024 * 1024):.1f} MB"


def _progress(downloaded: int, total: int | None) -> None:
    if total:
        percent = downloaded / total * 100
        print(
            f"\rDescargando: {downloaded / (1024 * 1024):.1f} / "
            f"{total / (1024 * 1024):.1f} MB ({percent:.1f}%)",
            end="",
            flush=True,
        )
    else:
        print(
            f"\rDescargando: {downloaded / (1024 * 1024):.1f} MB",
            end="",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba del Java Runtime Manager de MiyuLauncher.")
    parser.add_argument("java_major", nargs="?", type=int, default=25)
    parser.add_argument(
        "--install",
        action="store_true",
        help="Descarga, verifica e instala el runtime administrado.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reinstala el runtime aunque ya exista.",
    )
    args = parser.parse_args()

    try:
        existing = find_managed_runtime(args.java_major)
        if existing is not None and not args.force:
            print(f"Java {args.java_major} administrado ya está instalado.")
            print(f"Versión: {existing.installation.version}")
            print(f"Ruta: {existing.executable}")
            return

        package = get_latest_runtime_package(args.java_major)
        print(f"Runtime disponible para Java {args.java_major}:")
        print(f"  Proveedor: {package.vendor}")
        print(f"  Release: {package.release_name or '-'}")
        print(f"  Versión: {package.version or '-'}")
        print(f"  Tipo: {package.image_type}")
        print(f"  Plataforma: {package.os_name}/{package.architecture}")
        print(f"  Archivo: {package.filename}")
        print(f"  Tamaño: {_format_size(package.size)}")
        print(f"  SHA-256: {package.sha256}")

        if not args.install:
            print("\nConsulta correcta. Para instalarlo ejecuta:")
            print(f"python tools/check_runtime.py {args.java_major} --install")
            return

        print("\nInstalando runtime administrado...")
        runtime = install_managed_runtime(
            args.java_major,
            progress=_progress,
            force=args.force,
        )
        print("\n\nInstalación completada y validada.")
        print(f"Versión detectada: {runtime.installation.version}")
        print(f"Java major: {runtime.installation.major}")
        print(f"Ejecutable: {runtime.executable}")
        print(f"Directorio: {runtime.root}")
    except RuntimeErrorBase as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

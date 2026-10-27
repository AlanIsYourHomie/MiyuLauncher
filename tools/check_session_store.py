from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth.session_store import (  # noqa: E402
    clear_saved_session,
    load_session,
    save_session,
)


def main() -> int:
    if os.name != "nt":
        print("ERROR: esta prueba usa DPAPI y debe ejecutarse en Windows.")
        return 2

    dummy_token = "MIYU_DPAPI_CHECK_TOKEN_NOT_A_REAL_CREDENTIAL_2026"
    with tempfile.TemporaryDirectory(prefix="miyu-dpapi-check-") as temporary_directory:
        path = Path(temporary_directory) / "microsoft.session"
        try:
            save_session(dummy_token, "MiyuLauncherCheck", "0123456789abcdef", path=path)
            encrypted_bytes = path.read_bytes()
            if dummy_token.encode("utf-8") in encrypted_bytes:
                raise RuntimeError("El token de prueba aparece en texto claro dentro del archivo.")

            restored = load_session(path=path)
            if restored is None or restored.refresh_token != dummy_token:
                raise RuntimeError("El token ficticio no pudo recuperarse correctamente.")
            if restored.username != "MiyuLauncherCheck":
                raise RuntimeError("Los metadatos de prueba no se recuperaron correctamente.")

            clear_saved_session(path=path)
            if path.exists():
                raise RuntimeError("El archivo no se eliminó al cerrar la sesión de prueba.")
        except Exception as exc:
            print(f"ERROR: la prueba DPAPI no se completó: {exc}")
            return 1

    print("OK: DPAPI cifró y recuperó un token ficticio; el archivo no contiene el token en texto claro.")
    print("OK: la sesión de prueba se eliminó correctamente.")
    print("No se usó ni se guardó ninguna credencial real de Microsoft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

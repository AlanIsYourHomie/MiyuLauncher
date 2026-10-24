from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth.microsoft import (
    MicrosoftAuthError,
    begin_device_code,
    finish_minecraft_login,
    poll_device_code,
)


def main() -> None:
    client_id = os.environ.get("MIYU_MS_CLIENT_ID", "").strip()
    if not client_id:
        print("Falta MIYU_MS_CLIENT_ID.")
        print("MiyuLauncher necesita un Client ID propio de Microsoft Entra para probar el login oficial.")
        return

    try:
        session = begin_device_code(client_id)
        print("Inicio de sesión oficial de Microsoft iniciado.\n")
        print(session.message or f"Abre {session.verification_uri} e introduce: {session.user_code}")
        print("\nEsperando autenticación...")

        ms_token = poll_device_code(
            client_id,
            session,
            progress=lambda message: print(message),
        )
        print("Microsoft: OK")
        print("Xbox Live / XSTS / Minecraft Services: comprobando...")

        account = finish_minecraft_login(ms_token)
        print("\nAutenticación completada.")
        print(f"Jugador: {account.username}")
        print(f"UUID: {account.uuid}")
        print(f"Licencia detectada: {'sí' if account.owns_minecraft else 'no'}")
        print("El access token no se muestra ni se guarda en esta prueba.")
    except MicrosoftAuthError as exc:
        print(f"\nError de autenticación: {exc}")


if __name__ == "__main__":
    main()

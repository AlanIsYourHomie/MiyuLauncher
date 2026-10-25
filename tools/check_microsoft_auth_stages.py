from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth import microsoft


def main() -> None:
    client_id = os.environ.get("MIYU_MS_CLIENT_ID")
    if not client_id:
        print("Falta MIYU_MS_CLIENT_ID.")
        return

    try:
        print("[1/5] Microsoft device code...")
        session = microsoft.begin_device_code(client_id)
        print(session.message)
        ms_token = microsoft.poll_device_code(
            client_id,
            session,
            progress=lambda message: print(message),
        )
        print("Microsoft: OK")

        print("[2/5] Xbox Live...")
        xbl_token, _ = microsoft._xbox_live_token(ms_token.access_token)
        print("Xbox Live: OK")

        print("[3/5] XSTS...")
        xsts_token, user_hash = microsoft._xsts_token(xbl_token)
        print("XSTS: OK")

        print("[4/5] Minecraft Services login...")
        mc_token = microsoft._minecraft_token(user_hash, xsts_token)
        print("Minecraft Services login: OK")

        print("[5/5] Licencia y perfil...")
        owns = microsoft._owns_minecraft(mc_token)
        if not owns:
            print("La cuenta no reporta una licencia compatible de Minecraft.")
            return
        username, uuid = microsoft._minecraft_profile(mc_token)
        print("Minecraft: OK")
        print(f"Usuario: {username}")
        print(f"UUID: {uuid}")

    except microsoft.MicrosoftAuthError as exc:
        print(f"\nFalló la etapa actual: {exc}")
        print("No se mostraron tokens ni credenciales.")


if __name__ == "__main__":
    main()

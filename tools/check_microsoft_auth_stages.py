from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth import microsoft


XSTS_ERRORS = {
    2148916227: "La cuenta está bloqueada o suspendida en Xbox Live.",
    2148916233: "La cuenta Microsoft todavía no tiene un perfil/cuenta de Xbox Live.",
    2148916235: "Xbox Live no está disponible para la región configurada en la cuenta.",
    2148916236: "La cuenta requiere verificación de adulto en Xbox.",
    2148916237: "La cuenta requiere verificación de adulto en Xbox.",
    2148916238: "La cuenta está clasificada como menor y XSTS exige configuración familiar/autorización de adulto para esta aplicación.",
    2148916262: "XSTS rechazó la cuenta por una condición no documentada con detalle.",
}


def diagnose_xsts(xbl_token: str) -> None:
    body = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [xbl_token],
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT",
    }
    request = urllib.request.Request(
        microsoft.XSTS_AUTH_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "User-Agent": microsoft.USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30):
            print("XSTS respondió correctamente en el diagnóstico.")
            return
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}

        xerr = payload.get("XErr") if isinstance(payload, dict) else None
        redirect = payload.get("Redirect") if isinstance(payload, dict) else None

        print(f"HTTP XSTS: {exc.code}")
        if isinstance(xerr, int):
            print(f"XErr: {xerr}")
            print(f"Significado: {XSTS_ERRORS.get(xerr, 'Código XSTS no reconocido por el diagnóstico.')}")
        else:
            print("XErr: no disponible")
        if isinstance(redirect, str) and redirect:
            print("XSTS también devolvió una URL de ayuda/configuración de cuenta.")
        return
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"No se pudo completar el diagnóstico XSTS: {exc}")


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
        try:
            xsts_token, user_hash = microsoft._xsts_token(xbl_token)
        except microsoft.MicrosoftAuthError:
            print("XSTS: ERROR")
            diagnose_xsts(xbl_token)
            print("No se mostraron tokens ni credenciales.")
            return
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

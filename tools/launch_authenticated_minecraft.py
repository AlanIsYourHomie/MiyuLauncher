from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth import microsoft
from miyu_launcher.core.assets import install_missing_assets
from miyu_launcher.core.launch_command import LaunchProfile, build_launch_command
from miyu_launcher.core.libraries import resolve_libraries
from miyu_launcher.core.minecraft import find_default_minecraft_installation
from miyu_launcher.core.minecraft_installer import install_version_dependencies
from miyu_launcher.core.natives import extract_natives


def get_xuid(ms_access_token: str) -> str:
    """Fetch the Xbox XUID via XSTS for the Xbox Live relying party; never print tokens."""
    headers = {
        "User-Agent": microsoft.USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Exchange the Microsoft access token for an Xbox Live token.
    xbl_body = {
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"d={ms_access_token}",
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    }
    xbl_request = urllib.request.Request(
        microsoft.XBL_AUTH_URL,
        data=json.dumps(xbl_body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(xbl_request, timeout=30) as response:
            xbl_payload = json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se pudo autenticar con Xbox Live para obtener el XUID: {exc}") from exc

    xbl_token = xbl_payload.get("Token")
    if not isinstance(xbl_token, str) or not xbl_token:
        raise RuntimeError("Xbox Live no devolvió un token válido para consultar el XUID.")

    # The XUID is not reliably present in the initial Xbox Live response.
    # Request XSTS for Xbox Live and read xid from the returned claims.
    xsts_body = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [xbl_token],
        },
        "RelyingParty": "http://xboxlive.com",
        "TokenType": "JWT",
    }
    xsts_request = urllib.request.Request(
        microsoft.XSTS_AUTH_URL,
        data=json.dumps(xsts_body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(xsts_request, timeout=30) as response:
            xsts_payload = json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se pudo obtener el perfil XSTS de Xbox Live: {exc}") from exc

    try:
        claim = xsts_payload["DisplayClaims"]["xui"][0]
        xuid = claim.get("xid") or claim.get("xuid")
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Xbox Live no incluyó el XUID en los claims de XSTS.") from exc

    if not isinstance(xuid, str) or not xuid.strip():
        raise RuntimeError("Xbox Live no devolvió un XUID válido en la respuesta XSTS.")
    return xuid



def main() -> int:
    version_id = sys.argv[1] if len(sys.argv) > 1 else "26.3"
    client_id = os.environ.get("MIYU_MS_CLIENT_ID", "").strip()
    if not client_id:
        print("Falta MIYU_MS_CLIENT_ID.")
        print("En CMD ejecuta: set MIYU_MS_CLIENT_ID=2c405b6a-a357-4083-811e-f0da479e759d")
        return 2

    installation = find_default_minecraft_installation()
    if installation is None:
        print("No se encontró una instalación estándar de Minecraft.")
        return 2

    version = next((item for item in installation.versions if item.version_id == version_id), None)
    if version is None:
        print(f"No se encontró la versión {version_id} en {installation.root}.")
        print("Usa python tools\\check_minecraft.py para ver las versiones detectadas.")
        return 2

    try:
        print(f"Preparando Minecraft {version_id}...")
        plan = install_version_dependencies(
            installation,
            version,
            progress=lambda index, total, task: print(f"Descarga [{index}/{total}]: {task.label}"),
        )
        if plan.total_files:
            print(f"Dependencias verificadas/instaladas: {plan.total_files} archivo(s).")

        libraries = resolve_libraries(installation, version)
        if not libraries.ready:
            print(f"Siguen faltando {len(libraries.missing_required)} librerías; no se lanzará el juego.")
            for item in libraries.missing_required[:10]:
                print(f"  - {item.name}")
            return 1
        if not version.jar_file or not version.jar_file.is_file():
            print(f"Falta el client JAR de Minecraft {version_id}.")
            return 1

        print("Comprobando assets...")
        assets = install_missing_assets(
            installation,
            version,
            progress=lambda done, total, name: print(f"Assets: {done}/{total} ({name})")
            if total and (done == 0 or done == total or done % 100 == 0)
            else None,
        )
        if not assets.ready:
            print(f"Quedaron {len(assets.missing)} assets sin instalar; no se lanzará el juego.")
            return 1

        print("Extrayendo bibliotecas nativas...")
        native_result = extract_natives(installation, version, libraries)
        if not native_result.extracted_files:
            print("Aviso: no se extrajeron archivos nativos; el juego podría fallar al arrancar.")

        print("Inicia sesión con la cuenta Microsoft que tiene Minecraft: Java Edition.")
        device_session = microsoft.begin_device_code(client_id)
        print(device_session.message or f"Abre {device_session.verification_uri} e introduce {device_session.user_code}.")
        ms_token = microsoft.poll_device_code(
            client_id,
            device_session,
            progress=lambda message: print(message),
        )
        print("Microsoft: OK")

        print("Verificando Xbox Live, XSTS, Minecraft Services y la licencia...")
        account = microsoft.finish_minecraft_login(ms_token)
        print(f"Cuenta verificada: {account.username}")
        print(f"UUID: {account.uuid}")
        print("Licencia: OK")

        xuid = get_xuid(ms_token.access_token)
        profile = LaunchProfile(
            username=account.username,
            uuid=account.uuid,
            access_token=account.access_token,
            user_type="msa",
            xuid=xuid,
            # This argument identifies the launcher installation for game telemetry;
            # it is not an OAuth secret. Generate a per-installation value for this test.
            client_id=str(uuid.uuid4()),
        )
        launch = build_launch_command(
            installation,
            version,
            profile=profile,
            game_directory=installation.root,
        )

        print(f"Lanzando Minecraft {version_id} con {launch.executable}...")
        print("Los tokens no se mostrarán ni se guardarán en archivos.")
        process = subprocess.Popen(list(launch.command), cwd=str(installation.root))
        print(f"Proceso iniciado (PID {process.pid}).")
        print("Si el juego falla al iniciar, conserva esta ventana de CMD y comparte el error sin tokens.")
        return 0

    except (microsoft.MicrosoftAuthError, RuntimeError, ValueError, OSError) as exc:
        print(f"No se pudo lanzar Minecraft: {exc}")
        print("No se mostraron ni guardaron tokens o contraseñas.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

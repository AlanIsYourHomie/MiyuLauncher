from __future__ import annotations

import os
import subprocess
import uuid
from threading import Event
from typing import Callable

from miyu_launcher.auth import microsoft
from miyu_launcher.auth.session_store import (
    SessionStoreError,
    clear_saved_session,
    load_session,
    save_session,
)
from miyu_launcher.auth.token_refresh import refresh_microsoft_token
from miyu_launcher.core.assets import install_missing_assets
from miyu_launcher.core.launch_command import LaunchProfile, build_launch_command
from miyu_launcher.core.libraries import resolve_libraries
from miyu_launcher.core.minecraft import MinecraftInstallation, MinecraftVersion, find_default_minecraft_installation
from miyu_launcher.core.minecraft_installer import install_version_dependencies
from miyu_launcher.core.natives import extract_natives
from miyu_launcher.core.runtime import install_managed_runtime
from miyu_launcher.core.version_resolver import resolve_version


# A native desktop app uses a public client ID. This is not a client secret.
# MIYU_MS_CLIENT_ID remains as an optional local override for development.
DEFAULT_MICROSOFT_CLIENT_ID = "2c405b6a-a357-4083-811e-f0da479e759d"
ProgressCallback = Callable[[str], None]
AuthenticationCodeCallback = Callable[[str, str, str], None]


class LaunchCancelled(RuntimeError):
    """Raised when the user cancels a launch before Minecraft starts."""


def _check_cancelled(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise LaunchCancelled("El lanzamiento fue cancelado.")


def _report(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)


_AUTH_ERRORS_REQUIRING_INTERACTIVE_LOGIN = {
    "invalid_grant",
    "interaction_required",
    "login_required",
    "consent_required",
    "invalid_token",
    "expired_token",
}


def _start_interactive_login(
    client_id: str,
    *,
    progress: ProgressCallback | None,
    authentication_code: AuthenticationCodeCallback | None,
    cancel_event: Event | None,
) -> microsoft.MicrosoftToken:
    """Run device-code login when no usable saved session is available."""
    _check_cancelled(cancel_event)
    _report(progress, "Solicitando inicio de sesión de Microsoft...")
    device_session = microsoft.begin_device_code(client_id)
    _check_cancelled(cancel_event)
    if authentication_code is not None:
        authentication_code(
            device_session.verification_uri,
            device_session.user_code,
            device_session.message,
        )
    else:
        _report(
            progress,
            device_session.message
            or f"Abre {device_session.verification_uri} e introduce el código {device_session.user_code}.",
        )

    def authentication_progress(message: str) -> None:
        _check_cancelled(cancel_event)
        _report(progress, message)

    token = microsoft.poll_device_code(
        client_id,
        device_session,
        progress=authentication_progress,
    )
    _check_cancelled(cancel_event)
    _report(progress, "Microsoft: cuenta verificada.")
    return token


def _discard_saved_session(progress: ProgressCallback | None) -> None:
    try:
        clear_saved_session()
    except SessionStoreError:
        # Interactive login can proceed; the old file remains encrypted.
        _report(progress, "Aviso: no se pudo eliminar el archivo de sesión anterior.")


def _save_verified_session(
    token: microsoft.MicrosoftToken,
    account: microsoft.MinecraftAccount,
    progress: ProgressCallback | None,
) -> None:
    if not token.refresh_token:
        _report(
            progress,
            "Microsoft no entregó un token de renovación; la próxima vez podría pedirte iniciar sesión.",
        )
        return
    try:
        save_session(token.refresh_token, account.username, account.uuid)
    except SessionStoreError:
        _report(
            progress,
            "Aviso: no se pudo guardar la sesión de forma segura. Minecraft puede abrirse, "
            "pero quizá debas iniciar sesión la próxima vez.",
        )
    else:
        _report(progress, f"Sesión segura guardada para {account.username}.")


def _get_xuid(ms_access_token: str) -> str:
    """Get the Xbox XUID using XSTS with the Xbox Live relying party."""
    # The XBL authentication response is primarily used to obtain the user hash.
    # The XUID is exposed by an XSTS token requested for http://xboxlive.com.
    xbl_token, _user_hash = microsoft._xbox_live_token(ms_access_token)
    payload = microsoft._request_json(
        microsoft.XSTS_AUTH_URL,
        method="POST",
        body={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token],
            },
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
        },
    )

    try:
        claims = payload["DisplayClaims"]["xui"][0]
        xuid = claims.get("xid") or claims.get("xuid")
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "XSTS no devolvió un identificador XUID válido para Xbox Live."
        ) from exc

    if isinstance(xuid, int):
        xuid = str(xuid)
    if not isinstance(xuid, str) or not xuid.strip():
        raise RuntimeError("XSTS no devolvió un identificador XUID válido para Xbox Live.")
    return xuid


def _find_version(
    installation: MinecraftInstallation,
    version_id: str,
) -> MinecraftVersion:
    version = next(
        (item for item in installation.versions if item.version_id == version_id),
        None,
    )
    if version is None:
        raise RuntimeError(
            f"No se encontró la versión {version_id} en la instalación de Minecraft."
        )
    if not version.has_modern_arguments:
        raise RuntimeError(
            f"La versión {version_id} usa un formato de argumentos que MiyuLauncher todavía no admite."
        )
    return version


def launch_minecraft(
    version_id: str,
    *,
    progress: ProgressCallback | None = None,
    authentication_code: AuthenticationCodeCallback | None = None,
    cancel_event: Event | None = None,
) -> subprocess.Popen:
    """Prepare, authenticate, and launch an installed Minecraft Java version.

    This function is intentionally independent of PySide6. The UI calls it from
    a QThread and forwards its progress callbacks to the main window.
    """
    client_id = os.environ.get("MIYU_MS_CLIENT_ID", "").strip() or DEFAULT_MICROSOFT_CLIENT_ID
    _check_cancelled(cancel_event)
    if not client_id:
        raise RuntimeError(
            "Falta el identificador de la aplicación Microsoft. Revisa MIYU_MS_CLIENT_ID."
        )

    _report(progress, "Buscando la instalación de Minecraft...")
    installation = find_default_minecraft_installation()
    if installation is None:
        raise RuntimeError(
            "No se encontró Minecraft en la carpeta estándar de Windows (%APPDATA%\\.minecraft)."
        )
    version = _find_version(installation, version_id)
    _check_cancelled(cancel_event)

    # Ensure the Java major version required by this Minecraft version is available.
    resolved = resolve_version(installation, version)
    required_java = resolved.required_java_major
    if required_java is not None and not resolved.java_compatible:
        _report(progress, f"Preparando Java {required_java} para Minecraft {version_id}...")

        def runtime_progress(downloaded: int, total: int | None) -> None:
            if total and total > 0:
                percentage = min(100, int(downloaded * 100 / total))
                _report(progress, f"Descargando Java {required_java}: {percentage}%")
            else:
                _report(progress, f"Descargando Java {required_java}...")

        install_managed_runtime(required_java, progress=runtime_progress)
        _check_cancelled(cancel_event)
        resolved = resolve_version(installation, version)
        if not resolved.java_compatible:
            raise RuntimeError(
                f"No se pudo preparar un Java {required_java} compatible con Minecraft {version_id}."
            )
    elif resolved.java is not None and resolved.java_compatible:
        _report(progress, f"Java {resolved.java.version or ''} está listo.")

    _report(progress, f"Comprobando bibliotecas de Minecraft {version_id}...")
    def dependency_progress(index: int, total: int, task: object) -> None:
        _check_cancelled(cancel_event)
        label = getattr(task, "label", "archivo")
        _report(progress, f"Preparando archivos ({index}/{total}): {label}")

    install_plan = install_version_dependencies(
        installation,
        version,
        progress=dependency_progress,
    )
    _check_cancelled(cancel_event)
    if install_plan.total_files:
        _report(progress, f"Archivos comprobados: {install_plan.total_files}.")

    libraries = resolve_libraries(installation, version)
    if not libraries.ready:
        missing = ", ".join(item.name for item in libraries.missing_required[:5])
        raise RuntimeError(f"Faltan bibliotecas necesarias para Minecraft: {missing}")

    client_jar = version.directory / f"{version.version_id}.jar"
    if not client_jar.is_file():
        raise RuntimeError(f"No se encontró el archivo principal de Minecraft {version_id}.")

    _report(progress, "Comprobando recursos del juego...")
    def assets_progress(done: int, total: int | None, name: str) -> None:
        _check_cancelled(cancel_event)
        if total and (done == 0 or done == total or done % 100 == 0):
            _report(progress, f"Comprobando recursos: {done}/{total}")

    assets = install_missing_assets(installation, version, progress=assets_progress)
    _check_cancelled(cancel_event)
    if not assets.ready:
        raise RuntimeError(
            f"No se pudieron preparar todos los recursos de Minecraft ({len(assets.missing)} pendientes)."
        )

    _report(progress, "Preparando bibliotecas nativas...")
    natives = extract_natives(installation, version, libraries)
    _check_cancelled(cancel_event)
    if not natives.extracted_files:
        _report(progress, "Aviso: Minecraft no reportó bibliotecas nativas extraídas; se intentará iniciar igualmente.")

    # Prefer a saved refresh token. Only invalid/revoked-token responses trigger
    # an interactive sign-in; network/service failures are surfaced instead of
    # unexpectedly opening the browser.
    _report(progress, "Comprobando si existe una sesión Microsoft guardada...")
    try:
        stored_session = load_session()
    except SessionStoreError:
        _report(
            progress,
            "No se pudo recuperar la sesión cifrada. Se solicitará iniciar sesión de nuevo.",
        )
        _discard_saved_session(progress)
        stored_session = None

    if stored_session is not None:
        _report(progress, f"Renovando la sesión guardada de {stored_session.username}...")
        try:
            ms_token = refresh_microsoft_token(client_id, stored_session.refresh_token)
        except microsoft.MicrosoftAuthError as exc:
            if exc.error_code not in _AUTH_ERRORS_REQUIRING_INTERACTIVE_LOGIN:
                raise RuntimeError(
                    "No se pudo renovar la sesión Microsoft. Comprueba tu conexión e inténtalo de nuevo. "
                    "No se abrirá el navegador automáticamente ante un posible fallo de red."
                ) from exc
            _report(
                progress,
                "La sesión guardada caducó o fue revocada. Hace falta iniciar sesión de nuevo.",
            )
            _discard_saved_session(progress)
            ms_token = _start_interactive_login(
                client_id,
                progress=progress,
                authentication_code=authentication_code,
                cancel_event=cancel_event,
            )
        else:
            # Persist a rotated refresh token immediately, before contacting
            # Xbox/Minecraft, so a later downstream failure does not lose it.
            if ms_token.refresh_token:
                try:
                    save_session(
                        ms_token.refresh_token,
                        stored_session.username,
                        stored_session.uuid,
                    )
                except SessionStoreError:
                    _report(
                        progress,
                        "Aviso: no se pudo actualizar el archivo de sesión segura. "
                        "La renovación funcionó, pero quizá debas iniciar sesión de nuevo más adelante.",
                    )
            _report(progress, "Sesión Microsoft renovada sin abrir el navegador.")
    else:
        ms_token = _start_interactive_login(
            client_id,
            progress=progress,
            authentication_code=authentication_code,
            cancel_event=cancel_event,
        )

    _check_cancelled(cancel_event)
    _report(progress, "Verificando Xbox Live, XSTS y la licencia de Minecraft...")
    account = microsoft.finish_minecraft_login(ms_token)
    _check_cancelled(cancel_event)
    if not account.owns_minecraft:
        raise microsoft.MicrosoftAuthError(
            "La cuenta Microsoft no tiene una licencia válida de Minecraft: Java Edition."
        )
    _report(progress, f"Cuenta verificada: {account.username} · licencia válida.")
    _save_verified_session(ms_token, account, progress)

    xuid = _get_xuid(ms_token.access_token)
    _check_cancelled(cancel_event)
    profile = LaunchProfile(
        username=account.username,
        uuid=account.uuid,
        access_token=account.access_token,
        user_type="msa",
        xuid=xuid,
        client_id=str(uuid.uuid4()),
    )

    # The test launcher uses the standard .minecraft root for compatibility.
    # A dedicated MiyuLauncher instance will be introduced in a later phase.
    launch = build_launch_command(
        installation,
        version,
        profile=profile,
        game_directory=installation.root,
    )

    _check_cancelled(cancel_event)
    _report(progress, f"Iniciando Minecraft {version_id}...")
    try:
        process = subprocess.Popen(list(launch.command), cwd=str(installation.root))
    except OSError as exc:
        raise RuntimeError(f"No se pudo ejecutar Java para Minecraft {version_id}: {exc}") from exc

    _report(
        progress,
        f"Minecraft se inició (PID {process.pid}). Los tokens de acceso no se guardan en texto claro.",
    )
    return process

from __future__ import annotations

import ctypes
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from miyu_launcher.core.paths import get_launcher_paths


_FILE_MAGIC = b"MIYU-DPAPI-SESSION-V1\n"
_CRYPTPROTECT_UI_FORBIDDEN = 0x1


class SessionStoreError(RuntimeError):
    """Raised when MiyuLauncher cannot safely read or write a saved session."""


@dataclass(frozen=True)
class StoredSession:
    refresh_token: str
    username: str
    uuid: str
    saved_at: str


def session_file_path(path: Path | None = None) -> Path:
    """Return the local encrypted-session path (never a plaintext token path)."""
    if path is not None:
        return Path(path)
    return get_launcher_paths().root / "auth" / "microsoft.session"


def has_saved_session_file(path: Path | None = None) -> bool:
    try:
        return session_file_path(path).is_file()
    except OSError:
        return False


def _dpapi_transform(data: bytes, *, encrypt: bool) -> bytes:
    """Protect/unprotect bytes with current-user Windows DPAPI.

    The LOCAL_MACHINE flag is deliberately not used: the session should be
    decryptable only under the Windows user profile that saved it.
    """
    if os.name != "nt":
        raise SessionStoreError(
            "El almacenamiento seguro de sesiones está disponible en Windows mediante DPAPI."
        )

    try:
        from ctypes import wintypes

        class DataBlob(ctypes.Structure):
            _fields_ = [
                ("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
            ]

        crypt32 = ctypes.WinDLL("crypt32.dll", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

        input_buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        input_blob = DataBlob(
            len(data),
            ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)),
        )
        output_blob = DataBlob()

        if encrypt:
            function = crypt32.CryptProtectData
            function.argtypes = [
                ctypes.POINTER(DataBlob),
                wintypes.LPCWSTR,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.POINTER(DataBlob),
            ]
            function.restype = wintypes.BOOL
            ok = function(
                ctypes.byref(input_blob),
                "MiyuLauncher Microsoft session",
                None,
                None,
                None,
                _CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(output_blob),
            )
        else:
            description = wintypes.LPWSTR()
            function = crypt32.CryptUnprotectData
            function.argtypes = [
                ctypes.POINTER(DataBlob),
                ctypes.POINTER(wintypes.LPWSTR),
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.POINTER(DataBlob),
            ]
            function.restype = wintypes.BOOL
            ok = function(
                ctypes.byref(input_blob),
                ctypes.byref(description),
                None,
                None,
                None,
                _CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(output_blob),
            )

        if not ok:
            error_code = ctypes.get_last_error()
            raise OSError(error_code, "Windows DPAPI no pudo procesar la sesión guardada.")

        try:
            return ctypes.string_at(output_blob.pbData, output_blob.cbData)
        finally:
            kernel32.LocalFree.argtypes = [ctypes.c_void_p]
            kernel32.LocalFree.restype = ctypes.c_void_p
            if output_blob.pbData:
                kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))
            if not encrypt and description:
                kernel32.LocalFree(ctypes.cast(description, ctypes.c_void_p))

    except SessionStoreError:
        raise
    except Exception as exc:
        action = "cifrar" if encrypt else "descifrar"
        raise SessionStoreError(
            f"Windows no pudo {action} la sesión guardada. Puede que el archivo esté dañado "
            "o que haya cambiado el perfil de Windows."
        ) from exc


def _protect_data(data: bytes) -> bytes:
    return _dpapi_transform(data, encrypt=True)


def _unprotect_data(data: bytes) -> bytes:
    return _dpapi_transform(data, encrypt=False)


def save_session(
    refresh_token: str,
    username: str,
    uuid: str,
    *,
    path: Path | None = None,
) -> StoredSession:
    """Encrypt and atomically persist the Microsoft refresh token and account label."""
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise SessionStoreError("Microsoft no proporcionó un token de renovación válido.")
    if not isinstance(username, str) or not username.strip():
        raise SessionStoreError("No se puede guardar una sesión sin nombre de perfil.")
    if not isinstance(uuid, str) or not uuid.strip():
        raise SessionStoreError("No se puede guardar una sesión sin UUID de Minecraft.")

    saved_at = datetime.now(timezone.utc).isoformat()
    session = StoredSession(
        refresh_token=refresh_token,
        username=username,
        uuid=uuid,
        saved_at=saved_at,
    )
    payload = json.dumps(
        {
            "schema_version": 1,
            "refresh_token": session.refresh_token,
            "username": session.username,
            "uuid": session.uuid,
            "saved_at": session.saved_at,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    encrypted = _FILE_MAGIC + _protect_data(payload)

    destination = session_file_path(path)
    temporary_name: str | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".miyu-session-",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(encrypted)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, destination)
    except OSError as exc:
        raise SessionStoreError(
            "No se pudo guardar la sesión cifrada en la carpeta de MiyuLauncher."
        ) from exc
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass

    return session


def load_session(*, path: Path | None = None) -> StoredSession | None:
    """Load the encrypted session; return None if no saved session exists."""
    source = session_file_path(path)
    try:
        encrypted = source.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise SessionStoreError("No se pudo leer el archivo de sesión de MiyuLauncher.") from exc

    if not encrypted.startswith(_FILE_MAGIC):
        raise SessionStoreError(
            "El archivo de sesión no tiene el formato cifrado esperado. Puedes eliminarlo e iniciar sesión de nuevo."
        )

    try:
        payload = _unprotect_data(encrypted[len(_FILE_MAGIC) :])
        data = json.loads(payload.decode("utf-8"))
    except SessionStoreError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SessionStoreError(
            "La sesión guardada está dañada o no se puede interpretar."
        ) from exc

    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise SessionStoreError("La versión del archivo de sesión no es compatible.")

    refresh_token = data.get("refresh_token")
    username = data.get("username")
    player_uuid = data.get("uuid")
    saved_at = data.get("saved_at")
    if not all(isinstance(value, str) and value.strip() for value in (refresh_token, username, player_uuid)):
        raise SessionStoreError("La sesión guardada está incompleta. Inicia sesión de nuevo.")
    if not isinstance(saved_at, str):
        saved_at = ""

    return StoredSession(
        refresh_token=refresh_token,
        username=username,
        uuid=player_uuid,
        saved_at=saved_at,
    )


def clear_saved_session(*, path: Path | None = None) -> None:
    """Delete the local encrypted session. This does not revoke tokens server-side."""
    destination = session_file_path(path)
    try:
        destination.unlink(missing_ok=True)
    except OSError as exc:
        raise SessionStoreError("No se pudo eliminar la sesión guardada localmente.") from exc

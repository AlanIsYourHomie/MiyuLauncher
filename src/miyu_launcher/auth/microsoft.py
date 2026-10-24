from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable


MS_DEVICE_CODE_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
MS_TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
XBL_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_LOGIN_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"
MC_ENTITLEMENTS_URL = "https://api.minecraftservices.com/entitlements/mcstore"
SCOPES = "XboxLive.signin offline_access"
USER_AGENT = "MiyuLauncher/0.1.0-dev"


class MicrosoftAuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeviceCodeSession:
    device_code: str
    user_code: str
    verification_uri: str
    message: str
    expires_in: int
    interval: int


@dataclass(frozen=True)
class MicrosoftToken:
    access_token: str
    refresh_token: str | None
    expires_in: int | None


@dataclass(frozen=True)
class MinecraftAccount:
    username: str
    uuid: str
    access_token: str
    owns_minecraft: bool


ProgressCallback = Callable[[str], None]


def _request_json(
    url: str,
    *,
    method: str = "GET",
    form: dict[str, str] | None = None,
    body: dict | None = None,
    bearer: str | None = None,
) -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    data: bytes | None = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            details = json.loads(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            details = {"message": str(exc)}
        message = details.get("error_description") or details.get("Message") or details.get("message") or str(exc)
        raise MicrosoftAuthError(f"HTTP {exc.code}: {message}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise MicrosoftAuthError(f"Error de red/autenticación: {exc}") from exc

    if not isinstance(payload, dict):
        raise MicrosoftAuthError("La respuesta de autenticación no tiene el formato esperado.")
    return payload


def begin_device_code(client_id: str) -> DeviceCodeSession:
    payload = _request_json(
        MS_DEVICE_CODE_URL,
        method="POST",
        form={"client_id": client_id, "scope": SCOPES},
    )

    try:
        return DeviceCodeSession(
            device_code=str(payload["device_code"]),
            user_code=str(payload["user_code"]),
            verification_uri=str(payload.get("verification_uri") or payload.get("verification_url")),
            message=str(payload.get("message") or ""),
            expires_in=int(payload.get("expires_in", 900)),
            interval=max(1, int(payload.get("interval", 5))),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MicrosoftAuthError("Microsoft no devolvió un código de dispositivo válido.") from exc


def poll_device_code(
    client_id: str,
    session: DeviceCodeSession,
    *,
    progress: ProgressCallback | None = None,
) -> MicrosoftToken:
    deadline = time.monotonic() + session.expires_in
    interval = session.interval

    while time.monotonic() < deadline:
        try:
            payload = _request_json(
                MS_TOKEN_URL,
                method="POST",
                form={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": client_id,
                    "device_code": session.device_code,
                },
            )
        except MicrosoftAuthError as exc:
            text = str(exc)
            if "authorization_pending" in text:
                if progress:
                    progress("Esperando que completes el inicio de sesión en Microsoft...")
                time.sleep(interval)
                continue
            if "slow_down" in text:
                interval += 5
                time.sleep(interval)
                continue
            if "authorization_declined" in text:
                raise MicrosoftAuthError("El inicio de sesión fue cancelado por el usuario.") from exc
            if "expired_token" in text:
                raise MicrosoftAuthError("El código de inicio de sesión expiró.") from exc
            raise

        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise MicrosoftAuthError("Microsoft no devolvió un access token válido.")

        refresh = payload.get("refresh_token")
        return MicrosoftToken(
            access_token=token,
            refresh_token=refresh if isinstance(refresh, str) else None,
            expires_in=payload.get("expires_in") if isinstance(payload.get("expires_in"), int) else None,
        )

    raise MicrosoftAuthError("El código de inicio de sesión expiró.")


def _xbox_live_token(ms_access_token: str) -> tuple[str, str]:
    payload = _request_json(
        XBL_AUTH_URL,
        method="POST",
        body={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={ms_access_token}",
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
        },
    )

    token = payload.get("Token")
    claims = payload.get("DisplayClaims")
    try:
        user_hash = claims["xui"][0]["uhs"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MicrosoftAuthError("Xbox Live no devolvió el user hash esperado.") from exc

    if not isinstance(token, str) or not isinstance(user_hash, str):
        raise MicrosoftAuthError("Xbox Live devolvió datos de autenticación inválidos.")
    return token, user_hash


def _xsts_token(xbl_token: str) -> tuple[str, str]:
    payload = _request_json(
        XSTS_AUTH_URL,
        method="POST",
        body={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token],
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT",
        },
    )

    token = payload.get("Token")
    claims = payload.get("DisplayClaims")
    try:
        user_hash = claims["xui"][0]["uhs"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MicrosoftAuthError("XSTS no devolvió el user hash esperado.") from exc

    if not isinstance(token, str) or not isinstance(user_hash, str):
        raise MicrosoftAuthError("XSTS devolvió datos de autenticación inválidos.")
    return token, user_hash


def _minecraft_token(user_hash: str, xsts_token: str) -> str:
    payload = _request_json(
        MC_LOGIN_URL,
        method="POST",
        body={"identityToken": f"XBL3.0 x={user_hash};{xsts_token}"},
    )
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise MicrosoftAuthError("Minecraft Services no devolvió un access token válido.")
    return token


def _owns_minecraft(mc_access_token: str) -> bool:
    payload = _request_json(MC_ENTITLEMENTS_URL, bearer=mc_access_token)
    items = payload.get("items")
    return isinstance(items, list) and len(items) > 0


def _minecraft_profile(mc_access_token: str) -> tuple[str, str]:
    payload = _request_json(MC_PROFILE_URL, bearer=mc_access_token)
    username = payload.get("name")
    uuid = payload.get("id")
    if not isinstance(username, str) or not username or not isinstance(uuid, str) or not uuid:
        raise MicrosoftAuthError("No se pudo obtener el perfil de Minecraft Java.")
    return username, uuid


def finish_minecraft_login(ms_token: MicrosoftToken) -> MinecraftAccount:
    xbl_token, _ = _xbox_live_token(ms_token.access_token)
    xsts_token, user_hash = _xsts_token(xbl_token)
    mc_access_token = _minecraft_token(user_hash, xsts_token)
    owns = _owns_minecraft(mc_access_token)
    if not owns:
        raise MicrosoftAuthError("La cuenta no reporta una licencia de Minecraft compatible.")
    username, uuid = _minecraft_profile(mc_access_token)
    return MinecraftAccount(
        username=username,
        uuid=uuid,
        access_token=mc_access_token,
        owns_minecraft=True,
    )


def login_with_device_code(
    client_id: str,
    *,
    progress: ProgressCallback | None = None,
) -> tuple[DeviceCodeSession, MicrosoftToken, MinecraftAccount]:
    session = begin_device_code(client_id)
    ms_token = poll_device_code(client_id, session, progress=progress)
    account = finish_minecraft_login(ms_token)
    return session, ms_token, account

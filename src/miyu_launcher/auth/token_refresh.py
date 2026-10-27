from __future__ import annotations

from miyu_launcher.auth.microsoft import (
    MS_TOKEN_URL,
    SCOPES,
    MicrosoftAuthError,
    MicrosoftToken,
    _request_json,
)


def refresh_microsoft_token(client_id: str, refresh_token: str) -> MicrosoftToken:
    """Exchange a saved Microsoft refresh token for a fresh token set.

    The current refresh token is preserved if the response does not include a
    replacement. When Microsoft returns a replacement, the caller should save
    it immediately, because it is the token that should be used subsequently.
    """
    if not client_id.strip():
        raise MicrosoftAuthError("Falta el identificador de la aplicación Microsoft.")
    if not refresh_token.strip():
        raise MicrosoftAuthError("No existe un token de renovación de Microsoft válido.")

    payload = _request_json(
        MS_TOKEN_URL,
        method="POST",
        form={
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": SCOPES,
        },
    )

    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise MicrosoftAuthError("Microsoft no devolvió un access token válido al renovar la sesión.")

    replacement = payload.get("refresh_token")
    if not isinstance(replacement, str) or not replacement:
        replacement = refresh_token

    expires_in = payload.get("expires_in")
    if isinstance(expires_in, str) and expires_in.isdigit():
        expires_in = int(expires_in)
    if not isinstance(expires_in, int):
        expires_in = None

    return MicrosoftToken(
        access_token=access_token,
        refresh_token=replacement,
        expires_in=expires_in,
    )

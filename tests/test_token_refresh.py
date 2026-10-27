from __future__ import annotations

import unittest
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth import token_refresh
from miyu_launcher.auth.microsoft import MicrosoftAuthError


class TokenRefreshTests(unittest.TestCase):
    def test_uses_replacement_refresh_token_from_microsoft(self) -> None:
        with patch.object(token_refresh, "_request_json", return_value={
            "access_token": "new-access",
            "refresh_token": "rotated-refresh",
            "expires_in": 3600,
        }) as request:
            result = token_refresh.refresh_microsoft_token("public-client-id", "old-refresh")

        self.assertEqual(result.access_token, "new-access")
        self.assertEqual(result.refresh_token, "rotated-refresh")
        self.assertEqual(result.expires_in, 3600)
        request.assert_called_once()
        form = request.call_args.kwargs["form"]
        self.assertEqual(form["grant_type"], "refresh_token")
        self.assertEqual(form["refresh_token"], "old-refresh")
        self.assertNotIn("client_secret", form)

    def test_preserves_old_refresh_token_if_microsoft_does_not_return_a_replacement(self) -> None:
        with patch.object(token_refresh, "_request_json", return_value={"access_token": "new-access"}):
            result = token_refresh.refresh_microsoft_token("public-client-id", "old-refresh")
        self.assertEqual(result.refresh_token, "old-refresh")

    def test_missing_access_token_is_rejected(self) -> None:
        with patch.object(token_refresh, "_request_json", return_value={"refresh_token": "new-refresh"}):
            with self.assertRaises(MicrosoftAuthError):
                token_refresh.refresh_microsoft_token("public-client-id", "old-refresh")


if __name__ == "__main__":
    unittest.main()

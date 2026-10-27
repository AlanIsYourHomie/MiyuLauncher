from __future__ import annotations

import base64
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.auth import session_store


class SessionStoreTests(unittest.TestCase):
    def test_save_is_atomic_format_and_round_trips_without_plaintext_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "auth" / "session.bin"
            token = "example-refresh-token-that-must-not-be-plaintext"
            # Test-only reversible transform. Production code calls Windows DPAPI.
            with patch.object(session_store, "_protect_data", side_effect=base64.b64encode), patch.object(
                session_store, "_unprotect_data", side_effect=base64.b64decode
            ):
                saved = session_store.save_session(token, "PlayerTest", "0123456789abcdef", path=path)
                encrypted_file = path.read_bytes()
                self.assertNotIn(token.encode("utf-8"), encrypted_file)
                self.assertEqual(saved.username, "PlayerTest")

                loaded = session_store.load_session(path=path)
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(loaded.refresh_token, token)
                self.assertEqual(loaded.username, "PlayerTest")
                self.assertEqual(loaded.uuid, "0123456789abcdef")

                session_store.clear_saved_session(path=path)
                self.assertFalse(path.exists())
                self.assertIsNone(session_store.load_session(path=path))

    def test_no_file_means_no_saved_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missing.session"
            self.assertIsNone(session_store.load_session(path=path))

    def test_invalid_plaintext_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "session.bin"
            path.write_text('{"refresh_token":"should-not-be-accepted"}', encoding="utf-8")
            with self.assertRaises(session_store.SessionStoreError):
                session_store.load_session(path=path)


if __name__ == "__main__":
    unittest.main()

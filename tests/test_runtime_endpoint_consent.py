"""Runtime regression tests for chat endpoint parsing without opening the GUI."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class EndpointConsentRuntimeTests(unittest.TestCase):
    def test_local_endpoint_and_remote_consent_flow_execute(self):
        # Import VYNEX in an isolated data directory. No Tk window is opened and no
        # network request is made; only the endpoint consent logic is exercised.
        with tempfile.TemporaryDirectory(prefix="vynex-endpoint-test-") as temporary:
            home = Path(temporary)
            env = {
                "HOME": str(home),
                "USERPROFILE": str(home),
                "LOCALAPPDATA": str(home / "LocalAppData"),
                "XDG_DATA_HOME": str(home / "xdg-data"),
                "VYNEX_HOME": str(home / "VYNEXRuntime"),
            }
            with patch.dict(os.environ, env, clear=False):
                module_name = f"vynex_runtime_test_{id(self)}"
                spec = importlib.util.spec_from_file_location(module_name, ROOT / "VYNEX.py")
                self.assertIsNotNone(spec)
                self.assertIsNotNone(spec.loader)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                app = module.VYNEXApp.__new__(module.VYNEXApp)
                app.root = None
                app.settings = {"chat_url": "http://127.0.0.1:11434"}
                self.assertTrue(app._ensure_chat_endpoint_consent())

                app.settings = {"chat_url": "https://remote.example:11434"}
                with patch.object(module.messagebox, "askyesno", return_value=False) as ask:
                    self.assertFalse(app._ensure_chat_endpoint_consent())
                    ask.assert_called_once()

                with patch.object(module.messagebox, "askyesno", return_value=True) as ask:
                    self.assertTrue(app._ensure_chat_endpoint_consent())
                    ask.assert_called_once()
                    self.assertEqual(app.settings["approved_remote_endpoint"], "https://remote.example:11434")


if __name__ == "__main__":
    unittest.main()

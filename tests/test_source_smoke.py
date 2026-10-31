from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "VYNEX.py"


class VynexSourceSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source_text, filename=str(SOURCE))

    def test_source_parses(self):
        self.assertIsNotNone(self.tree)

    def test_portable_paths_exist(self):
        self.assertIn("def _get_user_data_dir", self.source_text)
        self.assertIn("VYNEX_HOME", self.source_text)
        self.assertIn("def find_engine_asset", self.source_text)

    def test_cross_platform_default_app_opener(self):
        self.assertIn("def open_path_with_default_app", self.source_text)
        self.assertIn('sys.platform == "darwin"', self.source_text)
        self.assertIn('shutil.which("xdg-open")', self.source_text)

    def test_platform_speech_backends(self):
        self.assertIn('shutil.which("say")', self.source_text)
        self.assertIn('shutil.which("espeak-ng")', self.source_text)

    def test_first_run_terms_gate_exists(self):
        self.assertIn("LEGAL_NOTICE_VERSION", self.source_text)
        self.assertIn("def _startup_legal_gate", self.source_text)
        self.assertIn("accepted_legal_notice_version", self.source_text)
        self.assertIn("TERMS_TEXT", self.source_text)

    def test_sensitive_features_require_app_level_permission(self):
        self.assertIn("def _ensure_feature_permission", self.source_text)
        self.assertIn('self._ensure_feature_permission("microphone")', self.source_text)
        self.assertIn('self._ensure_feature_permission("screen_capture")', self.source_text)
        self.assertIn("def _revoke_feature_permission", self.source_text)

    def test_urlparse_is_imported_for_chat_and_settings(self):
        # A text-only assertion that urlparse is used is not enough: a missing import
        # would crash message sending and settings validation at runtime.
        imports_urlparse = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "urllib.parse"
            and any(alias.name == "urlparse" for alias in node.names)
            for node in ast.walk(self.tree)
        )
        self.assertTrue(imports_urlparse, "urlparse must be imported from urllib.parse")

    def test_windows_runtime_has_portable_user_profile_fallback(self):
        self.assertIn('Path.home() / "VYNEXRuntime"', self.source_text)
        self.assertIn('_legacy_runtime_root.is_dir()', self.source_text)
        self.assertIn('os.environ.get("VYNEX_HOME"', self.source_text)

    def test_remote_chat_endpoint_warns_user(self):
        self.assertIn("urlparse(base_url)", self.source_text)
        self.assertIn("Attention : serveur externe", self.source_text)
        self.assertIn("peuvent quitter cet appareil", self.source_text)
        self.assertIn("def _ensure_chat_endpoint_consent", self.source_text)
        self.assertIn("approved_remote_endpoint", self.source_text)

    def test_policy_and_macos_usage_declarations_exist(self):
        for name in ("TERMS_OF_USE.md", "PRIVACY_POLICY.md", "PERMISSIONS.md", "VYNEX_macos.spec"):
            self.assertTrue((ROOT / name).is_file(), name)
        spec = (ROOT / "VYNEX_macos.spec").read_text(encoding="utf-8")
        self.assertIn("NSMicrophoneUsageDescription", spec)
        self.assertIn("NSScreenCaptureUsageDescription", spec)

    def test_robot_brand_assets_are_packaged(self):
        assets = ROOT / "assets"
        for name in ("VYNEX_icon.png", "VYNEX_splash.png", "VYNEX.ico", "VYNEX.icns"):
            self.assertTrue((assets / name).is_file(), name)
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("--add-data", workflow)
        spec = (ROOT / "VYNEX_macos.spec").read_text(encoding="utf-8")
        self.assertIn("assets/VYNEX.icns", spec)
        self.assertIn("('assets/VYNEX_icon.png', 'assets')", spec)


    def test_robot_is_used_on_welcome_screen_and_window_icon(self):
        self.assertIn('find_image_asset("VYNEX_icon.png")', self.source_text)
        self.assertIn('find_image_asset("VYNEX_splash.png")', self.source_text)
        self.assertIn("self.root.iconphoto(True, self._window_icon_photo)", self.source_text)

    def test_individual_conversation_deletion_is_available(self):
        self.assertIn("def _delete_chat_record(self, record, parent=None) -> bool:", self.source_text)
        self.assertIn('text="Supprimer la sélection"', self.source_text)
        self.assertIn('self.recent_list.bind("<Delete>", self._delete_selected_recent_chat)', self.source_text)
        self.assertIn('self.recent_list.bind("<Button-3>", self._recent_context_menu)', self.source_text)
        self.assertIn("write_json(CHATS_FILE, remaining)", self.source_text)
        self.assertIn("self.current_chat_id = str(uuid.uuid4())", self.source_text)
        self.assertIn("Les fichiers de la bibliothèque d’images ne sont pas supprimés.", self.source_text)



if __name__ == "__main__":
    unittest.main()

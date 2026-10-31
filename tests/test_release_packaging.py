from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleasePackagingTests(unittest.TestCase):
    def test_build_scripts_exist_for_all_native_systems(self):
        for path in (
            ROOT / "BUILD_WINDOWS_SAFE.ps1",
            ROOT / "BUILD_MACOS.sh",
            ROOT / "BUILD_LINUX.sh",
            ROOT / "install-linux.sh",
            ROOT / "uninstall-linux.sh",
        ):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())

    def test_workflow_targets_windows_linux_and_both_mac_architectures(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        for label in (
            "windows-x64",
            "linux-x64",
            "macos-arm64",
            "macos-intel",
            "VYNEX-windows-x64.zip",
            "VYNEX-linux-x64.tar.gz",
        ):
            with self.subTest(label=label):
                self.assertIn(label, workflow)
        self.assertIn("windows-2022", workflow)
        self.assertIn("macos-15-intel", workflow)
        self.assertIn("actions/download-artifact@v8", workflow)

    def test_mac_builder_uses_permission_aware_bundle_spec(self):
        spec = (ROOT / "VYNEX_macos.spec").read_text(encoding="utf-8")
        self.assertIn("assets/VYNEX.icns", spec)
        self.assertIn("NSMicrophoneUsageDescription", spec)
        self.assertIn("NSScreenCaptureUsageDescription", spec)
        self.assertIn("upx=False", spec)

    def test_windows_build_uses_unique_paths_to_avoid_locked_old_files(self):
        script = (ROOT / "BUILD_WINDOWS_SAFE.ps1").read_text(encoding="utf-8")
        self.assertIn("dist_release_$stamp", script)
        self.assertIn("build_release_$stamp", script)
        self.assertIn("VYNEX.exe", script)

    def test_linux_installer_preserves_local_conversation_data(self):
        installer = (ROOT / "install-linux.sh").read_text(encoding="utf-8")
        uninstaller = (ROOT / "uninstall-linux.sh").read_text(encoding="utf-8")
        self.assertIn(".local/opt/vynex", installer)
        self.assertIn('APPLICATIONS_DIR="${HOME}/.local/share/applications"', installer)
        self.assertIn('"$APPLICATIONS_DIR/vynex.desktop"', installer)
        self.assertIn("Les conversations et modèles locaux ont été conservés", uninstaller)


if __name__ == "__main__":
    unittest.main()

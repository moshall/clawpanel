import subprocess
import unittest
from pathlib import Path


class InstallOnlineScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.script = cls.repo_root / "install-online.sh"

    def _run_dry(self, *args):
        cmd = ["bash", str(self.script), "--dry-run", *args]
        result = subprocess.run(cmd, cwd=str(self.repo_root), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        pairs = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                pairs[key.strip()] = value.strip()
        return pairs

    def test_default_archive_url(self):
        pairs = self._run_dry()
        self.assertEqual(
            pairs.get("ARCHIVE_URL"),
            "https://codeload.github.com/moshall/easyclaw/tar.gz/main",
        )

    def test_repo_and_ref_override(self):
        pairs = self._run_dry("--repo", "foo/bar", "--ref", "release")
        self.assertEqual(pairs.get("ARCHIVE_URL"), "https://codeload.github.com/foo/bar/tar.gz/release")

    def test_forward_install_args(self):
        pairs = self._run_dry("--install-dir", "/tmp/easyclaw", "--bin-dir", "/tmp/bin")
        self.assertEqual(pairs.get("FORWARDED_ARGS"), "--install-dir /tmp/easyclaw --bin-dir /tmp/bin")


if __name__ == "__main__":
    unittest.main()

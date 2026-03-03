import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallScriptCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.install_script = cls.repo_root / "install.sh"

    def _run_print_config(self, *args, extra_env=None):
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        cmd = ["bash", str(self.install_script), "--print-config", *args]
        result = subprocess.run(cmd, cwd=str(self.repo_root), capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        pairs = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                pairs[key.strip()] = value.strip()
        return pairs

    def test_cli_can_override_install_dir(self):
        custom_dir = f"/tmp/easyclaw-test-{next(tempfile._get_candidate_names())}"
        pairs = self._run_print_config("--install-dir", custom_dir)
        self.assertEqual(pairs.get("INSTALL_DIR"), custom_dir)

    def test_cli_install_dir_takes_precedence_over_env(self):
        env_dir = f"/tmp/easyclaw-env-{next(tempfile._get_candidate_names())}"
        cli_dir = f"/tmp/easyclaw-cli-{next(tempfile._get_candidate_names())}"
        pairs = self._run_print_config(
            "--install-dir",
            cli_dir,
            extra_env={"EASYCLAW_INSTALL_DIR": env_dir},
        )
        self.assertEqual(pairs.get("INSTALL_DIR"), cli_dir)

    def test_cli_can_override_bin_dir(self):
        custom_bin = f"/tmp/easyclaw-bin-{next(tempfile._get_candidate_names())}"
        pairs = self._run_print_config("--bin-dir", custom_bin)
        self.assertEqual(pairs.get("BIN_DIR"), custom_bin)


if __name__ == "__main__":
    unittest.main()

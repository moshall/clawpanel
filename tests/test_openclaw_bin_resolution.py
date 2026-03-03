import unittest
from unittest.mock import patch

from core import resolve_openclaw_bin


class OpenClawBinResolutionTests(unittest.TestCase):
    def test_prefers_env_override(self):
        with patch.dict("os.environ", {"OPENCLAW_BIN": "/custom/openclaw"}, clear=False):
            with patch("core.shutil.which", return_value="/usr/bin/openclaw"):
                self.assertEqual(resolve_openclaw_bin(), "/custom/openclaw")

    def test_uses_discovered_openclaw_when_env_missing(self):
        with patch.dict("os.environ", {"OPENCLAW_BIN": ""}, clear=False):
            with patch("core.shutil.which", return_value="/usr/bin/openclaw"):
                self.assertEqual(resolve_openclaw_bin(), "/usr/bin/openclaw")

    def test_falls_back_to_usr_local_when_not_found(self):
        with patch.dict("os.environ", {"OPENCLAW_BIN": ""}, clear=False):
            with patch("core.shutil.which", return_value=None):
                self.assertEqual(resolve_openclaw_bin(), "/usr/local/bin/openclaw")


if __name__ == "__main__":
    unittest.main()

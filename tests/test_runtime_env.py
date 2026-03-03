import unittest
from unittest.mock import mock_open, patch

from core.runtime_env import (
    capability_requires_sandbox,
    is_docker_environment,
    normalize_capability_preset_for_runtime,
    recommended_capability_preset_for_runtime,
)


class RuntimeEnvTests(unittest.TestCase):
    def test_is_docker_environment_true_when_dockerenv_exists(self):
        with patch("core.runtime_env.os.path.exists") as exists:
            exists.side_effect = lambda p: p == "/.dockerenv"
            self.assertTrue(is_docker_environment())

    def test_is_docker_environment_true_when_proc_cgroup_contains_container_marker(self):
        with patch("core.runtime_env.os.path.exists") as exists:
            exists.side_effect = lambda p: p == "/proc/1/cgroup"
            with patch("builtins.open", mock_open(read_data="12:cpu:/docker/abcd")):
                self.assertTrue(is_docker_environment())

    def test_is_docker_environment_false_without_markers(self):
        with patch("core.runtime_env.os.path.exists", return_value=False):
            self.assertFalse(is_docker_environment())

    def test_recommended_capability_preset_for_runtime(self):
        self.assertEqual(recommended_capability_preset_for_runtime(is_docker=True), "full-access")
        self.assertEqual(recommended_capability_preset_for_runtime(is_docker=False), "workspace-collab")

    def test_capability_requires_sandbox(self):
        self.assertTrue(capability_requires_sandbox("workspace-collab"))
        self.assertFalse(capability_requires_sandbox("full-access"))

    def test_normalize_capability_preset_for_runtime_forces_non_sandbox_in_docker(self):
        self.assertEqual(
            normalize_capability_preset_for_runtime("workspace-collab", is_docker=True),
            "full-access",
        )
        self.assertEqual(
            normalize_capability_preset_for_runtime("readonly-analysis", is_docker=True),
            "full-access",
        )

    def test_normalize_capability_preset_for_runtime_keeps_non_sandbox_preset(self):
        self.assertEqual(
            normalize_capability_preset_for_runtime("messaging", is_docker=True),
            "messaging",
        )
        self.assertEqual(
            normalize_capability_preset_for_runtime("workspace-collab", is_docker=False),
            "workspace-collab",
        )


if __name__ == "__main__":
    unittest.main()

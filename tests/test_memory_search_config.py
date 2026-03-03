import unittest
from unittest.mock import patch

import core


class MemorySearchConfigTests(unittest.TestCase):
    def test_get_memory_search_config_reads_agents_defaults_path(self):
        with patch.object(core.config, "reload", return_value=None):
            with patch.object(
                core.config,
                "data",
                {
                    "agents": {
                        "defaults": {
                            "memorySearch": {
                                "provider": "voyage",
                                "remote": {"baseUrl": "https://api.voyageai.com/v1"},
                            }
                        }
                    },
                    "memorySearch": {"provider": "openai"},
                },
            ):
                result = core.get_memory_search_config()

        self.assertEqual(
            result,
            {
                "provider": "voyage",
                "remote": {"baseUrl": "https://api.voyageai.com/v1"},
            },
        )

    def test_get_memory_search_config_falls_back_to_legacy_path(self):
        with patch.object(core.config, "reload", return_value=None):
            with patch.object(core.config, "data", {"memorySearch": {"provider": "openai"}}):
                result = core.get_memory_search_config()

        self.assertEqual(result, {"provider": "openai"})

    def test_clear_memory_search_config_targets_agents_defaults_path(self):
        with patch("core.run_cli", return_value=("", "", 0)) as run_cli:
            core.clear_memory_search_config(clear_provider=True)

        calls = [call.args[0] for call in run_cli.call_args_list]
        self.assertEqual(
            calls,
            [
                ["config", "unset", "agents.defaults.memorySearch.provider"],
                ["config", "unset", "memorySearch.provider"],
                ["config", "unset", "agents.defaults.memorySearch.local"],
                ["config", "unset", "memorySearch.local"],
                ["config", "unset", "agents.defaults.memorySearch.remote"],
                ["config", "unset", "memorySearch.remote"],
            ],
        )

    def test_get_memory_provider_credential_target_maps_gemini_to_google(self):
        self.assertEqual(core.get_memory_provider_credential_target("gemini"), "google")
        self.assertEqual(core.get_memory_provider_credential_target("openai"), "openai")
        self.assertIsNone(core.get_memory_provider_credential_target("local"))

    def test_has_memory_provider_api_key_checks_models_providers(self):
        with patch("core.get_models_providers", return_value={"google": {"apiKey": "abc123"}}):
            self.assertTrue(core.has_memory_provider_api_key("gemini"))
        with patch("core.get_models_providers", return_value={"google": {"apiKey": ""}}):
            self.assertFalse(core.has_memory_provider_api_key("gemini"))

    def test_set_memory_provider_api_key_writes_into_mapped_provider(self):
        captured_payload = {}

        def fake_set_models_providers(payload):
            captured_payload.update(payload)
            return True

        with patch("core.get_models_providers", return_value={"google": {"baseUrl": "https://x"}}):
            with patch("core.set_models_providers", side_effect=fake_set_models_providers):
                ok = core.set_memory_provider_api_key("gemini", "new-key")

        self.assertTrue(ok)
        self.assertEqual(
            captured_payload,
            {"google": {"baseUrl": "https://x", "apiKey": "new-key"}},
        )


if __name__ == "__main__":
    unittest.main()

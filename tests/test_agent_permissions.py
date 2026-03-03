import unittest

from core.agent_runtime import apply_agent_access_profile, normalize_permission_overrides


class AgentPermissionOverrideTests(unittest.TestCase):
    def test_normalize_permission_overrides_filters_invalid_values(self):
        raw = {
            "directory_binds": [" /tmp/a:/a:ro ", "", "/tmp/a:/a:ro"],
            "fs_workspace_only": True,
            "exec_security": "ALLOWLIST",
            "deny_tools": ["process", "", "process"],
            "elevated_enabled": False,
            "ignored": "x",
        }
        normalized = normalize_permission_overrides(raw)
        self.assertEqual(normalized["directory_binds"], ["/tmp/a:/a:ro"])
        self.assertTrue(normalized["fs_workspace_only"])
        self.assertEqual(normalized["exec_security"], "allowlist")
        self.assertEqual(normalized["deny_tools"], ["process"])
        self.assertFalse(normalized["elevated_enabled"])
        self.assertNotIn("ignored", normalized)

    def test_normalize_permission_overrides_accepts_camel_case_keys(self):
        normalized = normalize_permission_overrides(
            {
                "directoryBinds": ["/tmp/a:/a:ro"],
                "fsWorkspaceOnly": False,
                "execSecurity": "deny",
                "denyTools": ["process"],
                "elevatedEnabled": True,
            }
        )
        self.assertEqual(normalized["directory_binds"], ["/tmp/a:/a:ro"])
        self.assertFalse(normalized["fs_workspace_only"])
        self.assertEqual(normalized["exec_security"], "deny")
        self.assertEqual(normalized["deny_tools"], ["process"])
        self.assertTrue(normalized["elevated_enabled"])

    def test_apply_agent_access_profile_applies_permission_overrides(self):
        entry = {"id": "a1"}
        apply_agent_access_profile(
            entry,
            access_mode="rw",
            capability_preset="workspace-collab",
            permission_overrides={
                "directory_binds": ["/root/.openclaw/skills:/skills:ro"],
                "fs_workspace_only": True,
                "exec_security": "deny",
                "deny_tools": ["process"],
                "elevated_enabled": False,
            },
        )
        self.assertEqual(entry["sandbox"]["docker"]["binds"], ["/root/.openclaw/skills:/skills:ro"])
        self.assertTrue(entry["tools"]["fs"]["workspaceOnly"])
        self.assertEqual(entry["tools"]["exec"]["security"], "deny")
        self.assertEqual(entry["tools"]["deny"], ["process"])
        self.assertFalse(entry["tools"]["elevated"]["enabled"])


if __name__ == "__main__":
    unittest.main()

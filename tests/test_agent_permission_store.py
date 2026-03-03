import os
import tempfile
import unittest
from unittest.mock import patch

from core import (
    get_agent_permission_overrides,
    set_agent_control_plane_capabilities,
    set_agent_permission_overrides,
)


class AgentPermissionStoreTests(unittest.TestCase):
    def test_set_and_get_permission_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta_path = os.path.join(tmp, "agent_meta.json")
            with patch.dict(os.environ, {"OPENCLAW_AGENT_META_PATH": meta_path}, clear=False):
                ok = set_agent_permission_overrides(
                    "agent01",
                    {
                        "directoryBinds": [" /a:/x:ro ", "/a:/x:ro", ""],
                        "fsWorkspaceOnly": True,
                        "execSecurity": "ALLOWLIST",
                        "denyTools": ["process", "", "process"],
                        "elevatedEnabled": False,
                    },
                )
                self.assertTrue(ok)
                got = get_agent_permission_overrides("agent01")
                self.assertEqual(got.get("directoryBinds"), ["/a:/x:ro"])
                self.assertTrue(got.get("fsWorkspaceOnly"))
                self.assertEqual(got.get("execSecurity"), "allowlist")
                self.assertEqual(got.get("denyTools"), ["process"])
                self.assertFalse(got.get("elevatedEnabled"))

    def test_permission_overrides_survive_control_plane_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta_path = os.path.join(tmp, "agent_meta.json")
            with patch.dict(os.environ, {"OPENCLAW_AGENT_META_PATH": meta_path}, clear=False):
                self.assertTrue(
                    set_agent_permission_overrides(
                        "agent02",
                        {"execSecurity": "deny"},
                    )
                )
                self.assertTrue(set_agent_control_plane_capabilities("agent02", ["status.read"]))
                got = get_agent_permission_overrides("agent02")
                self.assertEqual(got.get("execSecurity"), "deny")

    def test_clear_permission_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta_path = os.path.join(tmp, "agent_meta.json")
            with patch.dict(os.environ, {"OPENCLAW_AGENT_META_PATH": meta_path}, clear=False):
                self.assertTrue(set_agent_permission_overrides("agent03", {"execSecurity": "deny"}))
                self.assertEqual(get_agent_permission_overrides("agent03").get("execSecurity"), "deny")
                self.assertTrue(set_agent_permission_overrides("agent03", {}))
                self.assertEqual(get_agent_permission_overrides("agent03"), {})

    def test_set_permission_overrides_accepts_snake_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta_path = os.path.join(tmp, "agent_meta.json")
            with patch.dict(os.environ, {"OPENCLAW_AGENT_META_PATH": meta_path}, clear=False):
                self.assertTrue(set_agent_permission_overrides("agent04", {"exec_security": "full"}))
                got = get_agent_permission_overrides("agent04")
                self.assertEqual(got.get("execSecurity"), "full")


if __name__ == "__main__":
    unittest.main()

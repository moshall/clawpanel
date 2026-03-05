import os
from copy import deepcopy
from typing import Any, Dict, List, Optional


ACCESS_MODE_LABELS: Dict[str, str] = {
    "none": "不访问工作区",
    "ro": "只读自己的工作区",
    "rw": "读写自己的工作区",
}

ACCESS_MODE_HELP: Dict[str, str] = {
    "none": "不挂载真实 workspace。推荐：纯协调、消息中转、最小数据接触场景。仅在启用 sandbox 时才是硬隔离。",
    "ro": "只读挂载自己的 workspace，不能写入。推荐：代码审查、资料检索、风险分析。仅在启用 sandbox 时才是硬隔离。",
    "rw": "读写挂载自己的 workspace。推荐：日常编码、改文档、修配置、多人协作。",
}

CAPABILITY_PRESET_LABELS: Dict[str, str] = {
    "full-access": "完全开放",
    "readonly-analysis": "只读分析",
    "safe-exec": "安全执行",
    "workspace-collab": "工作区协作",
    "messaging": "通讯协调",
}

CAPABILITY_PRESET_HELP: Dict[str, str] = {
    "full-access": "关闭沙箱限制，工具能力全开。适合主 Agent、高信任维护 Agent、需要跨目录处理事务的场景。",
    "readonly-analysis": "保留沙箱，只允许读取和分析，禁止写入和执行。适合审查、检索、复盘。",
    "safe-exec": "保留沙箱，允许执行命令，但不允许写文件。适合环境探测、日志排障、只读诊断。",
    "workspace-collab": "保留沙箱，允许读写自己的 workspace。适合编码、改文档、修本 Agent 目录内配置。",
    "messaging": "偏消息协调与任务分发，不提供完整编码能力。适合调度、中控、路由类 Agent。",
}

CAPABILITY_PRESETS: Dict[str, Dict[str, Any]] = {
    "full-access": {
        "sandbox": {"mode": "off", "scope": "agent"},
        "tools": {"profile": "full"},
    },
    "readonly-analysis": {
        "sandbox": {"mode": "all", "scope": "agent"},
        "tools": {
            "profile": "minimal",
            "deny": ["write", "edit", "apply_patch", "exec", "process"],
        },
    },
    "safe-exec": {
        "sandbox": {"mode": "all", "scope": "agent"},
        "tools": {
            "profile": "coding",
            "deny": ["write", "edit", "apply_patch"],
        },
    },
    "workspace-collab": {
        "sandbox": {"mode": "all", "scope": "agent"},
        "tools": {"profile": "coding"},
    },
    "messaging": {
        "sandbox": {"mode": "off", "scope": "agent"},
        "tools": {"profile": "messaging"},
    },
}

TOOLS_PROFILE_TO_PRESET = {
    "full": "full-access",
    "minimal": "readonly-analysis",
    "messaging": "messaging",
}

EXEC_SECURITY_VALUES = {"deny", "allowlist", "full"}
TOOLS_PROFILE_VALUES = {"full", "coding", "messaging", "minimal"}


def openclaw_root_from_config(config_path: Optional[str]) -> str:
    path = str(config_path or "").strip()
    if not path:
        return "/root/.openclaw"
    return os.path.dirname(path) or "/root/.openclaw"


def resolve_agent_runtime_paths(agent_id: str, config_path: Optional[str] = None) -> Dict[str, str]:
    aid = str(agent_id or "main").strip() or "main"
    root = openclaw_root_from_config(config_path)
    agent_dir = os.path.join(root, "agents", aid, "agent")
    workspace_name = "workspace" if aid == "main" else f"workspace-{aid}"
    return {
        "root": root,
        "agent_dir": agent_dir,
        "sessions_dir": os.path.join(root, "agents", aid, "sessions"),
        "auth_profiles": os.path.join(agent_dir, "auth-profiles.json"),
        "models_json": os.path.join(agent_dir, "models.json"),
        "workspace": os.path.join(root, workspace_name),
    }


def build_agent_access_profile(
    access_mode: str,
    capability_preset: str,
    custom_allow: Optional[List[str]] = None,
    custom_deny: Optional[List[str]] = None,
) -> Dict[str, Any]:
    mode = str(access_mode or "rw").strip().lower()
    if mode not in ACCESS_MODE_LABELS:
        mode = "rw"

    preset = str(capability_preset or "workspace-collab").strip().lower()
    base = deepcopy(CAPABILITY_PRESETS.get(preset, CAPABILITY_PRESETS["workspace-collab"]))
    base["sandbox"]["workspaceAccess"] = mode

    tools = base.setdefault("tools", {})
    if custom_allow is not None:
        tools["allow"] = _dedupe_tokens(custom_allow)
    if custom_deny is not None:
        tools["deny"] = _dedupe_tokens(custom_deny)

    return base


def normalize_permission_overrides(overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(overrides, dict):
        return {}

    out: Dict[str, Any] = {}

    tools_profile = str(overrides.get("tools_profile", overrides.get("toolsProfile", "")) or "").strip().lower()
    if tools_profile in TOOLS_PROFILE_VALUES:
        out["tools_profile"] = tools_profile

    raw_binds = overrides.get("directory_binds")
    if raw_binds is None:
        raw_binds = overrides.get("directoryBinds")
    if isinstance(raw_binds, list):
        binds = _dedupe_tokens(raw_binds)
        if binds:
            out["directory_binds"] = binds

    fs_workspace_only = overrides.get("fs_workspace_only")
    if fs_workspace_only is None:
        fs_workspace_only = overrides.get("fsWorkspaceOnly")
    if isinstance(fs_workspace_only, bool):
        out["fs_workspace_only"] = fs_workspace_only

    exec_security = str(overrides.get("exec_security", overrides.get("execSecurity", "")) or "").strip().lower()
    if exec_security in EXEC_SECURITY_VALUES:
        out["exec_security"] = exec_security

    raw_deny = overrides.get("deny_tools")
    if raw_deny is None:
        raw_deny = overrides.get("denyTools")
    if isinstance(raw_deny, list):
        deny_tools = _dedupe_tokens(raw_deny)
        if deny_tools:
            out["deny_tools"] = deny_tools

    elevated_enabled = overrides.get("elevated_enabled")
    if elevated_enabled is None:
        elevated_enabled = overrides.get("elevatedEnabled")
    if isinstance(elevated_enabled, bool):
        out["elevated_enabled"] = elevated_enabled

    return out


def apply_permission_overrides(
    agent_entry: Dict[str, Any],
    overrides: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    normalized = normalize_permission_overrides(overrides)
    if not normalized:
        return agent_entry

    sandbox = agent_entry.get("sandbox")
    if not isinstance(sandbox, dict):
        sandbox = {}
        agent_entry["sandbox"] = sandbox
    tools = agent_entry.get("tools")
    if not isinstance(tools, dict):
        tools = {}
        agent_entry["tools"] = tools

    tools_profile = normalized.get("tools_profile")
    if isinstance(tools_profile, str) and tools_profile in TOOLS_PROFILE_VALUES:
        tools["profile"] = tools_profile

    binds = normalized.get("directory_binds")
    if isinstance(binds, list) and binds:
        docker = sandbox.get("docker")
        if not isinstance(docker, dict):
            docker = {}
            sandbox["docker"] = docker
        docker["binds"] = binds

    if "fs_workspace_only" in normalized:
        fs_cfg = tools.get("fs")
        if not isinstance(fs_cfg, dict):
            fs_cfg = {}
            tools["fs"] = fs_cfg
        fs_cfg["workspaceOnly"] = bool(normalized["fs_workspace_only"])

    exec_security = normalized.get("exec_security")
    if isinstance(exec_security, str) and exec_security in EXEC_SECURITY_VALUES:
        exec_cfg = tools.get("exec")
        if not isinstance(exec_cfg, dict):
            exec_cfg = {}
            tools["exec"] = exec_cfg
        exec_cfg["security"] = exec_security

    deny_tools = normalized.get("deny_tools")
    if isinstance(deny_tools, list) and deny_tools:
        tools["deny"] = deny_tools

    if "elevated_enabled" in normalized:
        elevated_cfg = tools.get("elevated")
        if not isinstance(elevated_cfg, dict):
            elevated_cfg = {}
            tools["elevated"] = elevated_cfg
        elevated_cfg["enabled"] = bool(normalized["elevated_enabled"])

    return agent_entry


def apply_agent_access_profile(
    agent_entry: Dict[str, Any],
    access_mode: str,
    capability_preset: str,
    custom_allow: Optional[List[str]] = None,
    custom_deny: Optional[List[str]] = None,
    permission_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile = build_agent_access_profile(access_mode, capability_preset, custom_allow, custom_deny)
    agent_entry.pop("security", None)
    agent_entry["sandbox"] = profile["sandbox"]
    agent_entry["tools"] = profile["tools"]
    apply_permission_overrides(agent_entry, permission_overrides)
    return agent_entry


def extract_agent_access_profile(agent_entry: Dict[str, Any]) -> Dict[str, Any]:
    sandbox = agent_entry.get("sandbox") if isinstance(agent_entry.get("sandbox"), dict) else {}
    tools = agent_entry.get("tools") if isinstance(agent_entry.get("tools"), dict) else {}
    access_mode = str(sandbox.get("workspaceAccess", "rw") or "rw").strip().lower()
    if access_mode not in ACCESS_MODE_LABELS:
        access_mode = "rw"

    profile = str(tools.get("profile", "") or "").strip().lower()
    capability_preset = TOOLS_PROFILE_TO_PRESET.get(profile, "")
    deny = _dedupe_tokens(tools.get("deny", []))

    if not capability_preset:
        if profile == "coding":
            capability_preset = "safe-exec" if any(x in deny for x in ["write", "edit", "apply_patch"]) else "workspace-collab"
        else:
            capability_preset = "workspace-collab"

    return {
        "access_mode": access_mode,
        "access_label": ACCESS_MODE_LABELS.get(access_mode, ACCESS_MODE_LABELS["rw"]),
        "capability_preset": capability_preset,
        "capability_label": CAPABILITY_PRESET_LABELS.get(capability_preset, CAPABILITY_PRESET_LABELS["workspace-collab"]),
        "sandbox": deepcopy(sandbox),
        "tools": deepcopy(tools),
    }


def _dedupe_tokens(values: Any) -> List[str]:
    out: List[str] = []
    if not isinstance(values, list):
        return out
    for item in values:
        token = str(item or "").strip()
        if token and token not in out:
            out.append(token)
    return out

import os
from typing import Optional


DOCKER_MARKERS = ("docker", "containerd", "kubepods", "podman")
SANDBOX_CAPABILITY_PRESETS = {"readonly-analysis", "safe-exec", "workspace-collab"}


def is_docker_environment() -> bool:
    if os.path.exists("/.dockerenv"):
        return True
    cgroup_path = "/proc/1/cgroup"
    if not os.path.exists(cgroup_path):
        return False
    try:
        with open(cgroup_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().lower()
    except Exception:
        return False
    return any(marker in text for marker in DOCKER_MARKERS)


def capability_requires_sandbox(capability_preset: str) -> bool:
    key = str(capability_preset or "").strip().lower()
    return key in SANDBOX_CAPABILITY_PRESETS


def normalize_capability_preset_for_runtime(
    capability_preset: str,
    is_docker: Optional[bool] = None,
) -> str:
    key = str(capability_preset or "").strip().lower()
    if not key:
        key = recommended_capability_preset_for_runtime(is_docker=is_docker)
    docker_flag = is_docker_environment() if is_docker is None else bool(is_docker)
    if docker_flag and capability_requires_sandbox(key):
        return "full-access"
    return key


def recommended_capability_preset_for_runtime(is_docker: Optional[bool] = None) -> str:
    flag = is_docker_environment() if is_docker is None else bool(is_docker)
    return "full-access" if flag else "workspace-collab"

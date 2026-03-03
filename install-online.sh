#!/usr/bin/env bash
# EasyClaw online bootstrap installer
# Example:
#   curl -fsSL https://raw.githubusercontent.com/moshall/easyclaw/main/install-online.sh | bash -s -- --install-dir /opt/easyclaw

set -euo pipefail

usage() {
  cat <<'EOF'
EasyClaw online installer

Usage:
  bash install-online.sh [bootstrap-options] [install-options...]

Bootstrap options:
  --repo <owner/name>   GitHub repo slug (default: moshall/easyclaw)
  --ref <git-ref>       Branch/tag/commit (default: main)
  --keep-temp           Keep temp source directory after install
  --dry-run             Print resolved archive URL and forwarded args, then exit
  -h, --help            Show this help

Install options:
  Any other options are forwarded to install.sh
  e.g. --install-dir /data/easyclaw --bin-dir /usr/local/bin
EOF
}

REPO_SLUG="${EASYCLAW_REPO_SLUG:-moshall/easyclaw}"
REF="${EASYCLAW_REF:-main}"
KEEP_TEMP="0"
DRY_RUN="0"
FORWARD_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "[ERROR] --repo requires a value" >&2; exit 1; }
      REPO_SLUG="$2"
      shift 2
      ;;
    --ref)
      [[ $# -ge 2 ]] || { echo "[ERROR] --ref requires a value" >&2; exit 1; }
      REF="$2"
      shift 2
      ;;
    --keep-temp)
      KEEP_TEMP="1"
      shift
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      FORWARD_ARGS+=("$1")
      shift
      ;;
  esac
done

ARCHIVE_URL="${EASYCLAW_ARCHIVE_URL:-https://codeload.github.com/${REPO_SLUG}/tar.gz/${REF}}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "ARCHIVE_URL=${ARCHIVE_URL}"
  if [[ ${#FORWARD_ARGS[@]} -gt 0 ]]; then
    echo "FORWARDED_ARGS=${FORWARD_ARGS[*]}"
  else
    echo "FORWARDED_ARGS="
  fi
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[ERROR] curl not found. Please install curl first." >&2
  exit 1
fi

if ! command -v tar >/dev/null 2>&1; then
  echo "[ERROR] tar not found. Please install tar first." >&2
  exit 1
fi

tmp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t easyclaw-install)"
cleanup() {
  if [[ "${KEEP_TEMP}" != "1" && -n "${tmp_dir}" && -d "${tmp_dir}" ]]; then
    rm -rf "${tmp_dir}"
  fi
}
trap cleanup EXIT

echo "[INFO] Downloading ${ARCHIVE_URL}"
curl -fsSL "${ARCHIVE_URL}" | tar -xzf - -C "${tmp_dir}"

install_script="$(find "${tmp_dir}" -maxdepth 3 -type f -name "install.sh" | head -n 1)"
if [[ -z "${install_script}" || ! -f "${install_script}" ]]; then
  echo "[ERROR] install.sh not found in downloaded archive." >&2
  exit 1
fi

echo "[INFO] Running installer: ${install_script}"
bash "${install_script}" "${FORWARD_ARGS[@]}"
echo "[OK] EasyClaw installation finished."

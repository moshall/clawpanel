#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

function isTrue(value) {
  const text = String(value || "").trim().toLowerCase();
  return text === "1" || text === "true" || text === "yes" || text === "on";
}

function isFalse(value) {
  const text = String(value || "").trim().toLowerCase();
  return text === "0" || text === "false" || text === "no" || text === "off";
}

function buildEnvInstallArgs() {
  const args = [];
  const pairs = [
    ["CLAWPANEL_INSTALL_DIR", "--install-dir"],
    ["CLAWPANEL_BIN_DIR", "--bin-dir"],
    ["CLAWPANEL_OPENCLAW_HOME", "--openclaw-home"],
    ["CLAWPANEL_TARGET_USER", "--target-user"],
    ["CLAWPANEL_TARGET_HOME", "--target-home"]
  ];
  for (const [envName, flag] of pairs) {
    const value = String(process.env[envName] || "").trim();
    if (value) {
      args.push(flag, value);
    }
  }
  if (isTrue(process.env.CLAWPANEL_SKIP_PIP)) {
    args.push("--skip-pip");
  }
  if (isTrue(process.env.CLAWPANEL_NO_AUTO_DEPS) || isFalse(process.env.CLAWPANEL_AUTO_DEPS)) {
    args.push("--no-auto-deps");
  } else if (isTrue(process.env.CLAWPANEL_AUTO_DEPS)) {
    args.push("--auto-deps");
  }
  return args;
}

function hasFlag(args, flagName) {
  for (const item of args || []) {
    const token = String(item || "").trim();
    if (token === flagName || token.startsWith(`${flagName}=`)) {
      return true;
    }
  }
  return false;
}

function buildNpmDefaultArgs(repoRoot, forwardArgs) {
  const args = [];
  const hasCliInstallDir = hasFlag(forwardArgs, "--install-dir");
  const hasCliBinDir = hasFlag(forwardArgs, "--bin-dir");
  const hasEnvInstallDir = String(process.env.CLAWPANEL_INSTALL_DIR || process.env.EASYCLAW_INSTALL_DIR || "").trim();
  const hasEnvBinDir = String(process.env.CLAWPANEL_BIN_DIR || process.env.EASYCLAW_BIN_DIR || "").trim();

  // npm mode default: keep runtime inside npm package directory.
  if (!hasCliInstallDir && !hasEnvInstallDir) {
    args.push("--install-dir", repoRoot);
  }
  if (!hasCliBinDir && !hasEnvBinDir) {
    args.push("--bin-dir", path.join(repoRoot, ".bin"));
  }
  return args;
}

function runInstall(forwardArgs) {
  const repoRoot = path.resolve(__dirname, "..");
  const installScript = path.join(repoRoot, "install.sh");
  if (!fs.existsSync(installScript)) {
    console.error(`[ERROR] install.sh not found: ${installScript}`);
    return 1;
  }

  const args = [
    installScript,
    ...buildNpmDefaultArgs(repoRoot, forwardArgs || []),
    ...buildEnvInstallArgs(),
    ...(forwardArgs || [])
  ];
  const result = spawnSync("bash", args, {
    stdio: "inherit",
    env: process.env
  });

  if (typeof result.status === "number") {
    return result.status;
  }
  return 1;
}

const exitCode = runInstall(process.argv.slice(2));
process.exit(exitCode);

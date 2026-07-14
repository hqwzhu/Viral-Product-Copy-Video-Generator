"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");

const ALLOWED_PLATFORMS = new Set(["youtube", "zhihu", "xiaohongshu", "douyin", "github", "tiktok"]);
const LOCAL_HOST_RE = /^(localhost|127\.|0\.0\.0\.0|10\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.|\[?::1\]?)/i;
const DAY_MS = 24 * 60 * 60 * 1000;
const DEFAULT_ARTIFACT_RETENTION_DAYS = 30;
const DEFAULT_AUDIT_RETENTION_DAYS = 180;
const DEFAULT_RETENTION_CLEANUP_INTERVAL_MS = 6 * 60 * 60 * 1000;

async function startRetentionCleanup(store, options = {}) {
  const intervalMs = Math.max(
    60 * 1000,
    Number(options.intervalMs || process.env.RETENTION_CLEANUP_INTERVAL_MS || DEFAULT_RETENTION_CLEANUP_INTERVAL_MS)
  );
  await runRetentionCleanup(store, options);
  return setInterval(() => {
    runRetentionCleanup(store, options).catch((error) => {
      console.error(`retention cleanup failed: ${error.stack || error.message}`);
    });
  }, intervalMs);
}

async function runRetentionCleanup(store, options = {}) {
  const now = new Date(options.now || Date.now());
  if (!Number.isFinite(now.getTime())) {
    throw new Error("invalid_retention_cleanup_time");
  }
  const outputRoot = path.resolve(
    options.outputRoot || process.env.HOSTED_RUN_OUTPUT_ROOT || path.join(__dirname, "..", "var", "hosted-runs")
  );
  const artifactRetentionDays = positiveDays(
    options.artifactRetentionDays || process.env.HOSTED_ARTIFACT_RETENTION_DAYS,
    DEFAULT_ARTIFACT_RETENTION_DAYS
  );
  const auditRetentionDays = positiveDays(
    options.auditRetentionDays || process.env.SECURITY_AUDIT_LOG_RETENTION_DAYS,
    DEFAULT_AUDIT_RETENTION_DAYS
  );
  const artifactCutoff = now.getTime() - artifactRetentionDays * DAY_MS;
  const auditCutoff = now.getTime() - auditRetentionDays * DAY_MS;
  const summary = { artifactsDeleted: 0, artifactDeleteFailures: 0, auditEventsDeleted: 0 };

  await store.update((state) => {
    const auditLog = Array.isArray(state.auditLog) ? state.auditLog : [];
    state.auditLog = auditLog.filter((entry) => {
      const timestamp = Date.parse(String(entry && entry.at || ""));
      const keep = !Number.isFinite(timestamp) || timestamp > auditCutoff;
      if (!keep) summary.auditEventsDeleted += 1;
      return keep;
    });

    for (const run of Object.values(state.hostedRuns || {})) {
      const finishedAt = Date.parse(String(run.finishedAt || ""));
      if (!Number.isFinite(finishedAt) || finishedAt > artifactCutoff || run.artifactsDeletedAt) {
        continue;
      }
      const artifactDirectory = String(run.artifactDirectory || "").trim();
      if (!artifactDirectory) {
        continue;
      }
      const resolvedDirectory = path.resolve(artifactDirectory);
      if (!isPathInside(outputRoot, resolvedDirectory)) {
        summary.artifactDeleteFailures += 1;
        state.auditLog.push({
          at: now.toISOString(),
          action: "hosted_artifact_delete_blocked",
          details: { runId: run.id, reason: "artifact_path_outside_output_root" }
        });
        continue;
      }
      try {
        fs.rmSync(resolvedDirectory, { recursive: true, force: true });
        run.artifactDirectory = "";
        run.reportPath = "";
        run.reportUrl = "";
        run.artifactsDeletedAt = now.toISOString();
        run.updatedAt = now.toISOString();
        summary.artifactsDeleted += 1;
        state.auditLog.push({
          at: now.toISOString(),
          action: "hosted_artifacts_deleted",
          details: { runId: run.id, retentionDays: artifactRetentionDays }
        });
      } catch (error) {
        summary.artifactDeleteFailures += 1;
        state.auditLog.push({
          at: now.toISOString(),
          action: "hosted_artifact_delete_failed",
          details: { runId: run.id, reason: error.message }
        });
      }
    }
    return summary;
  });
  return summary;
}

function isPathInside(root, target) {
  const relative = path.relative(root, target);
  return Boolean(relative) && !relative.startsWith("..") && !path.isAbsolute(relative);
}

function positiveDays(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

async function startHostedWorker(store, options = {}) {
  const intervalMs = Math.max(5000, Number(options.intervalMs || process.env.HOSTED_WORKER_INTERVAL_MS || 15000));
  await processNextHostedRun(store, options);
  return setInterval(() => {
    processNextHostedRun(store, options).catch((error) => {
      console.error(`hosted worker failed: ${error.stack || error.message}`);
    });
  }, intervalMs);
}

async function processNextHostedRun(store, options = {}) {
  let selectedRun = null;
  await store.update((state) => {
    selectedRun = Object.values(state.hostedRuns || {})
      .filter((run) => run.status === "queued")
      .sort((a, b) => String(a.createdAt).localeCompare(String(b.createdAt)))[0] || null;
    if (!selectedRun) return null;
    selectedRun.status = "running";
    selectedRun.startedAt = nowIso();
    selectedRun.updatedAt = nowIso();
    const usage = state.usageLedger[selectedRun.usageId];
    if (usage && usage.status === "reserved") {
      usage.status = "running";
      usage.updatedAt = nowIso();
    }
    audit(state, "hosted_run_started", { runId: selectedRun.id, workflowType: selectedRun.workflowType });
    return selectedRun;
  });

  if (!selectedRun) return null;

  const result = await executeHostedRun(selectedRun, options);
  await store.update((state) => {
    const run = state.hostedRuns[selectedRun.id];
    if (!run) return null;
    run.status = result.status;
    run.exitCode = result.exitCode;
    run.reason = result.reason;
    run.command = result.command;
    run.artifactDirectory = result.artifactDirectory;
    run.reportPath = result.reportPath;
    run.reportUrl = result.reportUrl;
    run.finishedAt = nowIso();
    run.updatedAt = nowIso();
    commitUsage(state, run.usageId, {
      status: result.status === "succeeded" ? "succeeded" : "failed",
      creditsUsed: result.status === "succeeded" ? Number(run.estimatedCredits || 0) : 0,
      inputTokens: 0,
      outputTokens: 0,
      videoSecondsRendered: 0
    });
    audit(state, "hosted_run_finished", {
      runId: run.id,
      status: run.status,
      exitCode: run.exitCode,
      reason: run.reason
    });
    return run;
  });
  return result;
}

async function executeHostedRun(run, options = {}) {
  const repoRoot = path.resolve(options.repoRoot || process.env.PROMOTION_REPO_ROOT || path.join(__dirname, "..", "..", ".."));
  const outputRoot = path.resolve(options.outputRoot || process.env.HOSTED_RUN_OUTPUT_ROOT || path.join(__dirname, "..", "var", "hosted-runs"));
  const artifactDirectory = path.join(outputRoot, run.id);
  fs.mkdirSync(artifactDirectory, { recursive: true });

  const command = buildHostedCommand(run, { repoRoot, artifactDirectory });
  if (command.error) {
    writeRunSummary(artifactDirectory, run, { status: "blocked", reason: command.error });
    return {
      status: "blocked",
      exitCode: null,
      reason: command.error,
      command: [],
      artifactDirectory,
      reportPath: "",
      reportUrl: ""
    };
  }

  if ((options.mode || process.env.HOSTED_WORKER_MODE || "execute") === "simulate") {
    const summary = writeRunSummary(artifactDirectory, run, {
      status: "succeeded",
      reason: "simulated_worker_run",
      command: [command.bin, ...command.args]
    });
    return {
      status: "succeeded",
      exitCode: 0,
      reason: "simulated_worker_run",
      command: [command.bin, ...command.args],
      artifactDirectory,
      reportPath: summary,
      reportUrl: ""
    };
  }

  const env = safeWorkerEnv(process.env);
  const childResult = await spawnCommand(command.bin, command.args, {
    cwd: repoRoot,
    env,
    timeoutMs: Number(options.timeoutMs || process.env.HOSTED_RUN_TIMEOUT_MS || 30 * 60 * 1000),
    logFile: path.join(artifactDirectory, "worker.log")
  });
  const status = childResult.exitCode === 0 ? "succeeded" : "failed";
  const summary = writeRunSummary(artifactDirectory, run, {
    status,
    reason: childResult.reason,
    exitCode: childResult.exitCode,
    command: [command.bin, ...command.args]
  });
  return {
    status,
    exitCode: childResult.exitCode,
    reason: childResult.reason,
    command: [command.bin, ...command.args],
    artifactDirectory,
    reportPath: summary,
    reportUrl: ""
  };
}

function buildHostedCommand(run, context) {
  const commandType = String(run.commandType || "skill_entry");
  const productUrl = String(run.productUrl || "").trim();
  const platforms = Array.isArray(run.platforms)
    ? run.platforms.map((platform) => String(platform).trim()).filter(Boolean)
    : [];
  const validationError = validateHostedRequest(commandType, productUrl, platforms);
  if (validationError) {
    return { error: validationError };
  }

  const python = process.env.PYTHON_BIN || "python";
  if (commandType === "skill_entry") {
    const args = [
      path.join("scripts", "skill_entry.py"),
      "--link",
      productUrl,
      "--platforms",
      platforms.join(","),
      "--out-dir",
      context.artifactDirectory
    ];
    if (run.workflowDepth === "playbook") {
      args.push("--skip-video", "--skip-publish-queue", "--skip-final-capability-audit");
    }
    if (run.workflowDepth === "research") {
      args.push("--skip-video", "--skip-publish-queue");
    }
    if (!run.options || run.options.hostedVideo !== true) {
      args.push("--skip-video");
    }
    return { bin: python, args };
  }

  if (commandType === "final_readiness") {
    return {
      bin: python,
      args: [path.join("scripts", "final_capability_readiness.py"), "--out-dir", context.artifactDirectory]
    };
  }

  if (commandType === "real_evidence_inbox_setup" || commandType === "viral_evidence_inbox_setup") {
    const script = commandType === "real_evidence_inbox_setup"
      ? path.join("scripts", "real_evidence_inbox_setup.py")
      : path.join("scripts", "viral_evidence_inbox_setup.py");
    return {
      bin: python,
      args: [
        script,
        "--product-url",
        productUrl,
        "--platforms",
        platforms.join(","),
        "--inbox-dir",
        path.join(context.artifactDirectory, commandType),
        "--out-dir",
        context.artifactDirectory
      ]
    };
  }

  return { error: "unsupported_hosted_command_type" };
}

function validateHostedRequest(commandType, productUrl, platforms) {
  const requiresUrl = ["skill_entry", "real_evidence_inbox_setup", "viral_evidence_inbox_setup"].includes(commandType);
  const requiresPlatforms = ["skill_entry", "real_evidence_inbox_setup", "viral_evidence_inbox_setup"].includes(commandType);
  if (requiresUrl) {
    let parsed;
    try {
      parsed = new URL(productUrl);
    } catch (_error) {
      return "invalid_product_url";
    }
    if (!["http:", "https:"].includes(parsed.protocol)) return "unsupported_product_url_scheme";
    if (!process.env.ALLOW_PRIVATE_PRODUCT_URLS && LOCAL_HOST_RE.test(parsed.hostname)) {
      return "private_product_url_blocked";
    }
  }
  if (requiresPlatforms) {
    if (!platforms.length) return "missing_platforms";
    const unknown = platforms.filter((platform) => !ALLOWED_PLATFORMS.has(platform));
    if (unknown.length) return `unsupported_platforms:${unknown.join(",")}`;
  }
  return "";
}

function spawnCommand(bin, args, options) {
  return new Promise((resolve) => {
    const output = fs.createWriteStream(options.logFile, { flags: "a" });
    output.write(`$ ${[bin, ...args].join(" ")}\n`);
    const child = childProcess.spawn(bin, args, {
      cwd: options.cwd,
      env: options.env,
      shell: false,
      windowsHide: true
    });
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      child.kill("SIGTERM");
      settled = true;
      output.end("\nTIMEOUT\n");
      resolve({ exitCode: null, reason: "timeout" });
    }, options.timeoutMs);
    child.stdout.pipe(output, { end: false });
    child.stderr.pipe(output, { end: false });
    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      output.end(`\nERROR: ${error.message}\n`);
      resolve({ exitCode: null, reason: error.message });
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      output.end(`\nEXIT ${code}\n`);
      resolve({ exitCode: code, reason: code === 0 ? "ok" : "worker_process_failed" });
    });
  });
}

function safeWorkerEnv(source) {
  const env = {
    PATH: source.PATH,
    Path: source.Path,
    SystemRoot: source.SystemRoot,
    TEMP: source.TEMP,
    TMP: source.TMP,
    PYTHONIOENCODING: "utf-8",
    I_APPROVE_PUBLISH: "false",
    PUBLISH_DRY_RUN: "true",
    REQUIRE_MANUAL_APPROVAL: "true"
  };
  for (const key of ["YOUTUBE_API_KEY", "OPENAI_API_KEY"]) {
    if (source[key]) env[key] = source[key];
  }
  return env;
}

function writeRunSummary(artifactDirectory, run, result) {
  const reportPath = path.join(artifactDirectory, "hosted-run-summary.json");
  fs.writeFileSync(
    reportPath,
    `${JSON.stringify({
      runId: run.id,
      workflowType: run.workflowType,
      commandType: run.commandType,
      productUrl: run.productUrl,
      platforms: run.platforms,
      status: result.status,
      reason: result.reason,
      exitCode: result.exitCode,
      command: result.command,
      generatedAt: nowIso()
    }, null, 2)}\n`
  );
  return reportPath;
}

function commitUsage(state, usageId, result) {
  const usage = state.usageLedger && state.usageLedger[usageId];
  if (!usage || usage.status === "succeeded" || usage.status === "failed") {
    return null;
  }
  const license = state.licenses && state.licenses[usage.licenseId];
  const creditsUsed = Math.max(0, Number(result.creditsUsed || 0));
  const refundable = Math.max(0, Number(usage.creditsReserved || 0) - creditsUsed);
  usage.inputTokens = Number(result.inputTokens || 0);
  usage.outputTokens = Number(result.outputTokens || 0);
  usage.videoSecondsRendered = Number(result.videoSecondsRendered || 0);
  usage.creditsUsed = creditsUsed;
  usage.status = String(result.status || "succeeded");
  usage.updatedAt = nowIso();
  if (license && refundable > 0) {
    license.creditsRemaining += refundable;
    license.updatedAt = nowIso();
  }
  return { usageId: usage.id, creditsUsed, creditsRefunded: refundable, status: usage.status };
}

function audit(state, action, details) {
  state.auditLog.push({ at: nowIso(), action, details });
}

function nowIso() {
  return new Date().toISOString();
}

module.exports = {
  buildHostedCommand,
  commitUsage,
  executeHostedRun,
  processNextHostedRun,
  runRetentionCleanup,
  startHostedWorker,
  startRetentionCleanup,
  validateHostedRequest
};

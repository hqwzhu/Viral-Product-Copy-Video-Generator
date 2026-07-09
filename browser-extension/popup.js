const ENHE_SITE = "https://www.enhe-tech.com.cn/";
const DEFAULT_ENDPOINT = "https://www.enhe-tech.com.cn/api/promotion-manager/license";
const DEFAULT_USAGE_AUTHORIZE_ENDPOINT = "https://www.enhe-tech.com.cn/api/promotion-manager/usage/authorize";
const DEFAULT_HOSTED_RUN_ENDPOINT = "https://www.enhe-tech.com.cn/api/promotion-manager/run";
const CHECKOUT_URL = "https://www.enhe-tech.com.cn/promotion-manager/checkout";
const CUSTOMER_PORTAL_URL = "https://www.enhe-tech.com.cn/promotion-manager/billing";

const PLANS = {
  free: { label: "Free", credits: 5, price: 0 },
  starter: { label: "Starter", credits: 60, price: 29 },
  growth: { label: "Growth", credits: 220, price: 99 },
  scale: { label: "Scale", credits: 800, price: 299 }
};

const COST_PER_CREDIT = 0.35;

const COMMAND_LABELS = {
  skill_entry: "Skill run",
  browser_publish_session: "Publish session",
  real_evidence_inbox: "Evidence inbox",
  performance_monitor: "Performance monitor",
  final_readiness: "Readiness audit",
  automation_init: "Schedule init",
  automation_run: "Scheduled run",
  automation_windows_task: "Windows task"
};

const els = {
  licenseStatus: document.getElementById("licenseStatus"),
  productUrl: document.getElementById("productUrl"),
  tabTitle: document.getElementById("tabTitle"),
  useTab: document.getElementById("useTab"),
  generate: document.getElementById("generate"),
  selectAll: document.getElementById("selectAll"),
  workflowDepth: document.getElementById("workflowDepth"),
  commandType: document.getElementById("commandType"),
  commandModeLabel: document.getElementById("commandModeLabel"),
  outDir: document.getElementById("outDir"),
  publishQueue: document.getElementById("publishQueue"),
  platformPublishUrls: document.getElementById("platformPublishUrls"),
  evidenceInbox: document.getElementById("evidenceInbox"),
  automationConfig: document.getElementById("automationConfig"),
  automationOutputRoot: document.getElementById("automationOutputRoot"),
  automationJobId: document.getElementById("automationJobId"),
  automationIntervalDays: document.getElementById("automationIntervalDays"),
  windowsTaskScript: document.getElementById("windowsTaskScript"),
  windowsTaskTime: document.getElementById("windowsTaskTime"),
  runFormFill: document.getElementById("runFormFill"),
  captureBrowserEvidence: document.getElementById("captureBrowserEvidence"),
  allowLocalhost: document.getElementById("allowLocalhost"),
  autoSearchCompetitors: document.getElementById("autoSearchCompetitors"),
  enableMultiQueryDiscovery: document.getElementById("enableMultiQueryDiscovery"),
  browserFollowUps: document.getElementById("browserFollowUps"),
  enablePublishQueue: document.getElementById("enablePublishQueue"),
  enableBrowserPublishAssistant: document.getElementById("enableBrowserPublishAssistant"),
  enableBrowserFormFill: document.getElementById("enableBrowserFormFill"),
  enableMetricsRecovery: document.getElementById("enableMetricsRecovery"),
  enableNextRoundOptimization: document.getElementById("enableNextRoundOptimization"),
  alsoWindowsTask: document.getElementById("alsoWindowsTask"),
  plan: document.getElementById("plan"),
  monthlyRuns: document.getElementById("monthlyRuns"),
  deepReview: document.getElementById("deepReview"),
  hostedVideo: document.getElementById("hostedVideo"),
  creditMeter: document.getElementById("creditMeter"),
  costSummary: document.getElementById("costSummary"),
  licenseKey: document.getElementById("licenseKey"),
  licenseEndpoint: document.getElementById("licenseEndpoint"),
  usageAuthorizeEndpoint: document.getElementById("usageAuthorizeEndpoint"),
  hostedRunEndpoint: document.getElementById("hostedRunEndpoint"),
  saveLicense: document.getElementById("saveLicense"),
  validateLicense: document.getElementById("validateLicense"),
  authorizeUsage: document.getElementById("authorizeUsage"),
  copyHostedPayload: document.getElementById("copyHostedPayload"),
  startHostedRun: document.getElementById("startHostedRun"),
  openCheckout: document.getElementById("openCheckout"),
  openPortal: document.getElementById("openPortal"),
  licenseMessage: document.getElementById("licenseMessage"),
  usageMessage: document.getElementById("usageMessage"),
  hostedRunMessage: document.getElementById("hostedRunMessage"),
  commandOutput: document.getElementById("commandOutput"),
  copyCommand: document.getElementById("copyCommand")
};

document.addEventListener("DOMContentLoaded", init);
els.useTab.addEventListener("click", useCurrentTab);
els.generate.addEventListener("click", generateCommand);
els.selectAll.addEventListener("click", selectAllPlatforms);
els.copyCommand.addEventListener("click", copyCommand);
els.saveLicense.addEventListener("click", saveLicense);
els.validateLicense.addEventListener("click", validateLicense);
els.authorizeUsage.addEventListener("click", authorizeUsage);
els.copyHostedPayload.addEventListener("click", copyHostedPayload);
els.startHostedRun.addEventListener("click", startHostedRun);
els.openCheckout.addEventListener("click", openCheckout);
els.openPortal.addEventListener("click", openPortal);
els.plan.addEventListener("change", updateEstimate);
els.monthlyRuns.addEventListener("input", updateEstimate);
els.deepReview.addEventListener("change", updateEstimate);
els.hostedVideo.addEventListener("change", updateEstimate);
els.workflowDepth.addEventListener("change", updateEstimate);
els.commandType.addEventListener("change", handleCommandTypeChange);
els.runFormFill.addEventListener("change", updateEstimate);
els.captureBrowserEvidence.addEventListener("change", updateEstimate);
els.allowLocalhost.addEventListener("change", updateEstimate);
els.autoSearchCompetitors.addEventListener("change", updateEstimate);
els.enableMultiQueryDiscovery.addEventListener("change", updateEstimate);
els.browserFollowUps.addEventListener("change", updateEstimate);
els.enablePublishQueue.addEventListener("change", updateEstimate);
els.enableBrowserPublishAssistant.addEventListener("change", updateEstimate);
els.enableBrowserFormFill.addEventListener("change", updateEstimate);
els.enableMetricsRecovery.addEventListener("change", updateEstimate);
els.enableNextRoundOptimization.addEventListener("change", updateEstimate);
els.alsoWindowsTask.addEventListener("change", updateEstimate);
Array.from(document.querySelectorAll("#platforms input")).forEach((input) => {
  input.addEventListener("change", updateEstimate);
});

async function init() {
  const stored = await chrome.storage.local.get([
    "licenseKey",
    "licenseEndpoint",
    "usageAuthorizeEndpoint",
    "hostedRunEndpoint",
    "licensePlan",
    "licenseActive"
  ]);
  els.licenseKey.value = stored.licenseKey || "";
  els.licenseEndpoint.value = stored.licenseEndpoint || DEFAULT_ENDPOINT;
  els.usageAuthorizeEndpoint.value = stored.usageAuthorizeEndpoint || DEFAULT_USAGE_AUTHORIZE_ENDPOINT;
  els.hostedRunEndpoint.value = stored.hostedRunEndpoint || DEFAULT_HOSTED_RUN_ENDPOINT;
  if (stored.licensePlan) {
    const planKey = String(stored.licensePlan).toLowerCase();
    if (PLANS[planKey]) {
      els.plan.value = planKey;
    }
  }
  setLicenseStatus(stored.licenseActive ? "Active" : "Local", stored.licenseActive ? "active" : "");
  await useCurrentTab();
  handleCommandTypeChange();
  updateEstimate();
}

async function useCurrentTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs && tabs[0];
  if (!tab) {
    els.tabTitle.textContent = "No active tab found.";
    return;
  }
  if (tab.url && /^https?:\/\//.test(tab.url)) {
    els.productUrl.value = tab.url;
  }
  els.tabTitle.textContent = tab.title ? `Current tab: ${tab.title}` : "Current tab captured.";
}

function selectedPlatforms() {
  return Array.from(document.querySelectorAll("#platforms input:checked")).map((input) => input.value);
}

function selectAllPlatforms() {
  const boxes = Array.from(document.querySelectorAll("#platforms input"));
  const allChecked = boxes.every((box) => box.checked);
  boxes.forEach((box) => {
    box.checked = !allChecked;
  });
  updateEstimate();
}

function generateCommand() {
  const commandType = els.commandType.value;
  if (commandType === "browser_publish_session") {
    generateBrowserPublishSessionCommand();
    return;
  }
  if (commandType === "real_evidence_inbox") {
    generateRealEvidenceInboxCommand();
    return;
  }
  if (commandType === "performance_monitor") {
    generatePerformanceMonitorCommand();
    return;
  }
  if (commandType === "final_readiness") {
    generateFinalReadinessCommand();
    return;
  }
  if (commandType === "automation_init") {
    generateAutomationInitCommand();
    return;
  }
  if (commandType === "automation_run") {
    generateAutomationRunCommand();
    return;
  }
  if (commandType === "automation_windows_task") {
    els.commandOutput.value = automationWindowsTaskCommand();
    updateEstimate();
    return;
  }
  generateSkillEntryCommand();
}

function generateSkillEntryCommand() {
  const url = els.productUrl.value.trim();
  const platforms = selectedPlatforms();
  if (!url) {
    els.commandOutput.value = "Enter a product or website URL first.";
    return;
  }
  if (!platforms.length) {
    els.commandOutput.value = "Select at least one platform.";
    return;
  }
  const args = [
    "python scripts\\skill_entry.py",
    `--link ${quote(url)}`,
    `--platforms ${platforms.join(",")}`,
    `--out-dir ${quote(outDir())}`
  ];
  if (els.workflowDepth.value === "playbook") {
    args.push("--skip-video");
    args.push("--skip-publish-queue");
    args.push("--skip-final-capability-audit");
  }
  if (els.workflowDepth.value === "research") {
    args.push("--skip-video");
    args.push("--skip-publish-queue");
  }
  if (els.workflowDepth.value === "full") {
    args.push("--install-browser-if-missing");
  }
  if (els.deepReview.checked) {
    args.push("--multi-query-query-count 8");
  }
  els.commandOutput.value = args.join(" ");
  updateEstimate();
}

function generateBrowserPublishSessionCommand() {
  const queuePath = els.publishQueue.value.trim();
  if (!queuePath) {
    els.commandOutput.value = "Enter a publish-queue.json path first.";
    return;
  }
  const platforms = selectedPlatforms();
  const args = [
    "python scripts\\browser_publish_session.py",
    `--publish-queue ${quote(queuePath)}`,
    `--out-dir ${quote(outDir())}`
  ];
  if (platforms.length) {
    args.push(`--platforms ${platforms.join(",")}`);
  }
  parseList(els.platformPublishUrls.value).forEach((value) => {
    args.push(`--platform-publish-url ${quote(value)}`);
  });
  if (els.runFormFill.checked) {
    args.push("--run-form-fill");
  }
  if (els.captureBrowserEvidence.checked) {
    args.push("--open-browser");
  }
  if (els.allowLocalhost.checked) {
    args.push("--allow-localhost");
  }
  els.commandOutput.value = args.join(" ");
  updateEstimate();
}

function generateRealEvidenceInboxCommand() {
  const inboxPath = els.evidenceInbox.value.trim();
  if (!inboxPath) {
    els.commandOutput.value = "Enter an evidence inbox folder first.";
    return;
  }
  const args = [
    "python scripts\\real_evidence_inbox.py",
    `--inbox-dir ${quote(inboxPath)}`,
    `--out-dir ${quote(outDir())}`
  ];
  if (els.captureBrowserEvidence.checked) {
    args.push("--capture-browser-assisted");
  }
  if (els.allowLocalhost.checked) {
    args.push("--allow-localhost");
  }
  els.commandOutput.value = args.join(" ");
  updateEstimate();
}

function generatePerformanceMonitorCommand() {
  const args = [
    "python scripts\\performance_monitor.py",
    `--out-dir ${quote(outDir())}`
  ];
  if (els.captureBrowserEvidence.checked) {
    args.push("--capture-browser-assisted");
  }
  if (els.allowLocalhost.checked) {
    args.push("--allow-localhost");
  }
  els.commandOutput.value = args.join(" ");
  updateEstimate();
}

function generateFinalReadinessCommand() {
  const args = [
    "python scripts\\final_capability_readiness.py",
    `--out-dir ${quote(outDir())}`
  ];
  els.commandOutput.value = args.join(" ");
  updateEstimate();
}

function generateAutomationInitCommand() {
  const url = els.productUrl.value.trim();
  const platforms = selectedPlatforms();
  if (!url) {
    els.commandOutput.value = "Enter a product or website URL first.";
    return;
  }
  if (!platforms.length) {
    els.commandOutput.value = "Select at least one platform.";
    return;
  }
  const args = [
    "python scripts\\automation_scheduler.py init",
    `--config ${quote(automationConfig())}`,
    `--job-id ${quote(els.automationJobId.value.trim() || "product-weekly")}`,
    `--browser-url ${quote(url)}`,
    `--platforms ${platforms.join(",")}`,
    `--interval-days ${positiveInt(els.automationIntervalDays.value, 7)}`,
    `--output-root ${quote(automationOutputRoot())}`,
    "--install-browser-if-missing"
  ];
  if (els.autoSearchCompetitors.checked) {
    args.push("--auto-search-competitors");
  }
  if (els.enableMultiQueryDiscovery.checked) {
    args.push("--enable-multi-query-viral-discovery");
  }
  if (els.browserFollowUps.checked) {
    args.push("--run-follow-up-captures");
    args.push("--capture-browser-assisted-follow-ups");
    args.push("--sample-video-frames");
  }
  if (els.enablePublishQueue.checked) {
    args.push("--enable-publish-queue");
  }
  if (els.enableBrowserPublishAssistant.checked) {
    args.push("--enable-browser-publish-assistant");
  }
  if (els.enableBrowserFormFill.checked) {
    args.push("--enable-browser-form-fill");
  }
  if (els.enableMetricsRecovery.checked) {
    args.push("--enable-metrics-recovery");
  }
  if (els.enableNextRoundOptimization.checked) {
    args.push("--enable-next-round-optimization");
  }
  const commands = [args.join(" ")];
  if (els.alsoWindowsTask.checked) {
    commands.push(automationWindowsTaskCommand());
  }
  els.commandOutput.value = commands.join("\n");
  updateEstimate();
}

function generateAutomationRunCommand() {
  const args = [
    "python scripts\\automation_scheduler.py run",
    `--config ${quote(automationConfig())}`,
    "--force"
  ];
  els.commandOutput.value = args.join(" ");
  updateEstimate();
}

function automationWindowsTaskCommand() {
  const args = [
    "python scripts\\automation_scheduler.py windows-task",
    `--config ${quote(automationConfig())}`,
    `--out-file ${quote(els.windowsTaskScript.value.trim() || ".\\register-enhe-promotion-task.ps1")}`,
    "--task-name \"ENHE Promotion Manager\"",
    `--time ${quote(els.windowsTaskTime.value.trim() || "09:00")}`
  ];
  return args.join(" ");
}

async function copyCommand() {
  const value = els.commandOutput.value.trim();
  if (!value) {
    return;
  }
  await navigator.clipboard.writeText(value);
  els.copyCommand.textContent = "Copied";
  setTimeout(() => {
    els.copyCommand.textContent = "Copy";
  }, 1200);
}

async function saveLicense() {
  await chrome.storage.local.set({
    licenseKey: els.licenseKey.value.trim(),
    licenseEndpoint: els.licenseEndpoint.value.trim() || DEFAULT_ENDPOINT,
    usageAuthorizeEndpoint: els.usageAuthorizeEndpoint.value.trim() || DEFAULT_USAGE_AUTHORIZE_ENDPOINT,
    hostedRunEndpoint: els.hostedRunEndpoint.value.trim() || DEFAULT_HOSTED_RUN_ENDPOINT,
    licensePlan: els.plan.value
  });
  els.licenseMessage.textContent = "License settings saved locally.";
}

async function authorizeUsage() {
  const licenseKey = els.licenseKey.value.trim();
  const endpoint = els.usageAuthorizeEndpoint.value.trim() || DEFAULT_USAGE_AUTHORIZE_ENDPOINT;
  const estimate = estimateCredits();
  if (!licenseKey) {
    els.usageMessage.textContent = "Paste a license key before reserving hosted credits.";
    return;
  }
  if (estimate.creditsPerRun <= 0) {
    els.usageMessage.textContent = "This command type does not need hosted credits.";
    return;
  }
  els.usageMessage.textContent = "Requesting usage authorization...";
  const idempotencyKey = createIdempotencyKey();
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        licenseKey,
        workflowType: estimate.workflowType,
        estimatedCredits: estimate.creditsPerRun,
        idempotencyKey,
        commandType: els.commandType.value,
        extensionVersion: chrome.runtime.getManifest().version,
        website: ENHE_SITE
      })
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (!payload.allowed) {
      els.usageMessage.textContent = `Usage blocked: ${payload.reason || "not_allowed"}.`;
      return;
    }
    await chrome.storage.local.set({
      usageAuthorizeEndpoint: endpoint,
      lastUsageId: payload.usageId || "",
      lastUsageWorkflowType: estimate.workflowType,
      lastUsageCreditsReserved: payload.creditsReserved ?? estimate.creditsPerRun,
      lastUsageCommandType: els.commandType.value,
      lastUsageIdempotencyKey: idempotencyKey
    });
    els.usageMessage.textContent = `Reserved ${payload.creditsReserved ?? estimate.creditsPerRun} credits. Remaining: ${payload.creditsRemainingAfterReservation ?? "unknown"}.`;
  } catch (error) {
    els.usageMessage.textContent = `Usage API not reachable. Run locally or manage billing on ENHE website. ${error.message}`;
  }
}

async function validateLicense() {
  const licenseKey = els.licenseKey.value.trim();
  const endpoint = els.licenseEndpoint.value.trim() || DEFAULT_ENDPOINT;
  if (!licenseKey) {
    setLicenseStatus("Local", "");
    els.licenseMessage.textContent = "Paste a license key before validation.";
    return;
  }
  els.licenseMessage.textContent = "Checking license endpoint...";
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        licenseKey,
        requestedPlan: els.plan.value,
        extensionVersion: chrome.runtime.getManifest().version,
        website: ENHE_SITE,
        commandType: els.commandType.value,
        estimatedMonthlyCredits: estimateCredits().credits
      })
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    const active = Boolean(payload.active);
    await chrome.storage.local.set({
      licenseKey,
      licenseEndpoint: endpoint,
      hostedRunEndpoint: payload.hostedRunEndpoint || els.hostedRunEndpoint.value.trim() || DEFAULT_HOSTED_RUN_ENDPOINT,
      licensePlan: String(payload.plan || els.plan.value).toLowerCase(),
      licenseActive: active,
      checkoutUrl: payload.checkoutUrl || CHECKOUT_URL,
      customerPortalUrl: payload.customerPortalUrl || CUSTOMER_PORTAL_URL
    });
    els.hostedRunEndpoint.value = payload.hostedRunEndpoint || els.hostedRunEndpoint.value.trim() || DEFAULT_HOSTED_RUN_ENDPOINT;
    setLicenseStatus(active ? "Active" : "Inactive", active ? "active" : "error");
    els.licenseMessage.textContent = active
      ? `Plan ${payload.plan || els.plan.value}, credits ${payload.creditsRemaining ?? "unknown"}.`
      : "License is not active.";
  } catch (error) {
    await chrome.storage.local.set({ licenseActive: false });
    setLicenseStatus("Offline", "error");
    els.licenseMessage.textContent = `License API not reachable. Manage billing on ENHE website. ${error.message}`;
  }
}

async function copyHostedPayload() {
  try {
    const payload = await buildHostedRunPayload();
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    els.hostedRunMessage.textContent = "Hosted run payload copied.";
  } catch (error) {
    els.hostedRunMessage.textContent = error.message;
  }
}

async function startHostedRun() {
  const endpoint = els.hostedRunEndpoint.value.trim() || DEFAULT_HOSTED_RUN_ENDPOINT;
  let payload;
  try {
    payload = await buildHostedRunPayload();
  } catch (error) {
    els.hostedRunMessage.textContent = error.message;
    return;
  }
  if (payload.estimatedCredits > 0 && !payload.usageId) {
    els.hostedRunMessage.textContent = "Reserve credits before starting a hosted run.";
    return;
  }
  els.hostedRunMessage.textContent = "Submitting hosted run request...";
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const result = await response.json();
    await chrome.storage.local.set({
      hostedRunEndpoint: endpoint,
      lastHostedRunId: result.runId || "",
      lastHostedRunStatus: result.status || ""
    });
    els.hostedRunMessage.textContent = `Hosted run ${result.status || "accepted"}${result.runId ? `: ${result.runId}` : ""}.`;
  } catch (error) {
    els.hostedRunMessage.textContent = `Hosted run API not reachable. Copy the payload or run locally. ${error.message}`;
  }
}

async function buildHostedRunPayload() {
  const licenseKey = els.licenseKey.value.trim();
  const estimate = estimateCredits();
  const url = els.productUrl.value.trim();
  if (!licenseKey) {
    throw new Error("Paste a license key before creating a hosted run payload.");
  }
  if (requiresProductUrl(els.commandType.value) && !url) {
    throw new Error("Enter a product or website URL first.");
  }
  if (requiresPlatforms(els.commandType.value) && !selectedPlatforms().length) {
    throw new Error("Select at least one platform.");
  }
  if (els.commandType.value === "browser_publish_session" && !els.publishQueue.value.trim()) {
    throw new Error("Enter a publish-queue.json path first.");
  }
  if (els.commandType.value === "real_evidence_inbox" && !els.evidenceInbox.value.trim()) {
    throw new Error("Enter an evidence inbox folder first.");
  }
  generateCommand();
  const localCommand = els.commandOutput.value.trim();
  if (!localCommand || /^(Enter|Select)/.test(localCommand)) {
    throw new Error(localCommand || "Generate a command first.");
  }
  const stored = await chrome.storage.local.get([
    "lastUsageId",
    "lastUsageWorkflowType",
    "lastUsageCreditsReserved",
    "lastUsageCommandType"
  ]);
  const usageMatches =
    stored.lastUsageWorkflowType === estimate.workflowType &&
    stored.lastUsageCommandType === els.commandType.value &&
    Number(stored.lastUsageCreditsReserved || 0) >= estimate.creditsPerRun;
  return {
    licenseKey,
    usageId: usageMatches ? stored.lastUsageId || "" : "",
    workflowType: estimate.workflowType,
    estimatedCredits: estimate.creditsPerRun,
    commandType: els.commandType.value,
    extensionVersion: chrome.runtime.getManifest().version,
    website: ENHE_SITE,
    requestSource: "chrome_extension",
    idempotencyKey: createIdempotencyKey(),
    productUrl: url,
    platforms: selectedPlatforms(),
    workflowDepth: els.workflowDepth.value,
    localCommand,
    options: hostedRunOptions(),
    safety: {
      approvalRequiredForOfficialPublish: true,
      finalPublishNotClickedByExtension: true,
      noPlatformSecretsInPayload: true,
      noCaptchaBypass: true
    }
  };
}

function hostedRunOptions() {
  return {
    outputDir: outDir(),
    publishQueue: els.publishQueue.value.trim(),
    publisherUrlOverrides: parseList(els.platformPublishUrls.value),
    evidenceInbox: els.evidenceInbox.value.trim(),
    automationConfig: automationConfig(),
    automationOutputRoot: automationOutputRoot(),
    automationJobId: els.automationJobId.value.trim() || "product-weekly",
    automationIntervalDays: positiveInt(els.automationIntervalDays.value, 7),
    windowsTaskScript: els.windowsTaskScript.value.trim() || ".\\register-enhe-promotion-task.ps1",
    windowsTaskTime: els.windowsTaskTime.value.trim() || "09:00",
    runFormFill: els.runFormFill.checked,
    captureBrowserEvidence: els.captureBrowserEvidence.checked,
    allowLocalhost: els.allowLocalhost.checked,
    autoSearchCompetitors: els.autoSearchCompetitors.checked,
    enableMultiQueryDiscovery: els.enableMultiQueryDiscovery.checked,
    browserFollowUps: els.browserFollowUps.checked,
    enablePublishQueue: els.enablePublishQueue.checked,
    enableBrowserPublishAssistant: els.enableBrowserPublishAssistant.checked,
    enableBrowserFormFill: els.enableBrowserFormFill.checked,
    enableMetricsRecovery: els.enableMetricsRecovery.checked,
    enableNextRoundOptimization: els.enableNextRoundOptimization.checked,
    alsoWindowsTask: els.alsoWindowsTask.checked,
    deepReview: els.deepReview.checked,
    hostedVideo: els.hostedVideo.checked
  };
}

function requiresProductUrl(commandType) {
  return commandType === "skill_entry" || commandType === "automation_init";
}

function requiresPlatforms(commandType) {
  return commandType === "skill_entry" || commandType === "automation_init";
}

async function openCheckout() {
  const estimate = estimateCredits();
  const url = new URL(CHECKOUT_URL);
  url.searchParams.set("plan", els.plan.value);
  url.searchParams.set("source", "extension");
  url.searchParams.set("credits", String(estimate.credits));
  url.searchParams.set("runs", String(estimate.runs));
  url.searchParams.set("workflow", estimate.workflowType);
  await chrome.tabs.create({ url: url.toString() });
}

async function openPortal() {
  const stored = await chrome.storage.local.get(["customerPortalUrl"]);
  const url = new URL(stored.customerPortalUrl || CUSTOMER_PORTAL_URL);
  url.searchParams.set("source", "extension");
  await chrome.tabs.create({ url: url.toString() });
}

function updateEstimate() {
  const estimate = estimateCredits();
  const plan = PLANS[els.plan.value] || PLANS.free;
  const estimatedCost = estimate.credits * COST_PER_CREDIT;
  els.creditMeter.textContent = `${estimate.credits} credits`;
  els.costSummary.textContent = `${plan.label} includes ${plan.credits} credits at USD ${plan.price}/month. ${estimate.label}: ${estimate.creditsPerRun} credits/run, ${estimate.credits} credits planned, estimated gross cost up to USD ${estimatedCost.toFixed(2)}.`;
  if (estimate.credits > plan.credits && plan.price > 0) {
    els.costSummary.textContent += " Add prepaid credits or reduce automation depth.";
  }
}

function estimateCredits() {
  const runs = Math.max(0, Number.parseInt(els.monthlyRuns.value || "0", 10));
  const commandType = els.commandType.value;
  const depth = els.workflowDepth.value;
  let workflowType = commandType;
  let label = COMMAND_LABELS[commandType] || "Workflow";
  let creditsPerRun = 0;

  if (commandType === "skill_entry") {
    workflowType = depth === "playbook" ? "command_only" : depth === "research" ? "research_run" : "standard_run";
    creditsPerRun = depth === "playbook" ? 0 : depth === "research" ? 3 : 4;
    label = depth === "playbook" ? "Playbook command" : depth === "research" ? "Research run" : "Full Skill run";
  }
  if (commandType === "browser_publish_session") {
    workflowType = "browser_publish_session";
    creditsPerRun = 2;
  }
  if (commandType === "real_evidence_inbox") {
    workflowType = "real_evidence_inbox";
    creditsPerRun = 2;
  }
  if (commandType === "performance_monitor") {
    workflowType = "performance_monitor";
    creditsPerRun = 2;
  }
  if (commandType === "final_readiness") {
    workflowType = "final_readiness_audit";
    creditsPerRun = 1;
  }
  if (commandType === "automation_init") {
    workflowType = "automation_config_init";
    creditsPerRun = els.alsoWindowsTask.checked ? 2 : 1;
  }
  if (commandType === "automation_run") {
    workflowType = "automation_due_run";
    creditsPerRun = 4;
  }
  if (commandType === "automation_windows_task") {
    workflowType = "automation_windows_task";
    creditsPerRun = 1;
  }
  if (commandType === "skill_entry" && els.deepReview.checked) {
    creditsPerRun += 15;
  }
  if (commandType === "skill_entry" && els.hostedVideo.checked) {
    creditsPerRun += 3;
  }
  return { runs, workflowType, label, creditsPerRun, credits: runs * creditsPerRun };
}

function setLicenseStatus(label, className) {
  els.licenseStatus.textContent = label;
  els.licenseStatus.className = `status ${className || ""}`.trim();
}

function handleCommandTypeChange() {
  const commandType = els.commandType.value;
  const scope = commandScope(commandType);
  els.commandModeLabel.textContent = COMMAND_LABELS[commandType] || "Workflow";
  Array.from(document.querySelectorAll("[data-command-scope]")).forEach((node) => {
    const scopes = String(node.dataset.commandScope || "").split(/\s+/);
    node.classList.toggle("is-hidden", scope ? !scopes.includes(scope) : true);
  });
  updateEstimate();
}

function commandScope(commandType) {
  if (commandType === "browser_publish_session") {
    return "publish";
  }
  if (commandType === "real_evidence_inbox") {
    return "evidence-inbox";
  }
  if (commandType === "performance_monitor") {
    return "performance";
  }
  if (commandType === "automation_init") {
    return "automation-init";
  }
  if (commandType === "automation_run") {
    return "automation-run";
  }
  if (commandType === "automation_windows_task") {
    return "automation-task";
  }
  return "";
}

function outDir() {
  return els.outDir.value.trim() || ".\\promotion-output";
}

function automationConfig() {
  return els.automationConfig.value.trim() || ".\\promotion-automation.json";
}

function automationOutputRoot() {
  return els.automationOutputRoot.value.trim() || ".\\promotion-output\\automation";
}

function parseList(value) {
  return String(value || "")
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function quote(value) {
  return `"${String(value).replace(/"/g, '\\"')}"`;
}

function positiveInt(value, fallback) {
  const parsed = Number.parseInt(value || "", 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return fallback;
  }
  return parsed;
}

function createIdempotencyKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `pm_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

const ENHE_SITE = "https://www.enhe-tech.com.cn/";
const DEFAULT_ENDPOINT = "https://www.enhe-tech.com.cn/api/promotion-manager/license";
const CHECKOUT_URL = "https://www.enhe-tech.com.cn/promotion-manager/checkout";
const CUSTOMER_PORTAL_URL = "https://www.enhe-tech.com.cn/promotion-manager/billing";

const PLANS = {
  free: { label: "Free", credits: 5, price: 0 },
  starter: { label: "Starter", credits: 60, price: 29 },
  growth: { label: "Growth", credits: 220, price: 99 },
  scale: { label: "Scale", credits: 800, price: 299 }
};

const COST_PER_CREDIT = 0.35;

const els = {
  licenseStatus: document.getElementById("licenseStatus"),
  productUrl: document.getElementById("productUrl"),
  tabTitle: document.getElementById("tabTitle"),
  useTab: document.getElementById("useTab"),
  generate: document.getElementById("generate"),
  selectAll: document.getElementById("selectAll"),
  workflowDepth: document.getElementById("workflowDepth"),
  plan: document.getElementById("plan"),
  monthlyRuns: document.getElementById("monthlyRuns"),
  deepReview: document.getElementById("deepReview"),
  hostedVideo: document.getElementById("hostedVideo"),
  creditMeter: document.getElementById("creditMeter"),
  costSummary: document.getElementById("costSummary"),
  licenseKey: document.getElementById("licenseKey"),
  licenseEndpoint: document.getElementById("licenseEndpoint"),
  saveLicense: document.getElementById("saveLicense"),
  validateLicense: document.getElementById("validateLicense"),
  openCheckout: document.getElementById("openCheckout"),
  openPortal: document.getElementById("openPortal"),
  licenseMessage: document.getElementById("licenseMessage"),
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
els.openCheckout.addEventListener("click", openCheckout);
els.openPortal.addEventListener("click", openPortal);
els.plan.addEventListener("change", updateEstimate);
els.monthlyRuns.addEventListener("input", updateEstimate);
els.deepReview.addEventListener("change", updateEstimate);
els.hostedVideo.addEventListener("change", updateEstimate);
els.workflowDepth.addEventListener("change", updateEstimate);

async function init() {
  const stored = await chrome.storage.local.get(["licenseKey", "licenseEndpoint", "licensePlan", "licenseActive"]);
  els.licenseKey.value = stored.licenseKey || "";
  els.licenseEndpoint.value = stored.licenseEndpoint || DEFAULT_ENDPOINT;
  if (stored.licensePlan) {
    const planKey = String(stored.licensePlan).toLowerCase();
    if (PLANS[planKey]) {
      els.plan.value = planKey;
    }
  }
  setLicenseStatus(stored.licenseActive ? "Active" : "Local", stored.licenseActive ? "active" : "");
  await useCurrentTab();
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
}

function generateCommand() {
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
    "--out-dir .\\promotion-output"
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
    licensePlan: els.plan.value
  });
  els.licenseMessage.textContent = "License settings saved locally.";
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
      licensePlan: String(payload.plan || els.plan.value).toLowerCase(),
      licenseActive: active,
      checkoutUrl: payload.checkoutUrl || CHECKOUT_URL,
      customerPortalUrl: payload.customerPortalUrl || CUSTOMER_PORTAL_URL
    });
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

async function openCheckout() {
  const estimate = estimateCredits();
  const url = new URL(CHECKOUT_URL);
  url.searchParams.set("plan", els.plan.value);
  url.searchParams.set("source", "extension");
  url.searchParams.set("credits", String(estimate.credits));
  url.searchParams.set("runs", String(estimate.runs));
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
  els.costSummary.textContent = `${plan.label} includes ${plan.credits} credits at USD ${plan.price}/month. Planned use: ${estimate.credits} credits, estimated gross cost up to USD ${estimatedCost.toFixed(2)}.`;
  if (estimate.credits > plan.credits && plan.price > 0) {
    els.costSummary.textContent += " Add prepaid credits or reduce automation depth.";
  }
}

function estimateCredits() {
  const runs = Math.max(0, Number.parseInt(els.monthlyRuns.value || "0", 10));
  const depth = els.workflowDepth.value;
  let creditsPerRun = depth === "playbook" ? 0 : depth === "research" ? 3 : 4;
  if (els.deepReview.checked) {
    creditsPerRun += 15;
  }
  if (els.hostedVideo.checked) {
    creditsPerRun += 3;
  }
  return { runs, creditsPerRun, credits: runs * creditsPerRun };
}

function setLicenseStatus(label, className) {
  els.licenseStatus.textContent = label;
  els.licenseStatus.className = `status ${className || ""}`.trim();
}

function quote(value) {
  return `"${String(value).replace(/"/g, '\\"')}"`;
}

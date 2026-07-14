# Extension Bilingual UI and Branded Icon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a verified version 0.5.2 extension package with a persistent Chinese/English popup switch, Chrome-native manifest localization, and ENHE-branded icons.

**Architecture:** Keep command generation and backend contracts unchanged. Add a small translation layer to the existing popup script, annotate the existing HTML with translation keys, localize Chrome-controlled metadata through `_locales`, and replace only packaged icon assets. Store `uiLanguage` beside the existing local extension settings.

**Tech Stack:** Manifest V3, static HTML/CSS/JavaScript, `chrome.storage.local`, `chrome.i18n`, Python `unittest`, PNG assets, existing Python packaging script.

---

## File map

- Modify `docs/legal/privacy-policy.md`: approved retention and data-request wording.
- Modify `backend/license-service/src/hosted-worker.js`: automatic artifact and audit-log retention cleanup.
- Modify `backend/license-service/src/server.js`: start retention cleanup with the API even when hosted execution is disabled.
- Modify `backend/license-service/src/server.test.js`: deterministic 30-day/180-day cleanup regression test.
- Modify `deploy/promotion-manager/.env.production.example` and `deploy/promotion-manager/README.md`: production retention configuration.
- Modify `scripts/test_promotion_manager.py`: regression coverage for bilingual UI, locale completeness, version, icon dimensions/alpha, and ZIP contents.
- Modify `browser-extension/popup.html`: translation keys and upper-right language control.
- Modify `browser-extension/popup.css`: compact segmented switch and top-bar action layout.
- Modify `browser-extension/popup.js`: dictionaries, language persistence, DOM translation, and localized dynamic messages.
- Modify `browser-extension/manifest.json`: version 0.5.2 and Chrome message references.
- Create `browser-extension/_locales/en/messages.json`: English extension metadata.
- Create `browser-extension/_locales/zh_CN/messages.json`: Simplified Chinese extension metadata.
- Replace `browser-extension/icons/icon16.png`, `icon48.png`, and `icon128.png`: ENHE-branded PNG assets; text appears only at 128px.
- Modify `docs/browser-extension.md` and `docs/zh-CN/browser-extension.md`: language behavior and versioned package notes.
- Regenerate `dist/browser-extension-package-report.json`, `dist/browser-extension-package-report.md`, and `dist/enhe-promotion-manager-0.5.2.zip` without touching the user's existing 0.5.0 ZIP or store-assets directory.

### Task 0: Enforce the approved privacy retention policy

**Files:**
- Modify: `docs/legal/privacy-policy.md`
- Modify: `backend/license-service/src/hosted-worker.js`
- Modify: `backend/license-service/src/server.js`
- Modify: `backend/license-service/src/server.test.js`
- Modify: `deploy/promotion-manager/.env.production.example`
- Modify: `deploy/promotion-manager/README.md`

- [ ] **Step 1: Write a failing retention cleanup test**

Import `runRetentionCleanup` from `hosted-worker.js`. Create old and recent hosted-run directories under a temporary output root, a state object with runs finished 31 and 29 days ago, audit events 181 and 179 days old, and a payment record. Run cleanup at a fixed `now` with 30/180-day options. Assert the old directory is removed, the recent directory remains, only the old run has `artifactsDeletedAt`, the 181-day audit event is removed, the 179-day event remains, a deletion audit event is added, and the payment record remains unchanged.

```javascript
const { processNextHostedRun, runRetentionCleanup } = require("./hosted-worker");

test("retention cleanup deletes hosted artifacts after 30 days and audit logs after 180 days", async () => {
  const outputRoot = path.join(tmpRoot, "retention-runs");
  const oldDirectory = path.join(outputRoot, "run_old");
  const recentDirectory = path.join(outputRoot, "run_recent");
  fs.mkdirSync(oldDirectory, { recursive: true });
  fs.mkdirSync(recentDirectory, { recursive: true });
  fs.writeFileSync(path.join(oldDirectory, "artifact.txt"), "old");
  fs.writeFileSync(path.join(recentDirectory, "artifact.txt"), "recent");

  const state = emptyState();
  state.hostedRuns.run_old = {
    id: "run_old", status: "succeeded", finishedAt: "2026-06-14T00:00:00.000Z",
    artifactDirectory: oldDirectory, reportPath: path.join(oldDirectory, "report.json")
  };
  state.hostedRuns.run_recent = {
    id: "run_recent", status: "succeeded", finishedAt: "2026-06-16T00:00:00.000Z",
    artifactDirectory: recentDirectory, reportPath: path.join(recentDirectory, "report.json")
  };
  state.auditLog = [
    { at: "2026-01-15T00:00:00.000Z", action: "old_audit", details: {} },
    { at: "2026-01-17T00:00:00.000Z", action: "recent_audit", details: {} }
  ];
  state.payments.pay_keep = { id: "pay_keep", status: "paid" };
  const retentionStore = { update: async (mutator) => mutator(state) };

  await runRetentionCleanup(retentionStore, {
    outputRoot,
    now: "2026-07-15T00:00:00.000Z",
    artifactRetentionDays: 30,
    auditRetentionDays: 180
  });

  assert.equal(fs.existsSync(oldDirectory), false);
  assert.equal(fs.existsSync(recentDirectory), true);
  assert.equal(state.hostedRuns.run_old.artifactDirectory, "");
  assert.equal(state.hostedRuns.run_recent.artifactDirectory, recentDirectory);
  assert.equal(state.auditLog.some((entry) => entry.action === "old_audit"), false);
  assert.equal(state.auditLog.some((entry) => entry.action === "recent_audit"), true);
  assert.equal(state.auditLog.some((entry) => entry.action === "hosted_artifacts_deleted"), true);
  assert.deepEqual(state.payments.pay_keep, { id: "pay_keep", status: "paid" });
});
```

- [ ] **Step 2: Run the backend test and verify RED**

Run `npm test` from `backend/license-service`.

Expected: failure because `runRetentionCleanup` is not exported.

- [ ] **Step 3: Implement retention cleanup**

Add 30-day artifact and 180-day audit defaults, safe path containment, fixed-time injection for testing, and `startRetentionCleanup`. Only delete completed-run artifact directories inside `HOSTED_RUN_OUTPUT_ROOT`. Clear artifact paths and record `artifactsDeletedAt`; never delete account, license, payment, refund, subscription, or legally required accounting records.

- [ ] **Step 4: Start cleanup independently of hosted execution**

Import `startRetentionCleanup` in `server.js` and start it after store initialization. Use a six-hour default interval. Keep `HOSTED_WORKER_ENABLED` behavior unchanged so enabling retention does not start hosted jobs.

- [ ] **Step 5: Add production configuration**

```dotenv
HOSTED_ARTIFACT_RETENTION_DAYS=30
SECURITY_AUDIT_LOG_RETENTION_DAYS=180
RETENTION_CLEANUP_INTERVAL_MS=21600000
```

Document that the API performs cleanup even when the hosted worker is disabled.

- [ ] **Step 6: Apply the approved legal wording**

Set the effective date to 2026-07-15 and state exactly that Hosted Task artifacts are automatically deleted 30 days after completion; security and audit logs are retained for 180 days; payment, refund, and legally required accounting records are retained under applicable law; and users may email `huqingwei5942@gmail.com` to request access to or deletion of data that is not subject to mandatory retention.

- [ ] **Step 7: Verify GREEN**

Run `npm test` from `backend/license-service` and the privacy-policy regression test in `scripts/test_promotion_manager.py`.

Expected: both commands exit 0.

### Task 1: Add failing bilingual and icon regression tests

**Files:**
- Modify: `scripts/test_promotion_manager.py`

- [ ] **Step 1: Add the standard-library PNG header import**

```python
import struct
```

- [ ] **Step 2: Add a failing bilingual behavior test**

```python
def test_browser_extension_popup_is_bilingual_and_remembers_language(self) -> None:
    manifest = json.loads((BROWSER_EXTENSION / "manifest.json").read_text(encoding="utf-8"))
    popup = (BROWSER_EXTENSION / "popup.html").read_text(encoding="utf-8")
    script = (BROWSER_EXTENSION / "popup.js").read_text(encoding="utf-8")

    self.assertEqual(manifest["version"], "0.5.2")
    self.assertEqual(manifest["default_locale"], "en")
    self.assertEqual(manifest["name"], "__MSG_extensionName__")
    self.assertIn('id="languageZh"', popup)
    self.assertIn('id="languageEn"', popup)
    self.assertIn("data-i18n=", popup)
    self.assertIn("data-i18n-placeholder=", popup)
    self.assertIn("chrome.i18n.getUILanguage", script)
    self.assertIn('"uiLanguage"', script)
    self.assertIn("chrome.storage.local.set({ uiLanguage", script)
    self.assertIn('"zh-CN"', script)
    self.assertIn('"en"', script)
    self.assertIn("aria-pressed", script)

    for locale in ["en", "zh_CN"]:
        messages = json.loads(
            (BROWSER_EXTENSION / "_locales" / locale / "messages.json").read_text(encoding="utf-8")
        )
        for key in ["extensionName", "extensionShortName", "extensionDescription", "actionTitle"]:
            self.assertTrue(messages[key]["message"].strip())
```

- [ ] **Step 3: Add a failing icon format test**

```python
def test_browser_extension_icons_have_expected_size_and_alpha(self) -> None:
    for size in [16, 48, 128]:
        data = (BROWSER_EXTENSION / "icons" / f"icon{size}.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((width, height), (size, size))
        self.assertEqual(bit_depth, 8)
        self.assertIn(color_type, {4, 6})
```

- [ ] **Step 4: Extend the package test**

```python
self.assertEqual(report["version"], "0.5.2")
self.assertIn("_locales/en/messages.json", names)
self.assertIn("_locales/zh_CN/messages.json", names)
```

- [ ] **Step 5: Run targeted tests and verify RED**

Run:

```powershell
python scripts\test_promotion_manager.py PromotionManagerScriptTest.test_browser_extension_popup_is_bilingual_and_remembers_language PromotionManagerScriptTest.test_browser_extension_icons_have_expected_size_and_alpha
```

Expected: failures because version 0.5.2, language controls, locale files, and branded alpha icons do not exist yet.

### Task 2: Generate and install ENHE icon assets

**Files:**
- Source: `E:/AiProject/01.网站相关资料/LOGO/enhe_logo_final_exact_package/enhe_icon_gradient_transparent.png`
- Modify: `browser-extension/icons/icon16.png`
- Modify: `browser-extension/icons/icon48.png`
- Modify: `browser-extension/icons/icon128.png`

- [ ] **Step 1: Generate the approved 128px composition with the image tool**

Use this exact prompt with the supplied ENHE PNG as the edit target:

```text
Use case: precise-object-edit
Asset type: Chrome Web Store extension icon
Primary request: create a clean square icon composition using the supplied ENHE gradient logo unchanged.
Composition: a front-facing dark navy rounded 96x96 tile centered inside a transparent 128x128 canvas with 16px transparent padding; center the original ENHE gradient mark in the upper portion; place exact text "ENHE" and "PROMOTION MANAGER" on two centered lines beneath it.
Text: modern geometric sans serif, white, crisp, no letter distortion.
Constraints: preserve the source logo colors, proportions, and geometry; no outer border, no large shadow, no perspective, no watermark; must remain readable on light and dark backgrounds.
```

- [ ] **Step 2: Inspect the generated image at native size**

Verify the ENHE mark is not redrawn incorrectly, both text lines are exact, corners are transparent, and the content stays inside the 16px safe area. If text is wrong, run one targeted edit that changes only the text.

- [ ] **Step 3: Create text-free 48px and 16px variants**

Use the same ENHE mark and dark rounded tile, omit all text, keep the front-facing composition, and preserve transparent margins appropriate to each canvas.

- [ ] **Step 4: Install assets non-destructively, then wire the approved files**

Immediately after each built-in image result, use the result's reported local path as `$generated128`, `$generated48`, or `$generated16`. Copy generated finals into versioned sibling files for inspection, then replace only the three manifest-referenced files after validation:

```powershell
Copy-Item -LiteralPath $generated128 -Destination browser-extension\icons\icon128-v2.png
Copy-Item -LiteralPath $generated48 -Destination browser-extension\icons\icon48-v2.png
Copy-Item -LiteralPath $generated16 -Destination browser-extension\icons\icon16-v2.png
Copy-Item browser-extension\icons\icon128-v2.png browser-extension\icons\icon128.png -Force
Copy-Item browser-extension\icons\icon48-v2.png browser-extension\icons\icon48.png -Force
Copy-Item browser-extension\icons\icon16-v2.png browser-extension\icons\icon16.png -Force
```

- [ ] **Step 5: Run the icon test and verify GREEN**

Run:

```powershell
python scripts\test_promotion_manager.py PromotionManagerScriptTest.test_browser_extension_icons_have_expected_size_and_alpha
```

Expected: `OK`.

### Task 3: Add Chrome metadata localization and popup translation controls

**Files:**
- Modify: `browser-extension/manifest.json`
- Create: `browser-extension/_locales/en/messages.json`
- Create: `browser-extension/_locales/zh_CN/messages.json`
- Modify: `browser-extension/popup.html`
- Modify: `browser-extension/popup.css`

- [ ] **Step 1: Localize manifest metadata and bump the version**

Set:

```json
{
  "name": "__MSG_extensionName__",
  "short_name": "__MSG_extensionShortName__",
  "version": "0.5.2",
  "description": "__MSG_extensionDescription__",
  "default_locale": "en"
}
```

Set `action.default_title` to `__MSG_actionTitle__` and retain all existing permissions, icons, host permissions, and CSP exactly.

- [ ] **Step 2: Add complete manifest locale files**

English:

```json
{
  "extensionName": {"message": "ENHE Promotion Manager"},
  "extensionShortName": {"message": "ENHE Promote"},
  "extensionDescription": {"message": "Capture product pages and build guarded ENHE commands or hosted runs for copy, video, publishing, and performance reviews."},
  "actionTitle": {"message": "ENHE Promotion Manager"}
}
```

Simplified Chinese:

```json
{
  "extensionName": {"message": "ENHE 推广管理器"},
  "extensionShortName": {"message": "ENHE 推广"},
  "extensionDescription": {"message": "采集产品页面，生成受控的 ENHE 本地命令或托管任务，用于文案、视频、发布和效果复盘。"},
  "actionTitle": {"message": "ENHE 推广管理器"}
}
```

- [ ] **Step 3: Add the upper-right language switch**

Add beside the existing license status:

```html
<div class="topbar-actions">
  <div class="language-switch" role="group" data-i18n-aria-label="languageSwitchLabel">
    <button id="languageZh" type="button" class="language-option" aria-pressed="false">中文</button>
    <button id="languageEn" type="button" class="language-option" aria-pressed="true">EN</button>
  </div>
  <span class="status" id="licenseStatus" data-i18n="statusLocal">Local</span>
</div>
```

- [ ] **Step 4: Annotate every visible popup string**

Use `data-i18n` for text nodes, `data-i18n-placeholder` for placeholders, and `data-i18n-aria-label` for accessibility labels. Keep the existing English literal as the safe no-JavaScript fallback. Do not annotate CLI paths, URLs, product/platform brand names, or user-entered values.

- [ ] **Step 5: Style the control without changing the overall layout**

```css
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.language-switch {
  display: inline-flex;
  padding: 2px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--panel);
}

.language-option {
  min-height: 24px;
  border: 0;
  border-radius: 5px;
  padding: 0 7px;
  color: var(--muted);
  background: transparent;
  font-size: 11px;
}

.language-option[aria-pressed="true"] {
  color: var(--accent-ink);
  background: var(--accent);
  font-weight: 700;
}
```

### Task 4: Implement persistent popup translations

**Files:**
- Modify: `browser-extension/popup.js`

- [ ] **Step 1: Add translation state and helpers**

```javascript
const SUPPORTED_LANGUAGES = new Set(["en", "zh-CN"]);
let currentLanguage = "en";
const messageState = new Map();
let commandMessage = null;

function normalizeLanguage(value) {
  const normalized = String(value || "").toLowerCase();
  return normalized.startsWith("zh") ? "zh-CN" : "en";
}

function t(key, params = {}) {
  const template = TRANSLATIONS[currentLanguage]?.[key] || TRANSLATIONS.en[key] || key;
  return Object.entries(params).reduce(
    (value, [name, replacement]) => value.replaceAll(`{${name}}`, String(replacement)),
    template
  );
}

function setMessage(element, key, params = {}) {
  messageState.set(element, { key, params });
  element.textContent = t(key, params);
}
```

- [ ] **Step 2: Add flat English and Chinese dictionaries**

Create identical key sets covering every `data-i18n`, placeholder, aria label, command-mode label, status, validation, copied/saved state, API progress/result/error, and pricing summary. Chinese terminology must consistently use `推广管理器`, `积分`, `托管任务`, `发布队列`, `证据收件箱`, and `效果监控`.

- [ ] **Step 3: Apply and persist language**

```javascript
async function setLanguage(language, persist = true) {
  currentLanguage = SUPPORTED_LANGUAGES.has(language) ? language : normalizeLanguage(language);
  document.documentElement.lang = currentLanguage;
  applyTranslations();
  if (persist) {
    await chrome.storage.local.set({ uiLanguage: currentLanguage });
  }
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel));
  });
  els.languageZh.setAttribute("aria-pressed", String(currentLanguage === "zh-CN"));
  els.languageEn.setAttribute("aria-pressed", String(currentLanguage === "en"));
  messageState.forEach(({ key, params }, element) => {
    element.textContent = t(key, params);
  });
  if (commandMessage) {
    els.commandOutput.value = t(commandMessage.key, commandMessage.params);
  }
  handleCommandTypeChange();
}
```

- [ ] **Step 4: Update initialization**

Read `uiLanguage` with existing settings. Before tab capture, call:

```javascript
const initialLanguage = stored.uiLanguage || chrome.i18n.getUILanguage();
await setLanguage(normalizeLanguage(initialLanguage), !stored.uiLanguage);
```

Bind both language buttons to `setLanguage("zh-CN")` and `setLanguage("en")`.

- [ ] **Step 5: Convert dynamic strings**

Replace direct user-visible `textContent` assignments and validation literals with `setMessage`, `setCommandMessage`, or `t`. Leave generated command syntax unchanged. Preserve API error details as `{error}`, HTTP status values, run IDs, URLs, plan names, and credit counts.

- [ ] **Step 6: Verify GREEN**

Run:

```powershell
python scripts\test_promotion_manager.py PromotionManagerScriptTest.test_browser_extension_popup_is_bilingual_and_remembers_language PromotionManagerScriptTest.test_browser_extension_manifest_popup_and_subscription_ui_are_static_mv3
```

Expected: `OK`.

### Task 5: Document, package, and verify version 0.5.2

**Files:**
- Modify: `docs/browser-extension.md`
- Modify: `docs/zh-CN/browser-extension.md`
- Generate: `dist/enhe-promotion-manager-0.5.2.zip`
- Generate: `dist/browser-extension-package-report.json`
- Generate: `dist/browser-extension-package-report.md`

- [ ] **Step 1: Document language behavior**

English documentation must say the popup follows Chrome on first launch, stores the manual choice locally, and does not upload language preference. Chinese documentation must state the same behavior in Chinese.

- [ ] **Step 2: Build the package**

```powershell
python scripts\package_browser_extension.py --out-dir .\dist
```

Expected: `Browser extension package written to: ...enhe-promotion-manager-0.5.2.zip`.

- [ ] **Step 3: Run targeted package tests**

```powershell
python scripts\test_promotion_manager.py PromotionManagerScriptTest.test_browser_extension_package_script_builds_store_submission_zip
```

Expected: `OK`, with both `_locales` files present in the ZIP.

- [ ] **Step 4: Run the full verification suite**

```powershell
python scripts\test_promotion_manager.py
python -m compileall -q scripts
git diff --check
```

Expected: all tests pass, compile command exits 0, and diff check is empty.

- [ ] **Step 5: Inspect the final icon and package contents**

Open `browser-extension/icons/icon128.png` at native size and list the ZIP entries. Confirm exact ENHE text, correct logo geometry, transparent corners, locale files, and no remote executable code.

- [ ] **Step 6: Commit only task-owned changes**

```powershell
git add browser-extension docs/browser-extension.md docs/zh-CN/browser-extension.md scripts/test_promotion_manager.py dist/browser-extension-package-report.json dist/browser-extension-package-report.md dist/enhe-promotion-manager-0.5.2.zip docs/superpowers/plans/2026-07-15-extension-i18n-icon-implementation.md
git commit -m "feat: add bilingual extension UI and ENHE icons"
```

Do not stage `dist/enhe-promotion-manager-0.5.0.zip` or unrelated files under `dist/store-assets/`.

- [ ] **Step 7: Push the existing feature branch**

```powershell
git push origin codex/github-readiness-missing
```

Expected: existing PR #1 receives the version 0.5.2 implementation commit. Do not upload the package to Chrome Web Store while version 0.5.1 remains under review unless the user separately authorizes that external action.

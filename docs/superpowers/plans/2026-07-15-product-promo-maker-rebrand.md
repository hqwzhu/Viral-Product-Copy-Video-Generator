# ENHE Product Promo Maker Rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand every current user-facing surface to ENHE Product Promo Maker / ENHE 产品推广素材生成器, produce a validated v0.5.3 store package, merge one PR, deploy the merged public pages, and prepare or submit the existing store item without changing compatibility identifiers.

**Architecture:** Keep all internal routes, service names, storage keys, package identifiers, and payment/license behavior unchanged. Change only presentation-layer strings, localized metadata, the customer-visible ZPAY order name, current documentation, and the 128 px store icon; enforce the boundary with focused regression tests and a scoped retired-name scan. Preserve the submitted v0.5.2 ZIP and reports, and write v0.5.3 artifacts into a separate versioned directory.

**Tech Stack:** Chrome Manifest V3, vanilla HTML/CSS/JavaScript, Chrome `_locales`, Node.js 20 with `node:test`, Python 3 `unittest`, Express, ZPAY, Git/GitHub CLI, Playwright, systemd, Nginx.

---

## File Map

The implementation changes these existing responsibilities without restructuring them:

- `browser-extension/manifest.json`: extension version and localized metadata references.
- `browser-extension/_locales/en/messages.json`: English store and toolbar identity.
- `browser-extension/_locales/zh_CN/messages.json`: Simplified Chinese store and toolbar identity.
- `browser-extension/popup.html`: fallback title, full product heading, and promise element.
- `browser-extension/popup.css`: compact styling for the promise beneath the heading.
- `browser-extension/popup.js`: English/Chinese popup identity, promise, and generated Windows task label.
- `browser-extension/billing-contract.json`: human-readable billing contract name only; all endpoints and contract fields remain stable.
- `browser-extension/icons/icon128.png`: active 128 px store icon.
- `browser-extension/icons/icon128-v3.png`: immutable v0.5.3 source copy of the new 128 px icon.
- `backend/license-service/src/server.js`: checkout, billing, result, run-status, legal fallback, and process-log product labels.
- `backend/license-service/src/zpay.js`: customer-visible ZPAY order name.
- `backend/license-service/src/server.test.js`: public page, legal alias, QR-payment, amount, signature, and order-name regressions.
- `backend/license-service/src/migrate.js`, `backend/license-service/src/worker.js`: operator-visible log labels only.
- `backend/license-service/package.json`, `backend/license-service/README.md`: human-readable package description and current operations guide.
- `deploy/promotion-manager/README.md`: current deployment guide while retaining every existing path and service command.
- `deploy/promotion-manager/enhe-promotion-manager-api.service`, `deploy/promotion-manager/enhe-promotion-manager-worker.service`: systemd descriptions only; filenames and unit dependencies remain unchanged.
- `docs/legal/*.md`: approved new name plus a single transition alias at the first product reference.
- `docs/store/*.md`: localized listing, review copy, screenshot plan, and exact v0.5.3 asset names.
- `docs/browser-extension.md`, `docs/zh-CN/browser-extension.md`, `docs/extension-store-submission.md`, `docs/zh-CN/extension-store-submission.md`: current extension and submission instructions.
- `README.md`, `README.en.md`, `README.zh-CN.md`, current operator docs, current reference examples, and CLI help/log text: presentation-name updates only.
- `scripts/test_promotion_manager.py`: identity, compatibility, documentation, icon, and package regressions.
- `dist/v0.5.3/`: new package report, v0.5.3 ZIP, and English/Chinese store screenshots. Existing files at `dist/enhe-promotion-manager-0.5.2.zip` and the root v0.5.2 reports are not modified.

## Non-Negotiable Compatibility Boundary

- Keep `/promotion-manager/` and `/api/promotion-manager/` URL paths unchanged.
- Keep `enhe-promotion-manager-*` systemd unit filenames and dependencies unchanged.
- Keep `/opt/enhe/promotion-manager/`, `/var/lib/enhe-promotion-manager/`, and `/etc/enhe-promotion-manager/` unchanged.
- Keep `promotion_manager_state`, existing license/payment records, `pm_live_` keys, environment variables, npm package names, Python filenames/modules, report schemas, and report paths unchanged.
- Keep Chrome Web Store item ID `dloklkbnmoigemnfigbkibogmgbieppl`; update that item only and never create a second item.
- Keep Starter ¥19, Growth ¥59, Scale ¥199, 30-day terms, desktop QR payment, mobile direct payment, payment signatures, and License Key behavior unchanged.
- Keep the committed v0.5.2 ZIP and its evidence byte-for-byte unchanged.
- Permit the retired English name only inside the one-time legal transition aliases and historical specifications, plans, release records, old ZIPs, and previous PR evidence.
- Keep the approved marketing short name `ENHE Promo Maker` for the store icon and compact copy, but use `ENHE Promo` only for Chrome's technical English `short_name`: the approved name is 16 characters while Chrome's official manifest reference sets a 12-character maximum. The approved Chinese `ENHE 推广素材` is 9 characters and needs no adaptation. Source: https://developer.chrome.com/docs/extensions/reference/manifest

### Task 1: Lock the localized extension identity and version

**Files:**
- Modify: `scripts/test_promotion_manager.py:6808-7010`
- Modify: `browser-extension/manifest.json:1-26`
- Modify: `browser-extension/_locales/en/messages.json:1-14`
- Modify: `browser-extension/_locales/zh_CN/messages.json:1-14`
- Modify: `browser-extension/popup.html:1-23`
- Modify: `browser-extension/popup.css:49-82`
- Modify: `browser-extension/popup.js:8-162`
- Modify: `browser-extension/billing-contract.json:1-4`

- [ ] **Step 1: Add a failing identity regression and update the package expectation**

Add this focused test beside the existing extension localization test, and change the existing package report expectation from `0.5.2` to `0.5.3`:

```python
def test_browser_extension_uses_approved_product_identity(self) -> None:
    manifest = json.loads((BROWSER_EXTENSION / "manifest.json").read_text(encoding="utf-8"))
    popup = (BROWSER_EXTENSION / "popup.html").read_text(encoding="utf-8")
    script = (BROWSER_EXTENSION / "popup.js").read_text(encoding="utf-8")
    contract = json.loads((BROWSER_EXTENSION / "billing-contract.json").read_text(encoding="utf-8"))
    expected = {
        "en": {
            "extensionName": "ENHE Product Promo Maker",
            "extensionShortName": "ENHE Promo",
            "actionTitle": "ENHE Product Promo Maker",
        },
        "zh_CN": {
            "extensionName": "ENHE 产品推广素材生成器",
            "extensionShortName": "ENHE 推广素材",
            "actionTitle": "ENHE 产品推广素材生成器",
        },
    }

    self.assertEqual(manifest["version"], "0.5.3")
    self.assertEqual(manifest["manifest_version"], 3)
    self.assertEqual(manifest["permissions"], ["activeTab", "storage", "clipboardWrite"])
    self.assertEqual(manifest["host_permissions"], ["https://www.enhe-tech.com.cn/*"])
    for locale, values in expected.items():
        messages = json.loads(
            (BROWSER_EXTENSION / "_locales" / locale / "messages.json").read_text(encoding="utf-8")
        )
        for key, value in values.items():
            self.assertEqual(messages[key]["message"], value)
        self.assertLessEqual(len(messages["extensionShortName"]["message"]), 12)
        self.assertLessEqual(len(messages["extensionDescription"]["message"]), 132)

    self.assertIn('data-i18n="productPromise"', popup)
    self.assertIn("Turn product pages into promotional copy, video scripts, and publishing assets.", script)
    self.assertIn("把产品网页变成推广文案、视频脚本和发布素材", script)
    self.assertEqual(contract["name"], "ENHE Product Promo Maker Billing Contract")
    for text in [popup, script, json.dumps(expected, ensure_ascii=False)]:
        self.assertNotIn("ENHE 推广管理器", text)

# In test_browser_extension_popup_is_bilingual_and_remembers_language:
self.assertEqual(manifest["version"], "0.5.3")

# In test_browser_extension_package_script_builds_store_submission_zip:
self.assertEqual(report["version"], "0.5.3")
self.assertTrue(str(package_path).endswith("enhe-promotion-manager-0.5.3.zip"))
```

- [ ] **Step 2: Run the focused test and confirm it fails for the old identity**

Run:

```powershell
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_uses_approved_product_identity -v
```

Expected: `FAIL` because the manifest is `0.5.2` and the locale names still contain the retired product name.

- [ ] **Step 3: Update the manifest, locale metadata, popup promise, and billing display name**

Set `browser-extension/manifest.json` to version `0.5.3` without changing permissions, host permissions, CSP, icon paths, or localized token references:

```json
{
  "manifest_version": 3,
  "name": "__MSG_extensionName__",
  "short_name": "__MSG_extensionShortName__",
  "version": "0.5.3",
  "description": "__MSG_extensionDescription__",
  "default_locale": "en"
}
```

Use these exact English locale values:

```json
{
  "extensionName": { "message": "ENHE Product Promo Maker" },
  "extensionShortName": { "message": "ENHE Promo" },
  "extensionDescription": {
    "message": "Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks."
  },
  "actionTitle": { "message": "ENHE Product Promo Maker" }
}
```

Use these exact Simplified Chinese locale values:

```json
{
  "extensionName": { "message": "ENHE 产品推广素材生成器" },
  "extensionShortName": { "message": "ENHE 推广素材" },
  "extensionDescription": {
    "message": "把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。"
  },
  "actionTitle": { "message": "ENHE 产品推广素材生成器" }
}
```

Change the fallback title and heading and add the first explanatory sentence in `popup.html`:

```html
<title>ENHE Product Promo Maker</title>
...
<p class="eyebrow">ENHE AI</p>
<h1 data-i18n="appTitle">ENHE Product Promo Maker</h1>
<p class="product-promise" data-i18n="productPromise">Turn product pages into promotional copy, video scripts, and publishing assets.</p>
```

Add only this focused styling:

```css
.product-promise {
  max-width: 260px;
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.35;
}
```

Set these exact translation entries in `popup.js` while leaving all functional keys intact:

```javascript
const EN_TRANSLATIONS = Object.freeze({
  appTitle: "ENHE Product Promo Maker",
  productPromise: "Turn product pages into promotional copy, video scripts, and publishing assets.",
  // existing English keys remain unchanged
});

const ZH_TRANSLATIONS = Object.freeze({
  appTitle: "ENHE 产品推广素材生成器",
  productPromise: "把产品网页变成推广文案、视频脚本和发布素材",
  // existing Chinese keys remain unchanged
});
```

Change only the human-readable contract name:

```json
"name": "ENHE Product Promo Maker Billing Contract"
```

- [ ] **Step 4: Run extension identity, localization, and package tests**

Run:

```powershell
python -m unittest `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_uses_approved_product_identity `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_popup_is_bilingual_and_remembers_language `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_package_script_builds_store_submission_zip -v
```

Expected: three tests pass; the temporary package report says `ready`, version `0.5.3`, and package filename `enhe-promotion-manager-0.5.3.zip`.

- [ ] **Step 5: Commit the localized extension identity**

```powershell
git add -- browser-extension/manifest.json browser-extension/_locales/en/messages.json browser-extension/_locales/zh_CN/messages.json browser-extension/popup.html browser-extension/popup.css browser-extension/popup.js browser-extension/billing-contract.json scripts/test_promotion_manager.py
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "feat: rename extension to product promo maker"
```

Expected: one commit containing only extension presentation, version, billing display name, and focused tests.

### Task 2: Replace the 128 px store icon label

**Files:**
- Modify: `scripts/test_promotion_manager.py:6960-6971`
- Create: `browser-extension/icons/icon128-v3.png`
- Modify: `browser-extension/icons/icon128.png`
- Preserve: `browser-extension/icons/icon16.png`, `browser-extension/icons/icon48.png`, and all `*-v2.png` files

- [ ] **Step 1: Update the icon regression to require a v3 store icon while preserving toolbar icons**

Replace the versioned-icon selection inside `test_browser_extension_icons_have_expected_size_and_alpha` with:

```python
for size in [16, 48, 128]:
    icon_path = BROWSER_EXTENSION / "icons" / f"icon{size}.png"
    version_suffix = "v3" if size == 128 else "v2"
    versioned_path = BROWSER_EXTENSION / "icons" / f"icon{size}-{version_suffix}.png"
    self.assertTrue(versioned_path.exists(), versioned_path)
    data = icon_path.read_bytes()
    self.assertEqual(data, versioned_path.read_bytes())
    self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    self.assertEqual((width, height), (size, size))
    self.assertEqual(bit_depth, 8)
    self.assertIn(color_type, {4, 6})

previous_store_icon = BROWSER_EXTENSION / "icons" / "icon128-v2.png"
current_store_icon = BROWSER_EXTENSION / "icons" / "icon128-v3.png"
self.assertNotEqual(previous_store_icon.read_bytes(), current_store_icon.read_bytes())
```

- [ ] **Step 2: Run the icon test and confirm the v3 asset is missing**

Run:

```powershell
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_icons_have_expected_size_and_alpha -v
```

Expected: `FAIL` because `browser-extension/icons/icon128-v3.png` does not exist.

- [ ] **Step 3: Edit the approved icon with the image-generation skill**

Use the `imagegen` skill with `browser-extension/icons/icon128-v2.png` as the referenced image and this exact edit instruction:

```text
Preserve the existing 128 by 128 transparent ENHE store icon exactly: same near-black rounded square, same centered multicolor ENHE website logo, same white ENHE wordmark, spacing, lighting, and safe margins. Replace only the tiny bottom label “PROMOTION MANAGER” with the exact uppercase text “ENHE PROMO MAKER”. Keep the new label centered, crisp, white, and legible at 128 px. Do not add any other text, symbols, borders, shadows, or background. Return a square transparent PNG.
```

Save the edited result as `browser-extension/icons/icon128-v3.png`, verify it visually with `view_image`, confirm that the text reads exactly `ENHE PROMO MAKER`, then copy the approved binary to `browser-extension/icons/icon128.png`. Do not regenerate the text-free 16 px and 48 px toolbar icons.

- [ ] **Step 4: Verify dimensions, alpha, and binary version linkage**

Run:

```powershell
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_icons_have_expected_size_and_alpha -v
```

Expected: `PASS`; 16/48 active icons equal their v2 copies, the 128 active icon equals its v3 copy, and the 128 v3 binary differs from v2.

- [ ] **Step 5: Commit the store icon only**

```powershell
git add -- browser-extension/icons/icon128.png browser-extension/icons/icon128-v3.png scripts/test_promotion_manager.py
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "feat: update product promo maker store icon"
```

Expected: the commit contains two 128 px PNGs and the focused icon test; the existing v2 assets remain unchanged.

### Task 3: Rename checkout, billing, run status, and ZPAY order labels

**Files:**
- Modify: `backend/license-service/src/server.test.js:185-330`
- Modify: `backend/license-service/src/server.js:762-1101`
- Modify: `backend/license-service/src/zpay.js:45-66`

- [ ] **Step 1: Add failing public-page and provider-name assertions**

Add these assertions to the existing ZPAY test after reading `checkoutHtml`:

```javascript
assert.match(checkoutHtml, /ENHE Product Promo Maker Checkout/);
assert.match(checkoutHtml, /ENHE 产品推广素材生成器 国内支付/);
assert.doesNotMatch(checkoutHtml, /ENHE 推广管理器/);
```

Fetch and check the billing page in the same test:

```javascript
const billingPage = await fetch(`${baseUrl}/promotion-manager/billing`);
assert.equal(billingPage.status, 200);
const billingHtml = await billingPage.text();
assert.match(billingHtml, /ENHE Product Promo Maker billing/);
assert.match(billingHtml, /ENHE 产品推广素材生成器 账单/);
```

Change the existing ZPAY provider expectations to:

```javascript
assert.equal(providerRequest.name, "ENHE Product Promo Maker Starter");
assert.equal(qrProviderRequest.name, "ENHE Product Promo Maker Growth");
```

Add this assertion after the hosted run succeeds in `license service queues and completes a hosted worker run`:

```javascript
const runPage = await getText(`${baseUrl}/promotion-manager/runs/${queued.runId}`);
assert.match(runPage, /ENHE Product Promo Maker Run/);
assert.doesNotMatch(runPage, /ENHE Promotion Manager Run/);
```

Add these assertions after reading `successHtml`:

```javascript
assert.match(successHtml, /ENHE Product Promo Maker/);
assert.match(successHtml, /ENHE 产品推广素材生成器/);
```

- [ ] **Step 2: Run the backend tests and confirm presentation assertions fail**

Run:

```powershell
Push-Location backend/license-service
npm test
$status = $LASTEXITCODE
Pop-Location
if ($status -eq 0) { exit 1 }
```

Expected: failures show the retired checkout, billing, run-title, and ZPAY provider names; amount, QR, cookie, callback signature, and license assertions still pass up to those checks.

- [ ] **Step 3: Replace only customer-visible names**

Use these exact `server.js` values:

```javascript
// renderRunPage
<title>ENHE Product Promo Maker Run ${runId}</title>

// renderZpayCheckoutPage messages
title: "ENHE 产品推广素材生成器 国内支付"
title: "ENHE Product Promo Maker Checkout"

// checkout fallback HTML
<title>ENHE 产品推广素材生成器 国内支付</title>
<h1 data-i18n="title">ENHE 产品推广素材生成器 国内支付</h1>

// renderCheckoutResult billing messages
title: "ENHE Product Promo Maker billing"
title: "ENHE 产品推广素材生成器 账单"

// renderCheckoutResult localized brand in every payment/billing result panel
const resultPanel = (language, productName, title, message, backLabel, licenseLabel, hidden) => `
  <section data-language-panel="${language}"${hidden ? " hidden" : ""}>
    <p class="product-name">${escapeHtml(productName)}</p>
    <h1>${escapeHtml(title)}</h1>
    ${licenseKey
      ? `<p>${escapeHtml(licenseLabel)}</p><p><code>${escapeHtml(licenseKey)}</code></p>`
      : `<p>${escapeHtml(message)}</p>`}
    <p><a href="/promotion-manager/checkout">${escapeHtml(backLabel)}</a></p>
  </section>`;

${resultPanel("en", "ENHE Product Promo Maker", content.en.title, content.en.message, "Return to checkout", "License key", false)}
${resultPanel("zh-CN", "ENHE 产品推广素材生成器", content.zh.title, content.zh.message, "返回结算页", "许可证密钥", true)}

// renderLegalPage fallback only
const title = firstHeading(markdown) || "ENHE Product Promo Maker";
```

Change only the ZPAY display name in `zpay.js`:

```javascript
name: `ENHE Product Promo Maker ${labelPlan(input.plan)}`,
```

Do not touch the order number prefix, amount formatting, callback URLs, signing fields, cookie names, API routes, plan credits, or license generation.

- [ ] **Step 4: Run the backend tests**

Run:

```powershell
Push-Location backend/license-service
npm test
$status = $LASTEXITCODE
Pop-Location
if ($status -ne 0) { exit $status }
```

Expected: all Node tests pass, including exact CNY amounts, signed callbacks, QR response, License Key hashing, and the new provider order names.

- [ ] **Step 5: Commit the public transactional labels**

```powershell
git add -- backend/license-service/src/server.js backend/license-service/src/zpay.js backend/license-service/src/server.test.js
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "feat: rename public payment surfaces"
```

### Task 4: Apply the one-time legal transition aliases

**Files:**
- Modify: `docs/legal/privacy-policy.md:1-9`
- Modify: `docs/legal/privacy-policy.zh-CN.md:1-9`
- Modify: `docs/legal/terms-of-service.md:1-10`
- Modify: `docs/legal/refund-policy.md:1-10`
- Modify: `docs/legal/support.md:1-10`
- Modify: `backend/license-service/src/server.test.js:40-61`
- Modify: `scripts/test_promotion_manager.py:7155-7193`

- [ ] **Step 1: Add failing legal identity assertions**

Extend the privacy route test with:

```javascript
assert.match(html, /ENHE Product Promo Maker \(formerly ENHE Promotion Manager\)/);
assert.match(html, /ENHE 产品推广素材生成器（原 ENHE Promotion Manager）/);
```

Add a test for the other public policies:

```javascript
test("public legal pages use the new name and one transition alias", async () => {
  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  try {
    for (const page of ["terms", "refund", "support"]) {
      const html = await getText(`${baseUrl}/promotion-manager/${page}`);
      assert.match(html, /ENHE Product Promo Maker/);
      assert.equal((html.match(/formerly ENHE Promotion Manager/g) || []).length, 1);
    }
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
```

Extend the Python legal-material test:

```python
english_legal = [
    DOCS / "legal/privacy-policy.md",
    DOCS / "legal/terms-of-service.md",
    DOCS / "legal/refund-policy.md",
    DOCS / "legal/support.md",
]
for path in english_legal:
    text = path.read_text(encoding="utf-8")
    self.assertIn("ENHE Product Promo Maker", text)
    self.assertEqual(text.count("formerly ENHE Promotion Manager"), 1, path)

chinese_privacy = (DOCS / "legal/privacy-policy.zh-CN.md").read_text(encoding="utf-8")
self.assertIn("ENHE 产品推广素材生成器（原 ENHE Promotion Manager）", chinese_privacy)
self.assertEqual(chinese_privacy.count("（原 ENHE Promotion Manager）"), 1)
```

- [ ] **Step 2: Run legal tests and confirm the new identity is absent**

Run:

```powershell
Push-Location backend/license-service
npm test
$nodeStatus = $LASTEXITCODE
Pop-Location
if ($nodeStatus -ne 0) { Write-Output "Expected failing Node legal assertions." }
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_privacy_policy_is_publication_ready scripts.test_promotion_manager.PromotionManagerScriptTest.test_legal_store_and_deployment_launch_materials_are_ready -v
```

Expected: the newly added identity assertions fail against the old legal headings and first references.

- [ ] **Step 3: Update headings and first product references exactly once**

Use these exact opening blocks while leaving all approved retention, payment, refund, safety, and contact terms unchanged:

```markdown
# ENHE Product Promo Maker Privacy Policy

Effective date: 2026-07-15

This policy explains how ENHE AI processes information for ENHE Product Promo Maker (formerly ENHE Promotion Manager), including its browser extension and optional hosted service.

## What The Product Does

ENHE Product Promo Maker helps users turn product or website URLs into guarded promotion workflow commands, publish packages, and optional ENHE-hosted task runs.
```

```markdown
# ENHE 产品推广素材生成器隐私政策

生效日期：2026-07-15

本政策说明 ENHE AI 如何处理 ENHE 产品推广素材生成器（原 ENHE Promotion Manager）浏览器扩展程序及其可选托管服务中的信息。

## 产品功能

ENHE 产品推广素材生成器帮助用户将产品或网站 URL 转换为受控的推广工作流命令、发布素材包以及可选的 ENHE 托管任务。
```

```markdown
# ENHE Product Promo Maker Terms Of Service
...
ENHE Product Promo Maker (formerly ENHE Promotion Manager) provides a browser extension, local Codex workflow commands, and optional ENHE-hosted promotion task execution.
```

```markdown
# ENHE Product Promo Maker Refund Policy
...
This policy applies to purchases of ENHE Product Promo Maker (formerly ENHE Promotion Manager).
```

```markdown
# ENHE Product Promo Maker Support

Support for ENHE Product Promo Maker (formerly ENHE Promotion Manager) is available through the public support URL below.
```

- [ ] **Step 4: Run Node and Python legal regressions**

Run:

```powershell
Push-Location backend/license-service
npm test
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
Pop-Location
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_privacy_policy_is_publication_ready scripts.test_promotion_manager.PromotionManagerScriptTest.test_legal_store_and_deployment_launch_materials_are_ready -v
```

Expected: all selected tests pass; each policy has one transition alias, and the retention/email assertions remain green.

- [ ] **Step 5: Commit legal identity changes**

```powershell
git add -- docs/legal/privacy-policy.md docs/legal/privacy-policy.zh-CN.md docs/legal/terms-of-service.md docs/legal/refund-policy.md docs/legal/support.md backend/license-service/src/server.test.js scripts/test_promotion_manager.py
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "docs: apply product rename to legal pages"
```

### Task 5: Rewrite store listing and reviewer copy around the direct value promise

**Files:**
- Modify: `docs/store/chrome-listing.md`
- Modify: `docs/store/edge-listing.md`
- Modify: `docs/store/reviewer-notes.md`
- Modify: `docs/store/screenshot-plan.md`
- Modify: `docs/extension-store-submission.md`
- Modify: `docs/zh-CN/extension-store-submission.md`
- Modify: `scripts/test_promotion_manager.py:7138-7193`

- [ ] **Step 1: Add a failing store-copy regression**

Add:

```python
def test_store_copy_uses_approved_bilingual_product_identity(self) -> None:
    chrome = (DOCS / "store/chrome-listing.md").read_text(encoding="utf-8")
    edge = (DOCS / "store/edge-listing.md").read_text(encoding="utf-8")
    reviewer = (DOCS / "store/reviewer-notes.md").read_text(encoding="utf-8")
    screenshot_plan = (DOCS / "store/screenshot-plan.md").read_text(encoding="utf-8")
    submission_en = (DOCS / "extension-store-submission.md").read_text(encoding="utf-8")
    submission_zh = (DOCS / "zh-CN/extension-store-submission.md").read_text(encoding="utf-8")

    for text in [chrome, edge, reviewer, screenshot_plan, submission_en, submission_zh]:
        self.assertIn("ENHE Product Promo Maker", text)
        self.assertNotIn("ENHE 推广管理器", text)
    for text in [chrome, edge, submission_zh]:
        self.assertIn("ENHE 产品推广素材生成器", text)
    self.assertIn(
        "Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.",
        chrome,
    )
    self.assertIn("把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。", chrome)
    self.assertIn("ENHE Promo Maker", screenshot_plan)
    self.assertIn("dist/v0.5.3", submission_en.replace("\\", "/"))
    self.assertIn("dist/v0.5.3", submission_zh.replace("\\", "/"))
```

- [ ] **Step 2: Run the store-copy test and confirm it fails**

Run:

```powershell
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_store_copy_uses_approved_bilingual_product_identity -v
```

Expected: `FAIL` because the listing still uses the retired English name and has no localized direct-value copy.

- [ ] **Step 3: Write the exact localized store identity**

In both Chrome and Edge listing drafts, include separate `English (default)` and `Simplified Chinese` blocks with these exact names and short descriptions:

```markdown
## English (default)

### Name

ENHE Product Promo Maker

### Short Description

Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.

## Simplified Chinese

### 名称

ENHE 产品推广素材生成器

### 简短说明

把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。
```

Start each detailed description with the page-to-output promise. Keep the existing permission, privacy, remote-code, login/captcha, publishing-approval, license, credit, and hosted-worker explanations after that first sentence. Do not use claims that guarantee virality, conversion, traffic, sales, revenue, or automatic publishing.

Start the reviewer note with:

```text
ENHE Product Promo Maker is a Manifest V3 extension that turns a product page selected by the user into promotional copy, video scripts, publishing assets, and guarded local commands or hosted ENHE run payloads.
```

Update the screenshot plan to require these exact assets:

```markdown
- `browser-extension/icons/icon128.png` — global store icon with the ENHE logo and the label `ENHE Promo Maker`.
- `dist/v0.5.3/store-assets/enhe-product-promo-maker-en-1280x800.png` — English popup.
- `dist/v0.5.3/store-assets/enhe-product-promo-maker-zh-1280x800.png` — Simplified Chinese popup.
```

Update both submission guides to name version `0.5.3`, point build output to `dist/v0.5.3`, use the exact localized names above, and retain the current official store links, extension ID, privacy URL, support URL, permission justifications, and remote-code statements.

- [ ] **Step 4: Run store documentation tests**

Run:

```powershell
python -m unittest `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_store_copy_uses_approved_bilingual_product_identity `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_store_submission_docs_are_bilingual `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_legal_store_and_deployment_launch_materials_are_ready -v
```

Expected: three tests pass and all safety/permission markers remain present.

- [ ] **Step 5: Commit the store copy**

```powershell
git add -- docs/store/chrome-listing.md docs/store/edge-listing.md docs/store/reviewer-notes.md docs/store/screenshot-plan.md docs/extension-store-submission.md docs/zh-CN/extension-store-submission.md scripts/test_promotion_manager.py
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "docs: rewrite store copy for promo maker"
```

### Task 6: Rename current documentation, operator labels, and CLI-facing text

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `README.zh-CN.md`
- Modify: `backend/license-service/README.md`
- Modify: `backend/license-service/package.json`
- Modify: `backend/license-service/src/migrate.js`
- Modify: `backend/license-service/src/server.js`
- Modify: `backend/license-service/src/worker.js`
- Modify: `deploy/promotion-manager/README.md`
- Modify: `deploy/promotion-manager/enhe-promotion-manager-api.service`
- Modify: `deploy/promotion-manager/enhe-promotion-manager-worker.service`
- Modify: `docs/100-percent-completion-roadmap.md`
- Modify: `docs/browser-extension.md`
- Modify: `docs/mediacrawler-sidecar.md`
- Modify: `docs/open-source-integration.md`
- Modify: `docs/zh-CN/browser-extension.md`
- Modify: `references/workflow.md`
- Modify: `scripts/automation_scheduler.py`
- Modify: `scripts/billing_contract_simulator.py`
- Modify: `scripts/completion_roadmap.py`
- Modify: `scripts/final_capability_audit.py`
- Modify: `scripts/mediacrawler_contract.py`
- Modify: `scripts/mediacrawler_downstream.py`
- Modify: `scripts/package_browser_extension.py`
- Modify: `scripts/platform_capabilities.py`
- Modify: `scripts/platform_data_manager.py`
- Modify: `scripts/publish_executor.py`
- Modify: `scripts/test_promotion_manager.py`

- [ ] **Step 1: Add a scoped retired-name regression and compatibility assertions**

Add these tests:

```python
def test_current_user_facing_files_do_not_use_retired_product_name(self) -> None:
    files = [
        ROOT / "README.md",
        ROOT / "README.en.md",
        ROOT / "README.zh-CN.md",
        LICENSE_SERVICE / "README.md",
        LICENSE_SERVICE / "package.json",
        LICENSE_SERVICE / "src/migrate.js",
        LICENSE_SERVICE / "src/server.js",
        LICENSE_SERVICE / "src/worker.js",
        ROOT / "deploy/promotion-manager/README.md",
        ROOT / "deploy/promotion-manager/enhe-promotion-manager-api.service",
        ROOT / "deploy/promotion-manager/enhe-promotion-manager-worker.service",
        DOCS / "100-percent-completion-roadmap.md",
        DOCS / "browser-extension.md",
        DOCS / "mediacrawler-sidecar.md",
        DOCS / "open-source-integration.md",
        DOCS / "zh-CN/browser-extension.md",
        ROOT / "references/workflow.md",
        ROOT / "scripts/automation_scheduler.py",
        ROOT / "scripts/billing_contract_simulator.py",
        ROOT / "scripts/completion_roadmap.py",
        ROOT / "scripts/final_capability_audit.py",
        ROOT / "scripts/mediacrawler_contract.py",
        ROOT / "scripts/mediacrawler_downstream.py",
        ROOT / "scripts/package_browser_extension.py",
        ROOT / "scripts/platform_capabilities.py",
        ROOT / "scripts/platform_data_manager.py",
        ROOT / "scripts/publish_executor.py",
    ]
    legal_aliases = [
        "ENHE Product Promo Maker (formerly ENHE Promotion Manager)",
        "ENHE 产品推广素材生成器（原 ENHE Promotion Manager）",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for alias in legal_aliases:
            text = text.replace(alias, "")
        self.assertNotIn("ENHE Promotion Manager", text, path)
        self.assertNotIn("ENHE 推广管理器", text, path)
        self.assertNotIn("Promotion Manager", text, path)
        self.assertNotIn("推广管理器", text, path)

def test_rebrand_preserves_internal_compatibility_identifiers(self) -> None:
    popup = (BROWSER_EXTENSION / "popup.js").read_text(encoding="utf-8")
    package_script = PACKAGE_BROWSER_EXTENSION.read_text(encoding="utf-8")
    package_json = json.loads((LICENSE_SERVICE / "package.json").read_text(encoding="utf-8"))
    state_store = (LICENSE_SERVICE / "src/state-store.js").read_text(encoding="utf-8")
    deploy = (ROOT / "deploy/promotion-manager/README.md").read_text(encoding="utf-8")

    self.assertIn("/api/promotion-manager/license", popup)
    self.assertIn("/promotion-manager/checkout", popup)
    self.assertEqual(package_json["name"], "enhe-promotion-manager-license-service")
    self.assertIn('return f"enhe-promotion-manager-{version}.zip"', package_script)
    self.assertIn("promotion_manager_state", state_store)
    self.assertIn("/opt/enhe/promotion-manager/current", deploy)
    self.assertIn("/var/lib/enhe-promotion-manager", deploy)
    self.assertTrue((ROOT / "deploy/promotion-manager/enhe-promotion-manager-api.service").exists())
    self.assertTrue((ROOT / "deploy/promotion-manager/enhe-promotion-manager-worker.service").exists())
```

- [ ] **Step 2: Run the two regressions and confirm the retired-name scan fails**

Run:

```powershell
python -m unittest `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_current_user_facing_files_do_not_use_retired_product_name `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_rebrand_preserves_internal_compatibility_identifiers -v
```

Expected: the retired-name test fails and the compatibility test passes.

- [ ] **Step 3: Apply surgical presentation-only replacements**

Use these mappings according to document language:

```text
English full name: ENHE Product Promo Maker
Chinese full name: ENHE 产品推广素材生成器
English short name: ENHE Promo Maker
Chinese short name: ENHE 推广素材
Chrome manifest English short_name: ENHE Promo
English promise: Turn product pages into promotional copy, video scripts, and publishing assets.
Chinese promise: 把产品网页变成推广文案、视频脚本和发布素材
```

Make these exact behavior-preserving label changes:

```javascript
// backend process logs and systemd Description values
ENHE Product Promo Maker license service listening on ${port}
ENHE Product Promo Maker retention cleanup enabled
ENHE Product Promo Maker hosted worker enabled in API process
ENHE Product Promo Maker database migration completed.
ENHE Product Promo Maker hosted worker started
Description=ENHE Product Promo Maker API
Description=ENHE Product Promo Maker Hosted Worker
```

```python
# automation_scheduler.py default shown in generated commands and Windows Task Scheduler
task.add_argument("--task-name", default="ENHE Product Promo Maker")

# publish_executor.py default PR body
body = args.pr_body or "Automated promotion content update generated by ENHE Product Promo Maker."
```

Update the existing test fixture at `scripts/test_promotion_manager.py:5011-5021` from `ENHE Promotion Manager Test` to `ENHE Product Promo Maker Test` so it still verifies exact user-supplied Windows task names.

Update only headings, introductions, current instructions, CLI descriptions/docstrings, generated human-readable labels, and example `--task-name` values in the listed files. Do not rename files, modules, URL fragments, output folders, environment variables, services, databases, state keys, or package filenames.

- [ ] **Step 4: Run the scoped identity and current-document tests**

Run:

```powershell
python -m unittest `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_current_user_facing_files_do_not_use_retired_product_name `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_rebrand_preserves_internal_compatibility_identifiers `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_github_docs_include_intro_usage_install_extension_and_pricing `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_license_service_backend_skeleton_matches_extension_billing_contract -v
```

Expected: all four tests pass.

- [ ] **Step 5: Verify the retired name remains only in approved historical/legal locations**

Run:

```powershell
$matches = @(git grep -n -I -E 'Promotion Manager|推广管理器' -- . 2>$null)
$unexpected = @($matches | Where-Object {
  $_ -notmatch 'docs/superpowers/(specs|plans)/' -and
  $_ -notmatch 'docs/releases/' -and
  $_ -notmatch 'docs/legal/' -and
  $_ -notmatch 'backend/license-service/src/server.test.js' -and
  $_ -notmatch 'scripts/test_promotion_manager.py'
})
$unexpected
if ($unexpected.Count -ne 0) { exit 1 }
```

Expected: no unexpected output. Legal matches are only the approved one-time aliases; historical design/plan/release evidence remains unchanged.

- [ ] **Step 6: Commit current documentation and operator labels**

```powershell
git add -- README.md README.en.md README.zh-CN.md backend/license-service/README.md backend/license-service/package.json backend/license-service/src/migrate.js backend/license-service/src/server.js backend/license-service/src/worker.js deploy/promotion-manager/README.md deploy/promotion-manager/enhe-promotion-manager-api.service deploy/promotion-manager/enhe-promotion-manager-worker.service docs/100-percent-completion-roadmap.md docs/browser-extension.md docs/mediacrawler-sidecar.md docs/open-source-integration.md docs/zh-CN/browser-extension.md references/workflow.md scripts/automation_scheduler.py scripts/billing_contract_simulator.py scripts/completion_roadmap.py scripts/final_capability_audit.py scripts/mediacrawler_contract.py scripts/mediacrawler_downstream.py scripts/package_browser_extension.py scripts/platform_capabilities.py scripts/platform_data_manager.py scripts/publish_executor.py scripts/test_promotion_manager.py
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "docs: apply product promo maker identity"
```

### Task 7: Build and preserve the versioned v0.5.3 package evidence

**Files:**
- Create: `dist/v0.5.3/enhe-promotion-manager-0.5.3.zip`
- Create: `dist/v0.5.3/browser-extension-package-report.json`
- Create: `dist/v0.5.3/browser-extension-package-report.md`
- Preserve: `dist/enhe-promotion-manager-0.5.2.zip`
- Preserve: `dist/browser-extension-package-report.json`
- Preserve: `dist/browser-extension-package-report.md`

- [ ] **Step 1: Prove the old release artifacts are unchanged before packaging**

Run:

```powershell
git diff --exit-code origin/main -- dist/enhe-promotion-manager-0.5.2.zip dist/browser-extension-package-report.json dist/browser-extension-package-report.md
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Get-FileHash -Algorithm SHA256 dist/enhe-promotion-manager-0.5.2.zip
```

Expected: no diff and one SHA-256 hash for the preserved v0.5.2 ZIP.

- [ ] **Step 2: Build into the isolated v0.5.3 directory**

Run:

```powershell
python scripts/package_browser_extension.py --out-dir ".\dist\v0.5.3"
```

Expected: `Browser extension package written to:` followed by `dist\v0.5.3\enhe-promotion-manager-0.5.3.zip`.

- [ ] **Step 3: Validate the generated report and ZIP contents**

Run:

```powershell
$report = Get-Content -LiteralPath 'dist/v0.5.3/browser-extension-package-report.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if ($report.status -ne 'ready') { exit 1 }
if ($report.version -ne '0.5.3') { exit 1 }
if (-not $report.checks.manifestV3) { exit 1 }
if (-not $report.checks.icons) { exit 1 }
if (-not $report.checks.allowedPermissions) { exit 1 }
if (-not $report.checks.hostPermissionsScopedToEnhe) { exit 1 }
if (-not $report.checks.noRemoteExecutableCode) { exit 1 }
if (-not $report.checks.noUnsafeEval) { exit 1 }
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_browser_extension_package_script_builds_store_submission_zip -v
```

Expected: all report guards are true and the package regression passes.

- [ ] **Step 4: Recheck the old evidence after packaging**

Run:

```powershell
git diff --exit-code origin/main -- dist/enhe-promotion-manager-0.5.2.zip dist/browser-extension-package-report.json dist/browser-extension-package-report.md
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

Expected: no diff; only `dist/v0.5.3/` is new.

- [ ] **Step 5: Commit versioned package evidence**

```powershell
git add -- dist/v0.5.3/enhe-promotion-manager-0.5.3.zip dist/v0.5.3/browser-extension-package-report.json dist/v0.5.3/browser-extension-package-report.md
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "build: package extension v0.5.3"
```

### Task 8: Capture localized store screenshots and run full validation

**Files:**
- Create: `dist/v0.5.3/store-assets/enhe-product-promo-maker-en-1280x800.png`
- Create: `dist/v0.5.3/store-assets/enhe-product-promo-maker-zh-1280x800.png`
- Verify only: all source, tests, and v0.5.3 package files

- [ ] **Step 1: Load the unpacked extension in an isolated persistent Chromium profile**

Use the `playwright-interactive` skill. Launch a headful persistent Chromium context with only `browser-extension/` enabled:

```javascript
const extensionPath = "C:\\Users\\HU\\Documents\\viral-product-copy-video-generator\\.worktrees\\product-promo-maker-rebrand\\browser-extension";
const context = await chromium.launchPersistentContext("C:\\Users\\HU\\AppData\\Local\\Temp\\enhe-promo-maker-v053-profile", {
  headless: false,
  args: [
    `--disable-extensions-except=${extensionPath}`,
    `--load-extension=${extensionPath}`,
  ],
  viewport: { width: 1280, height: 800 },
});
const extensionsPage = await context.newPage();
await extensionsPage.goto("chrome://extensions");
const extensionItem = extensionsPage.locator("extensions-item").filter({ hasText: "ENHE Product Promo Maker" });
await extensionItem.waitFor();
const extensionId = await extensionItem.getAttribute("id");
if (!extensionId) throw new Error("Unable to resolve the unpacked extension ID");
const page = await context.newPage();
await page.goto(`chrome-extension://${extensionId}/popup.html`);
```

Expected: the unpacked popup opens without console errors or network-loaded executable code.

- [ ] **Step 2: Capture the English and Chinese 1280×800 assets without secrets**

Center the popup only for store framing, populate a public ENHE URL, and capture both languages:

```powershell
New-Item -ItemType Directory -Force -Path 'dist/v0.5.3/store-assets' | Out-Null
```

```javascript
await page.addStyleTag({ content: "html{background:#111418}body{margin:0 auto}" });
await page.locator("#productUrl").fill("https://www.enhe-tech.com.cn/");
await page.locator("#languageEn").click();
await page.screenshot({
  path: "C:\\Users\\HU\\Documents\\viral-product-copy-video-generator\\.worktrees\\product-promo-maker-rebrand\\dist\\v0.5.3\\store-assets\\enhe-product-promo-maker-en-1280x800.png",
});
await page.locator("#languageZh").click();
await page.screenshot({
  path: "C:\\Users\\HU\\Documents\\viral-product-copy-video-generator\\.worktrees\\product-promo-maker-rebrand\\dist\\v0.5.3\\store-assets\\enhe-product-promo-maker-zh-1280x800.png",
});
```

Expected: both images are exactly 1280×800, show the full localized name and approved promise, and contain no License Key, email, payment secret, customer data, or private product URL. Inspect both with `view_image` before continuing.

- [ ] **Step 3: Commit the reviewed screenshots**

```powershell
git add -- dist/v0.5.3/store-assets/enhe-product-promo-maker-en-1280x800.png dist/v0.5.3/store-assets/enhe-product-promo-maker-zh-1280x800.png
git diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git commit -m "docs: add localized v0.5.3 store screenshots"
```

- [ ] **Step 4: Run the complete Node regression suite**

Run:

```powershell
Push-Location backend/license-service
npm test
$status = $LASTEXITCODE
Pop-Location
if ($status -ne 0) { exit $status }
```

Expected: all Node tests pass.

- [ ] **Step 5: Run the complete Python regression suite**

Run:

```powershell
New-Item -ItemType Directory -Force -Path 'promotion-output' | Out-Null
python scripts/test_promotion_manager.py -v
```

Expected: final output is `OK` with no failures or errors.

- [ ] **Step 6: Run final repository and package checks**

Run:

```powershell
git diff origin/main...HEAD --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/package_browser_extension.py --out-dir "$env:TEMP\enhe-promo-maker-v053-verify"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git status -sb
```

Expected: whitespace check passes, the independent package is `ready`, and the branch has no uncommitted files.

- [ ] **Step 7: Manually verify the compatibility boundary in Chrome**

In the isolated unpacked profile:

1. English shows `ENHE Product Promo Maker` and the approved English promise.
2. Chinese shows `ENHE 产品推广素材生成器` and the approved Chinese promise.
3. The language choice remains after closing and reopening the popup.
4. The 16/48 px toolbar icon remains recognizable; the 128 px icon reads `ENHE PROMO MAKER` when viewed at store size.
5. A locally stored valid License Key still validates against the unchanged `/api/promotion-manager/license` endpoint; do not record the key in screenshots, logs, commits, or PR text.
6. The generated commands retain existing script filenames, report paths, and `/promotion-manager/` endpoint paths.

Expected: all six checks pass without changing any production or store state.

### Task 9: Push one PR, wait for checks, and merge

**Files:**
- No new product files
- Verify: complete branch diff from `origin/main`

- [ ] **Step 1: Review the final diff and commit history**

Run:

```powershell
git status -sb
git diff --stat origin/main...HEAD
git log --oneline origin/main..HEAD
git diff --name-only origin/main...HEAD -- dist/enhe-promotion-manager-0.5.2.zip dist/browser-extension-package-report.json dist/browser-extension-package-report.md
```

Expected: clean worktree; the old v0.5.2 ZIP and root reports are absent from the changed-file output.

- [ ] **Step 2: Push the feature branch**

Run:

```powershell
git push -u origin agent/product-promo-maker-rebrand
```

Expected: the remote branch is created and tracks `origin/agent/product-promo-maker-rebrand`.

- [ ] **Step 3: Create the PR with exact scope and evidence**

Run:

```powershell
$body = @"
## Summary
- rename user-facing product identity to ENHE Product Promo Maker / ENHE 产品推广素材生成器
- update bilingual extension, checkout, legal, store, and documentation copy
- add the ENHE Promo Maker store icon, localized screenshots, and validated v0.5.3 package

## Compatibility
- keeps all /promotion-manager/ routes, API paths, systemd names, storage keys, npm identifiers, prices, payment signatures, licenses, and extension item identity unchanged
- preserves the existing v0.5.2 ZIP and reports

## Validation
- npm test
- python scripts/test_promotion_manager.py -v
- scripts/package_browser_extension.py reports ready for v0.5.3
- unpacked Chrome checks in English and Simplified Chinese
"@
gh pr create --base main --head agent/product-promo-maker-rebrand --title "feat: rebrand as ENHE Product Promo Maker" --body $body
```

Expected: GitHub returns one PR URL.

- [ ] **Step 4: Wait for GitHub checks and inspect review state**

Run:

```powershell
$pr = gh pr view --json number --jq .number
$checkCount = [int](gh pr view $pr --json statusCheckRollup --jq '.statusCheckRollup | length')
if ($checkCount -gt 0) {
  gh pr checks $pr --watch
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
gh pr view $pr --json mergeable,reviewDecision,statusCheckRollup
```

Expected: required checks succeed and the PR reports mergeable.

- [ ] **Step 5: Merge with the repository's existing merge-commit convention**

Run:

```powershell
gh pr merge $pr --merge
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git fetch origin main
gh pr view $pr --json state,mergedAt,mergeCommit,url
```

Expected: state `MERGED`, a merge commit on `origin/main`, and no deployment has occurred before this point.

### Task 10: Deploy the merged commit atomically and verify production

**Files:**
- Deploy only: merged `origin/main`
- Server layout: `/opt/enhe/promotion-manager/releases/<release-id>` and `/opt/enhe/promotion-manager/current`
- Preserve: `/etc/enhe-promotion-manager/api.env`, database state, hosted artifacts, and inactive-worker state
- Required local credential: `C:\Users\HU\Desktop\fushengpe.pem` (used in prior successful deployments, currently absent; restore it locally before this task and never commit it)

- [ ] **Step 1: Record the current release and build an archive from merged `origin/main`**

Run:

```powershell
$key = 'C:\Users\HU\Desktop\fushengpe.pem'
if (-not (Test-Path -LiteralPath $key)) {
  throw 'Restore C:\Users\HU\Desktop\fushengpe.pem before production deployment.'
}
$server = 'ubuntu@111.229.135.3'
$mergedSha = (git rev-parse origin/main).Trim()
$releaseId = (Get-Date -Format 'yyyyMMddHHmmss') + '-' + $mergedSha.Substring(0, 12)
$archive = Join-Path $env:TEMP ("enhe-promo-maker-" + $releaseId + ".tar.gz")
$previousRelease = (ssh -i $key $server 'test -L /opt/enhe/promotion-manager/current && readlink -f /opt/enhe/promotion-manager/current').Trim()
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not $previousRelease.StartsWith('/opt/enhe/promotion-manager/')) { exit 1 }
git archive --format=tar.gz --output $archive origin/main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

Expected: a local archive from the merged main commit and a verified previous release path under `/opt/enhe/promotion-manager/`.

- [ ] **Step 2: Upload and prepare the new immutable release**

Run:

```powershell
scp -i $key $archive "${server}:/tmp/enhe-promo-maker-$releaseId.tar.gz"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
ssh -i $key $server "set -e; sudo test ! -e '/opt/enhe/promotion-manager/releases/$releaseId'; sudo mkdir -p '/opt/enhe/promotion-manager/releases/$releaseId'; sudo tar -xzf '/tmp/enhe-promo-maker-$releaseId.tar.gz' -C '/opt/enhe/promotion-manager/releases/$releaseId'; cd '/opt/enhe/promotion-manager/releases/$releaseId/backend/license-service'; sudo npm ci --omit=dev"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

Expected: dependencies install successfully inside the new release; `current` still points to the previous release.

- [ ] **Step 3: Atomically switch `current` and restart only already managed services**

Run:

```powershell
ssh -i $key $server "set -e; sudo ln -sfn '/opt/enhe/promotion-manager/releases/$releaseId' /opt/enhe/promotion-manager/current.next; sudo mv -Tf /opt/enhe/promotion-manager/current.next /opt/enhe/promotion-manager/current; sudo systemctl restart enhe-promotion-manager-api; sudo systemctl try-restart enhe-promotion-manager-worker"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

Expected: the API restarts from the new symlink; an inactive worker remains inactive because `try-restart` does not enable or start it.

- [ ] **Step 4: Verify health, identity, prices, QR flow markers, and privacy policy**

Run:

```powershell
ssh -i $key $server 'set -e; curl -fsS http://127.0.0.1:3030/health; curl -fsS http://127.0.0.1:3030/api/promotion-manager/health'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$publicHealth = Invoke-RestMethod 'https://www.enhe-tech.com.cn/api/promotion-manager/health'
$checkout = (Invoke-WebRequest 'https://www.enhe-tech.com.cn/promotion-manager/checkout' -UseBasicParsing).Content
$privacy = (Invoke-WebRequest 'https://www.enhe-tech.com.cn/promotion-manager/privacy' -UseBasicParsing).Content
$checkoutRequired = @(
  'ENHE Product Promo Maker Checkout',
  'ENHE 产品推广素材生成器 国内支付',
  'Starter - ¥19',
  'Growth - ¥59',
  'Scale - ¥199',
  'id="paymentQr"',
  'id="openPaymentPage"'
)
$privacyRequired = @(
  'ENHE Product Promo Maker (formerly ENHE Promotion Manager)',
  'ENHE 产品推广素材生成器（原 ENHE Promotion Manager）',
  'automatically deleted 30 days',
  'retained for 180 days',
  'huqingwei5942@gmail.com'
)
if (@($checkoutRequired | Where-Object { -not $checkout.Contains($_) }).Count -ne 0) { exit 1 }
if (@($privacyRequired | Where-Object { -not $privacy.Contains($_) }).Count -ne 0) { exit 1 }
$publicHealth | ConvertTo-Json -Depth 5
```

Expected: local and public health checks succeed; production contains the new bilingual identity while prices, QR markers, retention statements, and contact email remain intact.

- [ ] **Step 5: Roll back immediately if any production check fails**

Run this only when Step 4 fails:

```powershell
ssh -i $key $server "set -e; sudo ln -sfn '$previousRelease' /opt/enhe/promotion-manager/current.next; sudo mv -Tf /opt/enhe/promotion-manager/current.next /opt/enhe/promotion-manager/current; sudo systemctl restart enhe-promotion-manager-api; sudo systemctl try-restart enhe-promotion-manager-worker; curl -fsS http://127.0.0.1:3030/health"
```

Expected: `current` returns to the recorded previous release and health succeeds. Report the failed assertion before attempting a corrected release.

- [ ] **Step 6: Clean only the known temporary archive after success**

Run:

```powershell
Remove-Item -LiteralPath $archive
ssh -i $key $server "rm -f '/tmp/enhe-promo-maker-$releaseId.tar.gz'"
```

Expected: only the local and remote temporary tarballs are removed; both immutable releases remain available for rollback.

### Task 11: Update the existing Chrome Web Store item according to its real state

**Files:**
- Upload candidate: `dist/v0.5.3/enhe-promotion-manager-0.5.3.zip`
- Store icon: `browser-extension/icons/icon128.png`
- Store screenshots: `dist/v0.5.3/store-assets/enhe-product-promo-maker-en-1280x800.png`, `dist/v0.5.3/store-assets/enhe-product-promo-maker-zh-1280x800.png`
- Store copy: `docs/store/chrome-listing.md`
- Reviewer note: `docs/store/reviewer-notes.md`

- [ ] **Step 1: Open the official dashboard and verify the existing item before mutation**

Use `playwright-interactive` with the already authenticated Chrome profile to open:

```text
https://chrome.google.com/webstore/devconsole
```

Verify that the selected item ID is exactly `dloklkbnmoigemnfigbkibogmgbieppl`. Record whether v0.5.2 is `Pending review`, `Published`, or `Rejected`. Do not create a new item. If Google requests password, 2FA, CAPTCHA, or account re-verification, pause only for the user to complete that authentication step.

- [ ] **Step 2: Follow the status branch without overwriting an active review blindly**

Use exactly one branch:

```text
Pending review -> keep v0.5.2 under review unchanged; retain v0.5.3 as the prepared next update and report the pending-review gate.
Published      -> upload v0.5.3 as the normal update to the same item.
Rejected       -> read and preserve the rejection reason, confirm this PR addresses any naming/listing issue, then upload the corrected v0.5.3 to the same item.
```

Expected: no second item and no withdrawal of a pending v0.5.2 review without a separate explicit decision.

- [ ] **Step 3: For Published or Rejected status, upload and fill the exact localized metadata**

Upload the v0.5.3 ZIP and use:

```text
English name: ENHE Product Promo Maker
English short description: Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.
Chinese name: ENHE 产品推广素材生成器
Chinese short description: 把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。
Privacy URL: https://www.enhe-tech.com.cn/promotion-manager/privacy
Support URL: https://www.enhe-tech.com.cn/promotion-manager/support
```

Upload the v3 128 px icon, the two reviewed screenshots, the detailed localized descriptions, permission justifications, and reviewer note from the committed docs. Confirm the item still displays ID `dloklkbnmoigemnfigbkibogmgbieppl` before saving.

- [ ] **Step 4: Submit the update and capture non-secret evidence**

For Published or Rejected status, submit v0.5.3 for review. Record the item ID, submitted version, submission timestamp, and resulting dashboard state; do not record account passwords, authentication codes, License Keys, merchant secrets, or customer information.

Expected: the existing item shows v0.5.3 in its submitted state. For Pending review status, expected outcome is an unchanged v0.5.2 review plus a validated local v0.5.3 update package ready for the next submission window.

## Final Acceptance Checklist

- [ ] New users see `ENHE Product Promo Maker` / `ENHE 产品推广素材生成器` and understand the page-to-copy/video/publishing-assets value immediately.
- [ ] Popup language follows Chrome on first use and remembers the explicit `中文 / EN` selection.
- [ ] The global marketing short name remains `ENHE Promo Maker`; Chrome's technical English `short_name` is the compliant 10-character `ENHE Promo`.
- [ ] Store icon reads `ENHE PROMO MAKER`; 16/48 px toolbar icons remain text-free and recognizable.
- [ ] Checkout, billing, run, privacy, terms, refund, and support pages use the approved identity.
- [ ] Each legal policy has exactly one approved transition alias.
- [ ] ZPAY sends `ENHE Product Promo Maker <Plan>` while amounts, signatures, callbacks, QR polling, mobile direct payment, and licenses remain unchanged.
- [ ] URL paths, API paths, service names, directories, DB keys, environment variables, npm identifiers, script/report paths, and store item ID remain unchanged.
- [ ] Existing v0.5.2 package/evidence remains unchanged; v0.5.3 package report is `ready`.
- [ ] Complete Node and Python regressions pass.
- [ ] One PR is merged before production deployment.
- [ ] Production health and bilingual page checks pass or the deployment is rolled back immediately.
- [ ] The existing store item is updated only when its real review state allows it; no second item is created.

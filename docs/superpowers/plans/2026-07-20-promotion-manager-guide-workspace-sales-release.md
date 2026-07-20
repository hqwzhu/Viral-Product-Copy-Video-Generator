# ENHE Promotion Manager Guide, Workspace, and Sales Release Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add a bilingual in-extension guide, a responsive full workspace, and a sales-oriented public distribution homepage, then finish the verified Skill/Chrome release workflow for v0.5.3.

**Architecture:** Keep browser-extension/popup.html as the fast launcher and use one shared view=workspace mode for the full extension page so translations, command generation, plan data, and license state remain single-sourced. Keep the distribution builder and strict validator as the release boundary, rebuild the public repository from one exact merged source commit, and publish the same verified extension ZIP to GitHub and the existing Chrome Web Store item.

**Tech Stack:** Chrome Manifest V3, vanilla HTML/CSS/JavaScript, Python 3.11 unittest, pathlib, json, zipfile, Git, GitHub CLI, and browser smoke checks.

---

## Context and Invariants

- Source worktree: C:/Users/HU/Documents/viral-product-copy-video-generator/.worktrees/product-promo-maker-rebrand
- Source branch: agent/product-promo-maker-rebrand
- Design commit: bb89f7c
- Public target: C:/Users/HU/Documents/enhe-promotion-manager
- Public repository: hqwzhu/enhe-promotion-manager
- Release: v0.5.3
- Existing Chrome item: dloklkbnmoigemnfigbkibogmgbieppl, currently 0.5.2
- Hosted Worker stays disabled.
- Approved plans: Free 5 credits; Starter CNY 19/30 days and 60 credits; Growth CNY 59/30 days and 220 credits; Scale CNY 199/30 days and 800 credits.
- Existing failed-candidate backup directories are evidence and must not be deleted or overwritten.
- The pre-UI validated extension hash D01BCCD2D1D8F2AC25B44BF615F4B9F4F3CD4C9E4461C9BF26AA3DCB849CA7B0 is not assumed after UI edits. Repackage and review the final hash again.

## File Map

- Modify browser-extension/popup.html, popup.js, popup.css for the guide and workspace.
- Create scripts/test_extension_ui.py for bilingual, accessibility, view, plan, permission, and responsive contracts.
- Modify scripts/test_public_distribution.py for the extension and sales-homepage contracts.
- Modify distribution/README.md and distribution/README.en.md for the sales homepages.
- Use scripts/package_browser_extension.py, scripts/build_public_distribution.py, distribution/scripts/build_release.py, and distribution/scripts/verify_distribution.py without weakening strict checks.
- Do not modify browser-extension/manifest.json permissions or billing-contract.json for this UI task.
- Do not add secrets, browser profiles, Sidecar checkouts, generated output, or backend runtime to the public tree.

---

### Task 1: Add the bilingual in-extension guide

**Files:** Create scripts/test_extension_ui.py; modify browser-extension/popup.html, browser-extension/popup.js, browser-extension/popup.css.

- [ ] Step 1: Write a failing static contract test.

The test must read popup.html, popup.js, popup.css, and manifest.json as UTF-8/JSON. Assert that popup.html contains openGuide, openWorkspace, guideView, guideBack, guideTabs, guideFeatures, guideUsage, and guideSubscription IDs; the guide has role=tablist, aria-selected, and aria-controls; and popup.js contains every new translation key at least once in each of EN_TRANSLATIONS and ZH_TRANSLATIONS. Assert that manifest permissions remain exactly activeTab, storage, and clipboardWrite, and that PLANS contains the approved Starter, Growth, and Scale CNY values.

Run:

    python -m unittest scripts.test_extension_ui -v

Expected: FAIL because the guide contract is not implemented.

- [ ] Step 2: Add the guide shell and localized labels.

Add a compact topbar help button, an open-workspace action, a hidden guide view, and three accessible tab sections. Every visible new string uses data-i18n or the existing translation helper. Add matching real Chinese and English entries for the guide title, tabs, feature groups, four quick-start steps, subscription labels, plan details, return action, and workspace action.

- [ ] Step 3: Add view and tab state without duplicating business logic.

Implement setView(viewName), setGuideTab(tabName), openWorkspace(), and renderGuideContent(). setView guide hides the primary form and shows the guide; main restores it; workspace marks the document for full layout. setGuideTab selects one tab and one section. openWorkspace opens the same page with ?view=workspace using chrome.tabs.create when available and window.open only as a safe fallback. Do not duplicate command generation, license, or billing handlers.

- [ ] Step 4: Add the factual guide content.

The Features tab groups product-page intake, copy/scripts, platform evidence, image/video preparation, publishing preparation, real-data recovery, next-round optimization, and automation. The Usage tab shows four numbered steps, local Skill execution, evidence boundaries, manual CAPTCHA/risk-control handling, and final publish confirmation. The Subscription tab reads the existing PLANS object and explains Free 5, Starter 19/60, Growth 59/220, Scale 199/800, audience fit, checkout, billing, and Hosted Worker disabled.

- [ ] Step 5: Add guide styling and verify.

Preserve the current dark/green language, radius, focus ring, reduced-motion behavior, and popup density. Run:

    python -m unittest scripts.test_extension_ui -v
    git diff --check

Expected: focused tests pass. Commit with:

    git add -- browser-extension/popup.html browser-extension/popup.js browser-extension/popup.css scripts/test_extension_ui.py
    git commit -m "feat: add bilingual in-extension usage guide"

---

### Task 2: Add the desktop-first responsive workspace

**Files:** Modify browser-extension/popup.html, popup.js, popup.css, and scripts/test_extension_ui.py.

- [ ] Step 1: Add failing workspace assertions.

Require popup.js to handle ?view=workspace, popup.html to expose a workspace view marker, and popup.css to contain workspace-grid plus max-width 900px, max-width 520px, and prefers-reduced-motion rules. Assert no tabs permission is added to manifest.json. Run the focused test and confirm the expected failure.

- [ ] Step 2: Add the shared workspace shell.

Keep popup mode focused on URL, platforms, workflow, and command generation. Mark existing configuration, command output, and subscription regions as semantic workspace regions. Add one summary region that reuses existing elements; do not render a second business-logic copy.

- [ ] Step 3: Add responsive rules.

Use this contract as the minimum:

    body[data-view="workspace"] { width: 100%; min-width: 320px; max-width: none; }
    .workspace-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(300px, .85fr); gap: 16px; }
    @media (max-width: 900px) { .workspace-grid { grid-template-columns: 1fr; } }
    @media (max-width: 520px) { .shell { padding: 12px; } .button-row > button { flex: 1 1 100%; } }

Also use min-width: 0, full-width controls, visible focus styles, touch-safe controls, and reduced-motion support. Do not add a second color system.

- [ ] Step 4: Verify state preservation and viewport behavior.

Assert that main form IDs remain unique and that returning from guide/workspace does not clear URL, platforms, workflow, plan, or command state. Use a DOM-capable smoke check or a real Chromium check at 360px, 768px, and 1280px; record which tool was available and do not call static checks a browser test.

- [ ] Step 5: Run and commit.

    python -m unittest scripts.test_extension_ui -v
    python -m unittest scripts.test_public_distribution -v
    python -m compileall -q scripts
    git diff --check
    git add -- browser-extension/popup.html browser-extension/popup.js browser-extension/popup.css scripts/test_extension_ui.py
    git commit -m "feat: add responsive promotion workspace"

---

### Task 3: Make both public READMEs sales-oriented

**Files:** Modify distribution/README.md, distribution/README.en.md, and scripts/test_public_distribution.py.

- [ ] Step 1: Add a failing homepage contract.

Require both READMEs to contain their language equivalents of: why users need it, what users get, from product page to publishing assets, plans and audience fit, trust and boundaries, creator and contact. Require Starter, Growth, Scale, the approved CNY prices, huqingwei5942@gmail.com, enhe-tech.com.cn, both download CTAs, and the product promise in both files. Run the focused test and confirm it fails before the rewrite.

- [ ] Step 2: Rewrite README.md as a Chinese sales homepage.

Keep the opening links, then lead with customer pain points, outcomes, a capability grid answering what/problem/benefit/use case, a six-step workflow, Free/Starter/Growth/Scale cards with approved prices and credits, local-first trust boundaries, five-minute installation CTAs, detailed-document links, creator/contact information, and a clear Skill-versus-extension explanation. Keep technical installation, privacy, security, platform, and troubleshooting documents linked below rather than deleting them.

- [ ] Step 3: Mirror the same facts in README.en.md.

Use equivalent English sections, capability groups, prices, limits, creator details, URLs, download names, privacy boundaries, and Hosted Worker state. Do not claim guaranteed results, CAPTCHA bypass, or automatic final publishing.

- [ ] Step 4: Run parity and safety checks.

    python -m unittest scripts.test_public_distribution -v
    Select-String -Path distribution/README.md,distribution/README.en.md -Pattern 'TBD|TODO|guaranteed viral|bypass captcha|automatic final publish|保证爆款|绕过验证码|自动点击最终发布'

Expected: all tests pass and Select-String has no output. Commit:

    git add -- distribution/README.md distribution/README.en.md scripts/test_public_distribution.py
    git commit -m "docs: make public distribution homepage sales-oriented"

---

### Task 4: Build and validate the local release candidate

**Files and paths:** source scripts and docs; public target C:/Users/HU/Documents/enhe-promotion-manager; generated public dist/v0.5.3, release-manifest.json, and SHA256SUMS.

- [ ] Step 1: Run all source gates from the clean new HEAD.

    python -m unittest scripts.test_extension_ui -v
    python -m unittest scripts.test_public_distribution -v
    python -m unittest scripts.test_mediacrawler_sidecar -v
    python -m unittest scripts.test_promotion_manager -v
    python -m compileall -q scripts distribution/scripts distribution/tests
    git status --short

Expected: green suites, expected Windows symlink skips only, compile success, and clean source status.

- [ ] Step 2: Repackage the final extension.

Run scripts/package_browser_extension.py using its existing validated-output contract. Record the package report, member list, permissions, and SHA-256. The final public build must use this exact validated ZIP; do not reuse the pre-UI package hash without proof of byte identity.

- [ ] Step 3: Preserve any old failed candidate safely.

Verify the target resolves exactly, has no .git, contains the prior failed manifest commit, and the next timestamped backup path does not exist. Rename the whole directory with Move-Item -LiteralPath. Never recursively delete or overwrite a backup.

- [ ] Step 4: Build the standalone public tree.

    python scripts/build_public_distribution.py --output-dir C:/Users/HU/Documents/enhe-promotion-manager --validated-extension-zip ./dist/v0.5.3/enhe-promotion-manager-0.5.3.zip

Verify manifest sourceCommit equals git rev-parse HEAD and the tree has no caches, secrets, Sidecar checkout, browser state, generated output, or .git.

- [ ] Step 5: Build and verify public assets.

From the public target run:

    python scripts/build_release.py --validated-extension-zip ./dist/validated/enhe-promotion-manager-0.5.3.zip
    python scripts/verify_distribution.py
    python -m unittest discover -s tests -v
    Get-Content ./SHA256SUMS

Expected: validator ready; Skill ZIP, extension ZIP, release-manifest.json, and SHA256SUMS exist; checksums and the final extension member bytes agree with the validated package.

- [ ] Step 6: Render-check both sales READMEs.

Use a GitHub-compatible renderer or local browser preview at 1280px and 390px. Confirm promise and download CTAs are in the first viewport, tables wrap safely, code blocks do not force horizontal overflow, bilingual links work, and release links use final asset names. Record renderer and viewport evidence.

---

### Task 5: Push source PR and merge

**External state:** source branch and one PR.

- [ ] Step 1: Before network operations, read C:/Users/HU/.codex/skills/web-access/SKILL.md completely.
- [ ] Step 2: Push and reuse one PR.

    git push origin agent/product-promo-maker-rebrand
    gh pr list --head agent/product-promo-maker-rebrand --base main --json number,url,state

Create a PR only if none exists. Reuse the existing PR if present.
- [ ] Step 3: Wait for checks and squash-merge.

    gh pr checks --watch
    gh pr merge --squash

Do not merge with failing checks. Fetch origin/main and record its full 40-character SHA.

---

### Task 6: Rebuild and publish the public GitHub repository

**External state:** hqwzhu/enhe-promotion-manager, tag v0.5.3, four Release assets.

- [ ] Step 1: Create a clean release worktree from merged origin/main. Do not build the final tree from the unmerged branch.
- [ ] Step 2: Move the Task 4 generated tree to a new non-existing evidence backup after verifying it has no .git, then build a clean C:/Users/HU/Documents/enhe-promotion-manager from merged main.
- [ ] Step 3: Run public builder, validator, tests, checksum verification, and README link checks. Initialize the generated directory only after status=ready.
- [ ] Step 4: After loading web-access, inspect gh repo view hqwzhu/enhe-promotion-manager. If not found, create it public with gh repo create --public --source . --remote origin --push. If it exists, inspect it and stop instead of creating a second repository.
- [ ] Step 5: Tag v0.5.3 and publish exactly the Skill ZIP, extension ZIP, release-manifest.json, and SHA256SUMS. Download them to a temporary in-repository directory and independently compare hashes.

---

### Task 7: Submit the existing Chrome Web Store update

**External state:** item dloklkbnmoigemnfigbkibogmgbieppl.

- [ ] Step 1: Read web-access and playwright-interactive before opening the dashboard.
- [ ] Step 2: Reuse authenticated Chrome, select the exact existing item, confirm current 0.5.2 and unchanged permissions, and upload the final hash-verified 0.5.3 ZIP. Never create a second item.
- [ ] Step 3: Submit the update for review, capture non-sensitive item/version/status evidence, and stop for a fresh verification code, CAPTCHA, 2FA, or account confirmation instead of bypassing it.
- [ ] Step 4: Record submission date, item ID, version, and status in CHANGELOG.md and both version-sync docs without mutating tagged Release assets.

---

### Task 8: Sync Skill and deliver the final audit

- [ ] Step 1: From the merged source release worktree, run:

    python scripts/self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC --skip-runtime-checks --out-dir ./promotion-output/distribution-final-sync

Verify syncResult.status is synced and no managed files are missing or unexpectedly drifted. Never sync .env, .venv, browser profiles, Sidecar runtime data, or generated output.

- [ ] Step 2: Run public validator/tests and confirm all non-payment command references map to shipped Skill scripts. State explicitly that payment/subscription behavior is excluded from the parity conclusion while the existing billing UI remains packaged.
- [ ] Step 3: Verify the public repository, Release, four assets, existing Chrome item, submitted version, review status, and Hosted Worker state.
- [ ] Step 4: Deliver the current stage, completed Skill work, completed extension work, public URLs, parity result, Chrome review status, remaining external gates, and exact manual actions.

## Final Acceptance Commands

    python -m unittest scripts.test_extension_ui scripts.test_public_distribution scripts.test_mediacrawler_sidecar -v
    python -m unittest scripts.test_promotion_manager -v
    python -m compileall -q scripts distribution/scripts distribution/tests
    python scripts/verify_distribution.py
    python -m unittest discover -s tests -v
    Get-Content ./SHA256SUMS
    gh repo view hqwzhu/enhe-promotion-manager --json nameWithOwner,visibility,url,defaultBranchRef
    gh release view v0.5.3 --repo hqwzhu/enhe-promotion-manager --json tagName,url,isDraft,isPrerelease,assets

Completion requires green local gates, a ready public tree, matching release hashes, the public repository and Release, the installed Skill synchronized, the existing Chrome item updated and submitted, Hosted Worker disabled, and the detailed progress/manual-action report delivered.

# ENHE Product Promo Maker v0.5.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the three-platform MediaCrawler release smoke, remove source/installed/public distribution drift, and publish verified v0.5.4 Skill and Chrome extension artifacts.

**Architecture:** Keep MediaCrawler as a separately installed local Sidecar pinned to its approved commit. Land bounded creator-mode adapters in the source repository, sync only managed Skill files after review, assemble the sales repository from reviewed source, and publish immutable v0.5.4 assets instead of replacing v0.5.3.

**Tech Stack:** Python 3.12, unittest, Playwright/Chromium, uv, MediaCrawler Sidecar, Chrome Manifest V3, PowerShell, Git/GitHub CLI, GitHub Actions.

## Global Constraints

- Hosted Worker remains disabled.
- Cookies, Chrome profiles, `.env` files, secrets, raw Sidecar output, and original user IDs must not enter either GitHub repository or a Release asset.
- The Sidecar remains pinned to `3bde9e2015f912f2e19ee63b615a0f48b9a90315`.
- Each real smoke run keeps at most 3 contents and 5 first-level comments per retained content, uses concurrency 1, waits at least 2 seconds between pages, and cleans raw output by default.
- Login, CAPTCHA, account verification, and platform risk confirmation are completed only by the user in a visible local browser.
- v0.5.3 assets are immutable; all post-PR-#5 fixes ship as v0.5.4.
- The public product name is `ENHE 产品推广素材生成器 / ENHE Product Promo Maker`.
- The public product repository is `hqwzhu/enhe-promotion-manager`; the source repository is `hqwzhu/Viral-Product-Copy-Video-Generator`.

---

### Task 1: Bound Douyin and Zhihu creator collection

**Files:**
- Modify: `scripts/mediacrawler_bootstrap.py`
- Modify: `scripts/test_mediacrawler_sidecar.py`

**Interfaces:**
- Produces: `patch_douyin_creator_limit(client_class, requested_max_contents)` and `patch_zhihu_creator_limit(client_class, requested_max_contents)`.
- Preserves: existing XHS detail and Zhihu search patches.

- [ ] **Step 1: Verify the creator-limit tests cover callbacks before downstream persistence**

  Confirm the tests require Douyin to stop pagination at three rows before callback execution and Zhihu to expose at most three rows from its first creator page with `paging.is_end=true`.

- [ ] **Step 2: Run the focused tests**

  Run:

  ```powershell
  .\.venv\Scripts\python.exe -m unittest -v `
    scripts.test_mediacrawler_sidecar.BootstrapTests.test_douyin_creator_limit_stops_pagination_before_callbacks `
    scripts.test_mediacrawler_sidecar.BootstrapTests.test_zhihu_creator_limit_stops_after_the_requested_first_page
  ```

  Expected: `Ran 2 tests` and `OK`.

- [ ] **Step 3: Run the full Sidecar contract suite**

  Run:

  ```powershell
  .\.venv\Scripts\python.exe -m unittest -v scripts.test_mediacrawler_sidecar
  ```

  Expected: all tests pass.

- [ ] **Step 4: Commit only the bootstrap, tests, and this plan**

  ```powershell
  git add scripts/mediacrawler_bootstrap.py scripts/test_mediacrawler_sidecar.py docs/superpowers/plans/2026-07-22-enhe-product-promo-maker-v054.md
  git commit -m "fix: bound creator sidecar collection"
  ```

### Task 2: Verify the installed Skill runtime and full regression

**Files:**
- Verify: `C:\Users\HU\.codex\skills\viral-product-copy-video-generator\.venv`
- Verify: `scripts/test_promotion_manager.py`

**Interfaces:**
- Consumes: reviewed source files from Task 1.
- Produces: versioned test evidence and a drift report.

- [ ] **Step 1: Confirm Pillow in the installed private environment**

  ```powershell
  C:\Users\HU\.codex\skills\viral-product-copy-video-generator\.venv\Scripts\python.exe -c "import PIL; print(PIL.__version__)"
  ```

  Expected: Pillow imports successfully.

- [ ] **Step 2: Run the 185-test main regression**

  ```powershell
  C:\Users\HU\.codex\skills\viral-product-copy-video-generator\.venv\Scripts\python.exe scripts\test_promotion_manager.py
  ```

  Expected: `Ran 185 tests` and `OK`.

- [ ] **Step 3: Run media-focused tests and Sidecar setup check**

  Verify real PNG output exists, `setup --check` reports `ready`, and no credential value is printed.

### Task 3: Complete the real three-platform Sidecar smoke

**Files:**
- Write runtime evidence only under: `promotion-output/mediacrawler-full-smoke-20260722-v054`

**Interfaces:**
- Consumes: current visible Chrome logins and the pinned Sidecar.
- Produces: search/detail/creator/comment evidence for Xiaohongshu, Douyin, and Zhihu plus one successful sub-comment run.

- [ ] **Step 1: Run Xiaohongshu detail, comments, creator, and a bounded sub-comment collection**
- [ ] **Step 2: Run Douyin detail, comments, creator, and a bounded sub-comment collection**
- [ ] **Step 3: Run Zhihu search, detail, comments, creator, and a bounded sub-comment collection**
- [ ] **Step 4: Stop only for visible login, CAPTCHA, account verification, or risk confirmation**
- [ ] **Step 5: Scan every formal run directory**

  Acceptance requires no raw directory, no `run.lock`, no Cookie/Authorization/token/signature value, no original user ID, and no orphan Sidecar Chrome/Python process.

### Task 4: Update the public distribution repository contract

**Files:**
- Modify assembled public `.gitignore`
- Create assembled public `.github/workflows/tests.yml`
- Modify `distribution/` templates and tests that generate or verify those files
- Modify bilingual version/status documentation and `release-manifest.json` inputs

**Interfaces:**
- Produces: an assembled public repository that ignores secrets, tests on Windows and Ubuntu, and reports Chrome Store v0.5.3 as published.

- [ ] **Step 1: Add secret ignore rules**

  The public `.gitignore` must include:

  ```gitignore
  .env
  .env.*
  !.env.example
  ```

- [ ] **Step 2: Add GitHub Actions**

  Create a workflow triggered by `push` and `pull_request` that checks out the repository, sets up Python 3.12, installs `requirements-test.txt`, runs `python scripts/verify_distribution.py`, and runs `python -m unittest discover -s tests -v` on `windows-latest` and `ubuntu-latest`.

- [ ] **Step 3: Update Chrome Store and release documentation**

  Record public Chrome version `0.5.3`, status `published`, and the verified public listing URL. Remove `pending_review` and `0.5.2` claims from current-state sections.

- [ ] **Step 4: Add distribution tests**

  Tests must fail when `.env` ignore rules, the workflow matrix/commands, product name, or published Chrome status drift.

### Task 5: Publish source PR and synchronize the installed Skill

**Files:**
- Source branch: `agent/v054-release`
- Installed target: `C:\Users\HU\.codex\skills\viral-product-copy-video-generator`

**Interfaces:**
- Consumes: reviewed commits from Tasks 1-4.
- Produces: merged source PR and zero managed-file drift.

- [ ] **Step 1: Run source tests and distribution tests**
- [ ] **Step 2: Push `agent/v054-release` and open a draft PR to source `main`**
- [ ] **Step 3: Complete spec and code-quality review, fix Important/Critical findings, and re-review**
- [ ] **Step 4: Mark the PR ready, merge it, and verify source `main`**
- [ ] **Step 5: Run approved Skill sync from reviewed source and rerun drift/setup/tests**

### Task 6: Update GitHub repository presentation

**Files:**
- GitHub repository metadata for `hqwzhu/enhe-promotion-manager`

**Interfaces:**
- Produces: a searchable sales repository header consistent with README.

- [ ] **Step 1: Set description**

  `Turn product pages into bilingual promotion copy, video scripts, media assets, safe publish packs, and evidence-driven optimization.`

- [ ] **Step 2: Set homepage**

  `https://www.enhe-tech.com.cn/`

- [ ] **Step 3: Set topics**

  `codex-skill`, `chrome-extension`, `product-marketing`, `content-automation`, `video-generation`, `xiaohongshu`, `douyin`, `zhihu`, `bilingual`, `enhe-ai`.

- [ ] **Step 4: Read back metadata through GitHub and verify exact values**

### Task 7: Build and publish v0.5.4

**Files:**
- Modify version manifests/changelog/component manifests to `0.5.4`
- Build: `enhe-product-promo-maker-skill-0.5.4.zip`
- Build: `enhe-promotion-manager-extension-0.5.4.zip`
- Build: `release-manifest.json`, `SHA256SUMS`

**Interfaces:**
- Consumes: merged source main and verified extension package.
- Produces: immutable GitHub Release `v0.5.4` in `hqwzhu/enhe-promotion-manager`.

- [ ] **Step 1: Include all post-PR-#5 fixes and creator-limit fixes**
- [ ] **Step 2: Build deterministic packages and verify member bytes and hashes**
- [ ] **Step 3: Push the assembled public repository changes through a PR and require green GitHub Actions**
- [ ] **Step 4: Merge the public PR and publish GitHub Release `v0.5.4`**
- [ ] **Step 5: Download the public assets again and verify SHA-256 and package manifests**
- [ ] **Step 6: Submit Chrome extension v0.5.4 only if the packaged extension bytes changed; user handles any 2FA/CAPTCHA prompt**

### Task 8: Safely organize old checkout and historical worktrees

**Files:**
- Inspect: `C:\Users\HU\Documents\viral-product-copy-video-generator`
- Inspect: registered paths under `.worktrees`

**Interfaces:**
- Consumes: merged commits and clean worktrees.
- Produces: one authoritative clean source checkout plus only worktrees needed for open PRs.

- [ ] **Step 1: Record every worktree path, branch, HEAD, dirty files, and remote containment**
- [ ] **Step 2: Preserve every dirty file or unique commit before cleanup**
- [ ] **Step 3: Remove only clean, merged, project-local historical worktrees**
- [ ] **Step 4: Do not delete the dirty legacy root; move or reconcile its unique changes first**
- [ ] **Step 5: Run `git worktree prune`, verify all remaining absolute paths are inside the intended repository, and confirm final status**

## Completion Evidence

- Pillow imports in the installed Skill venv and the 185-test suite passes.
- Every required real Sidecar mode has a ready manifest or an explicitly user-resolved platform gate, with the final sensitive-output scan passing.
- Both repositories have merged PRs and green required checks.
- Installed Skill managed-file drift is zero.
- Public repository metadata is populated and `.env` files are ignored.
- v0.5.4 assets are publicly downloadable, hash-verified, and contain the reviewed fixes.
- Historical worktree cleanup preserves all user changes and leaves no stale registrations.

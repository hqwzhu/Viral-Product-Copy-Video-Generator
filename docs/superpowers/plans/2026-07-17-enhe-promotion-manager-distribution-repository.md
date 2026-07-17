# ENHE Product Promo Maker Public Distribution Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `hqwzhu/enhe-promotion-manager` as a verified bilingual distribution repository for the ENHE Product Promo Maker Skill and Chrome extension, release version `v0.5.3`, submit the same extension version to the existing Chrome Web Store item, and leave Hosted Worker disabled.

**Architecture:** Keep `C:\Users\HU\Documents\viral-product-copy-video-generator` as the development source of truth. Add a deterministic allowlist-based distribution builder and public release validator to that source repository, generate a clean standalone repository from an exact merged source commit, and publish only verified archives and documentation. The public repository contains the local Skill engine, the byte-faithful extension source, bilingual sales and operating documentation, release manifests, checksums, tests, and release scripts; it excludes backend runtime, deployment secrets, browser state, Sidecar checkout/runtime data, generated outputs, and payment infrastructure.

**Tech Stack:** Python 3.11 `unittest`, `pathlib`, `hashlib`, `json`, `zipfile`, Git, GitHub CLI, Chrome Manifest V3, vanilla HTML/CSS/JavaScript, Chrome Web Store developer dashboard, Playwright browser automation.

---

## Execution Preconditions

- Source worktree: `C:\Users\HU\Documents\viral-product-copy-video-generator\.worktrees\product-promo-maker-rebrand`
- Source branch: `agent/product-promo-maker-rebrand`
- Public repository: `https://github.com/hqwzhu/enhe-promotion-manager`
- Public local checkout: `C:\Users\HU\Documents\enhe-promotion-manager`
- Release version: `0.5.3`
- Existing Chrome Web Store item ID: `dloklkbnmoigemnfigbkibogmgbieppl`
- Store version at plan time: `0.5.2`
- Hosted Worker state: disabled, and it must remain disabled
- Skill sync approval already granted: `I_APPROVE_SKILL_SYNC`
- Any GitHub or Chrome Web Store network operation must first load and follow the `web-access` Skill.
- Browser-dashboard work must load and follow `playwright-interactive`; do not create a second Chrome Web Store item.
- PR execution must preserve unrelated user changes and must not use destructive Git commands.

## File Map

### Source repository files

- Modify `.gitignore`: keep local virtual environments and generated public staging output untracked.
- Modify `scripts/self_evolution_audit.py`: include `requirements-youtube.txt` in installed-Skill synchronization.
- Modify `scripts/test_promotion_manager.py`: add the missing requirements-file sync regression.
- Create `scripts/distribution_contract.py`: single source for versions, identities, public allowlists, command parity, hashes, tree digest, and forbidden-content scanning.
- Create `scripts/build_public_distribution.py`: assemble the standalone public repository from a clean exact source commit.
- Create `scripts/test_public_distribution.py`: focused TDD coverage for the distribution contract and builder.
- Create `distribution/README.md` and `distribution/README.en.md`: Chinese-first and equivalent English sales homepages.
- Create `distribution/NOTICE.md`, `distribution/SECURITY.md`, `distribution/CHANGELOG.md`, and `distribution/.gitignore`: public legal, security, release, and generated-file boundaries.
- Create `distribution/docs/zh-CN/*.md` and `distribution/docs/en/*.md`: bilingual features, install, quick start, component guides, platform research, publishing, privacy, troubleshooting, and version sync.
- Create `distribution/scripts/build_release.py`: build deterministic Skill and extension ZIP files from the public repository.
- Create `distribution/scripts/generate_checksums.py`: write SHA-256 checksums for final release files.
- Create `distribution/scripts/verify_distribution.py`: fail closed on missing docs, drift, forbidden files, suspected secrets, unsafe claims, manifest changes, bad checksums, or Hosted Worker misrepresentation.
- Create `distribution/tests/test_distribution.py`: public-repository smoke and contract tests.

### Generated public repository files

- `skill/viral-product-copy-video-generator/`: approved local Skill runtime files.
- `extension/chrome/`: exact extension source used to build the store ZIP.
- `skill/viral-product-copy-video-generator/component-manifest.json`: Skill version, source commit, runtime, and capability IDs.
- `extension/chrome/component-manifest.json`: extension version, source commit, entry points, and non-payment capability IDs.
- `release-manifest.json`: release version, source commit, tree digest, store item/version state, sync scope, artifact names, hashes, and verification state.
- `SHA256SUMS`: hashes of the final Skill ZIP, extension ZIP, and release manifest.
- `dist/v0.5.3/`: generated local release assets; ignored by Git and uploaded to GitHub Release.

## Stable Distribution Contract

The implementation uses these exact values:

```python
VERSION = "0.5.3"
PUBLISHED_STORE_VERSION = "0.5.2"
STORE_ITEM_ID = "dloklkbnmoigemnfigbkibogmgbieppl"
PUBLIC_REPOSITORY = "hqwzhu/enhe-promotion-manager"
PRODUCT_EN = "ENHE Product Promo Maker"
PRODUCT_ZH = "ENHE 产品推广素材生成器"
PRODUCT_PROMISE_EN = "Turn product pages into promotional copy, video scripts, and publishing assets."
PRODUCT_PROMISE_ZH = "把产品网页变成推广文案、视频脚本和发布素材。"

NON_PAYMENT_COMMANDS = (
    "automation_scheduler.py",
    "browser_publish_session.py",
    "final_capability_readiness.py",
    "launch_unlock_pack.py",
    "performance_monitor.py",
    "promotion_manager.py",
    "real_evidence_inbox.py",
    "real_evidence_inbox_setup.py",
    "skill_entry.py",
    "viral_evidence_inbox.py",
    "viral_evidence_inbox_setup.py",
)
```

Payment plans, checkout, subscription status, license purchase, credits, usage authorization, and billing backend behavior are excluded from the synchronization conclusion. Existing extension billing UI and `billing-contract.json` remain in the verified extension package.

### Task 1: Converge the existing MediaCrawler Sidecar fixes

**Files:**
- Modify: `.gitignore`
- Modify: `docs/mediacrawler-sidecar.md`
- Modify: `scripts/mediacrawler_bootstrap.py`
- Modify: `scripts/mediacrawler_sidecar.py`
- Modify: `scripts/platform_data_manager.py`
- Modify: `scripts/self_evolution_audit.py`
- Modify: `scripts/test_mediacrawler_sidecar.py`
- Modify: `scripts/test_promotion_manager.py`
- Preserve without staging: `docs/zh-CN/installation.md` if it remains status-only with no content diff

- [ ] **Step 1: Confirm the current dirty scope**

Run:

```powershell
git status --short
git diff --name-only
```

Expected: the eight content-diff files listed above; `docs/zh-CN/installation.md` may appear in status because of line-ending metadata but must not appear in `git diff --name-only`.

- [ ] **Step 2: Run the complete focused Sidecar regression suite**

Run:

```powershell
python -m unittest scripts.test_mediacrawler_sidecar -v
```

Expected: `OK`, including these five regressions:

```text
SidecarCommandTests.test_xiaohongshu_detail_command_uses_safe_context_without_signed_parameters
BootstrapTests.test_zhihu_search_limits_upstream_results_before_comment_collection
BootstrapTests.test_xiaohongshu_detail_context_switches_to_filtered_search
SidecarRuntimeTests.test_execute_process_decodes_upstream_output_as_utf8
CliTests.test_xiaohongshu_detail_recovers_query_from_prior_normalized_output
```

- [ ] **Step 3: Run the cross-module regression affected by managed Skill files**

Run:

```powershell
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_self_evolution_managed_files_include_docs_and_browser_extension -v
```

Expected: `OK`.

- [ ] **Step 4: Stage only the eight content changes**

Run:

```powershell
git add -- .gitignore docs/mediacrawler-sidecar.md scripts/mediacrawler_bootstrap.py scripts/mediacrawler_sidecar.py scripts/platform_data_manager.py scripts/self_evolution_audit.py scripts/test_mediacrawler_sidecar.py scripts/test_promotion_manager.py
git diff --cached --name-status
git diff --cached --check
```

Expected: exactly eight staged files and no whitespace error.

- [ ] **Step 5: Commit the validated Sidecar fixes**

Run:

```powershell
git commit -m "fix: harden mediacrawler sidecar collection"
```

Expected: one commit containing only the eight staged files.

### Task 2: Restore complete installed-Skill synchronization

**Files:**
- Modify: `scripts/self_evolution_audit.py:303-326`
- Modify: `scripts/test_promotion_manager.py:8276-8327`
- Runtime sync target: `C:\Users\HU\.codex\skills\viral-product-copy-video-generator`

- [ ] **Step 1: Add a failing requirements-file sync regression**

Extend `test_self_evolution_managed_files_include_docs_and_browser_extension` with these exact assertions:

```python
managed = self_evolution.managed_skill_files(ROOT)
managed_names = {path.as_posix() for path in managed}
self.assertIn("requirements-youtube.txt", managed_names)
self.assertIn("scripts/fixtures/mediacrawler/xiaohongshu-contents.jsonl", managed_names)
self.assertNotIn(".venv/pyvenv.cfg", managed_names)
self.assertNotIn("promotion-output", "\n".join(sorted(managed_names)))
```

- [ ] **Step 2: Run the regression and verify the missing file is reproduced**

Run:

```powershell
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_self_evolution_managed_files_include_docs_and_browser_extension -v
```

Expected: `FAIL` because `requirements-youtube.txt` is not currently managed.

- [ ] **Step 3: Add the requirements file to the explicit standalone allowlist**

Change the standalone list in `managed_skill_files` to:

```python
for standalone in [
    "README.md",
    "README.en.md",
    "README.zh-CN.md",
    "LICENSE",
    ".gitignore",
    "requirements-youtube.txt",
]:
    if (root / standalone).exists():
        files.append(Path(standalone))
```

Do not add `.env`, `.venv`, `promotion-output`, Chrome profiles, Sidecar checkout paths, or runtime state.

- [ ] **Step 4: Run the focused test and synchronization audit tests**

Run:

```powershell
python -m unittest `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_self_evolution_managed_files_include_docs_and_browser_extension `
  scripts.test_promotion_manager.PromotionManagerScriptTest.test_self_evolution_audit_reports_tool_and_skill_state_without_secret_values -v
```

Expected: `OK`.

- [ ] **Step 5: Commit the sync fix**

Run:

```powershell
git add -- scripts/self_evolution_audit.py scripts/test_promotion_manager.py
git diff --cached --check
git commit -m "fix: include youtube requirements in skill sync"
```

Expected: one two-file commit.

- [ ] **Step 6: Synchronize the installed Skill with the approved gate**

Run:

```powershell
python scripts/self_evolution_audit.py `
  --sync-installed-skill `
  --approval I_APPROVE_SKILL_SYNC `
  --skip-runtime-checks `
  --out-dir ".\promotion-output\distribution-sync-audit"
```

Expected: report field `syncResult.status` equals `synced` and the copied-file list contains `requirements-youtube.txt`.

- [ ] **Step 7: Verify source and installed requirements hashes match**

Run:

```powershell
Get-FileHash ".\requirements-youtube.txt" -Algorithm SHA256
Get-FileHash "C:\Users\HU\.codex\skills\viral-product-copy-video-generator\requirements-youtube.txt" -Algorithm SHA256
```

Expected: identical SHA-256 values.

### Task 3: Define and test the public distribution contract

**Files:**
- Create: `scripts/distribution_contract.py`
- Create: `scripts/test_public_distribution.py`

- [ ] **Step 1: Write failing contract tests**

Create `scripts/test_public_distribution.py` with focused tests using `unittest` and temporary directories:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import distribution_contract as contract


ROOT = Path(__file__).resolve().parents[1]


class DistributionContractTest(unittest.TestCase):
    def test_extension_commands_match_the_approved_non_payment_contract(self) -> None:
        popup = (ROOT / "browser-extension" / "popup.js").read_text(encoding="utf-8")
        self.assertEqual(tuple(sorted(contract.extension_command_refs(popup))), contract.NON_PAYMENT_COMMANDS)
        for script_name in contract.NON_PAYMENT_COMMANDS:
            self.assertTrue((ROOT / "scripts" / script_name).is_file(), script_name)

    def test_skill_allowlist_contains_runtime_files_and_excludes_private_modules(self) -> None:
        names = {path.as_posix() for path in contract.skill_files(ROOT)}
        self.assertIn("SKILL.md", names)
        self.assertIn("requirements-youtube.txt", names)
        self.assertIn("scripts/skill_entry.py", names)
        self.assertIn("scripts/fixtures/mediacrawler/douyin-contents.jsonl", names)
        self.assertNotIn("browser-extension/manifest.json", names)
        self.assertFalse(any(name.startswith("backend/") for name in names))
        self.assertFalse(any(name.startswith("deploy/") for name in names))
        self.assertFalse(any("promotion-output" in name for name in names))
        self.assertNotIn("scripts/build_public_distribution.py", names)
        self.assertNotIn("scripts/distribution_contract.py", names)
        self.assertNotIn("scripts/test_public_distribution.py", names)

    def test_forbidden_scan_rejects_env_cookie_and_secret_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".env").write_text("FIRECRAWL_API_KEY=redacted-test-value\n", encoding="utf-8")
            (root / "cookies.json").write_text("{}\n", encoding="utf-8")
            violations = contract.scan_forbidden(root)
            rules = {item["rule"] for item in violations}
            self.assertIn("forbidden_path", rules)

    def test_tree_digest_is_stable_for_the_same_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            (root / "a.txt").write_text("one\n", encoding="utf-8")
            first = contract.tree_digest(root)
            second = contract.tree_digest(root)
            self.assertEqual(first, second)
            self.assertRegex(first, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and confirm the module is missing**

Run:

```powershell
python -m unittest scripts.test_public_distribution -v
```

Expected: import error for `scripts.distribution_contract`.

- [ ] **Step 3: Implement the explicit contract module**

Create `scripts/distribution_contract.py` with these public interfaces and exact allowlist behavior:

```python
from __future__ import annotations

import hashlib
import re
from pathlib import Path


VERSION = "0.5.3"
PUBLISHED_STORE_VERSION = "0.5.2"
STORE_ITEM_ID = "dloklkbnmoigemnfigbkibogmgbieppl"
PUBLIC_REPOSITORY = "hqwzhu/enhe-promotion-manager"
PRODUCT_EN = "ENHE Product Promo Maker"
PRODUCT_ZH = "ENHE 产品推广素材生成器"
PRODUCT_PROMISE_EN = "Turn product pages into promotional copy, video scripts, and publishing assets."
PRODUCT_PROMISE_ZH = "把产品网页变成推广文案、视频脚本和发布素材。"

NON_PAYMENT_COMMANDS = tuple(sorted({
    "automation_scheduler.py",
    "browser_publish_session.py",
    "final_capability_readiness.py",
    "launch_unlock_pack.py",
    "performance_monitor.py",
    "promotion_manager.py",
    "real_evidence_inbox.py",
    "real_evidence_inbox_setup.py",
    "skill_entry.py",
    "viral_evidence_inbox.py",
    "viral_evidence_inbox_setup.py",
}))

SKILL_STANDALONES = ("SKILL.md", "LICENSE", "requirements-youtube.txt")
SKILL_EXCLUDED_SCRIPTS = {
    "build_public_distribution.py",
    "distribution_contract.py",
    "test_public_distribution.py",
}
SKILL_DIRECTORIES = {
    "references": ("*.md",),
    "scripts": ("*.py", "*.jsonl"),
}
FORBIDDEN_PARTS = {
    ".env", ".venv", "node_modules", "promotion-output", "cookies.json",
    "chrome-profile", "user-data-dir", "mediacrawler-backup", "__pycache__",
}
TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}
SECRET_PATTERNS = {
    "github_token": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "firecrawl_key": re.compile(r"fc-[A-Za-z0-9]{20,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "live_license": re.compile(r"pm_live_[A-Za-z0-9]{20,}"),
}


def extension_command_refs(text: str) -> list[str]:
    return sorted(set(re.findall(r"python scripts\\\\([A-Za-z0-9_]+\.py)", text)))


def skill_files(root: Path) -> list[Path]:
    files = [Path(name) for name in SKILL_STANDALONES if (root / name).is_file()]
    for folder, patterns in SKILL_DIRECTORIES.items():
        for pattern in patterns:
            for path in (root / folder).rglob(pattern):
                rel = path.relative_to(root)
                if (
                    path.is_file()
                    and not any(part in FORBIDDEN_PARTS for part in rel.parts)
                    and not (rel.parent == Path("scripts") and rel.name in SKILL_EXCLUDED_SCRIPTS)
                ):
                    files.append(rel)
    return sorted(set(files), key=lambda item: item.as_posix())


def extension_files(root: Path) -> list[Path]:
    extension = root / "browser-extension"
    return sorted(
        (path.relative_to(extension) for path in extension.rglob("*") if path.is_file() and not any(part.startswith(".") for part in path.relative_to(extension).parts)),
        key=lambda item: item.as_posix(),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8") + b"\0" + bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def scan_forbidden(root: Path) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file())):
        rel = path.relative_to(root)
        if any(part.lower() in FORBIDDEN_PARTS for part in rel.parts):
            violations.append({"path": rel.as_posix(), "rule": "forbidden_path"})
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                violations.append({"path": rel.as_posix(), "rule": name})
    return violations
```

- [ ] **Step 4: Run the contract tests**

Run:

```powershell
python -m unittest scripts.test_public_distribution -v
```

Expected: four tests pass.

- [ ] **Step 5: Commit the contract and tests**

Run:

```powershell
git add -- scripts/distribution_contract.py scripts/test_public_distribution.py
git diff --cached --check
git commit -m "test: define public distribution contract"
```

### Task 4: Build a clean standalone repository from reviewed source

**Files:**
- Create: `scripts/build_public_distribution.py`
- Modify: `scripts/test_public_distribution.py`
- Modify: `.gitignore`
- Create: `distribution/.gitignore`
- Create: `distribution/scripts/build_release.py`
- Create: `distribution/scripts/generate_checksums.py`
- Create: `distribution/scripts/verify_distribution.py`
- Create: `distribution/tests/test_distribution.py`

- [ ] **Step 1: Add failing builder and release tests**

Add these tests to `DistributionContractTest`:

```python
from scripts import build_public_distribution as builder

def test_builder_creates_component_manifests_without_private_runtime(self) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / "public"
        builder.build_repository(ROOT, target, source_commit="test-source-commit")
        skill = target / "skill" / "viral-product-copy-video-generator"
        extension = target / "extension" / "chrome"
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertTrue((skill / "requirements-youtube.txt").is_file())
        self.assertTrue((extension / "manifest.json").is_file())
        self.assertFalse((target / "backend").exists())
        self.assertFalse((target / "deploy").exists())
        self.assertEqual(contract.scan_forbidden(target), [])
        release = json.loads((target / "release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(release["version"], "0.5.3")
        self.assertEqual(release["sourceCommit"], "test-source-commit")
        self.assertEqual(release["syncAudit"]["status"], "ready")
        self.assertEqual(release["syncAudit"]["commands"], list(contract.NON_PAYMENT_COMMANDS))

def test_builder_refuses_non_empty_target(self) -> None:
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / "public"
        target.mkdir()
        (target / "keep.txt").write_text("keep\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "target directory is not empty"):
            builder.build_repository(ROOT, target, source_commit="test")
```

- [ ] **Step 2: Run the builder tests and confirm the missing module failure**

Run:

```powershell
python -m unittest scripts.test_public_distribution -v
```

Expected: import error for `scripts.build_public_distribution`.

- [ ] **Step 3: Implement the allowlist-based source builder**

Create `scripts/build_public_distribution.py` with these behaviors:

```python
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import distribution_contract as contract


TEMPLATE_ROOT = ROOT / "distribution"
SKILL_TARGET = Path("skill/viral-product-copy-video-generator")
EXTENSION_TARGET = Path("extension/chrome")


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_repository(source: Path, target: Path, source_commit: str) -> None:
    if target.exists() and any(target.iterdir()):
        raise RuntimeError(f"target directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for path in TEMPLATE_ROOT.rglob("*"):
        if path.is_file():
            copy_file(path, target / path.relative_to(TEMPLATE_ROOT))
    copy_file(source / "LICENSE", target / "LICENSE")
    copy_file(source / "scripts" / "distribution_contract.py", target / "scripts" / "distribution_contract.py")
    for rel in contract.skill_files(source):
        copy_file(source / rel, target / SKILL_TARGET / rel)
    for rel in contract.extension_files(source):
        copy_file(source / "browser-extension" / rel, target / EXTENSION_TARGET / rel)
    popup = (source / "browser-extension" / "popup.js").read_text(encoding="utf-8")
    commands = contract.extension_command_refs(popup)
    missing = [name for name in commands if not (target / SKILL_TARGET / "scripts" / name).is_file()]
    if tuple(commands) != contract.NON_PAYMENT_COMMANDS or missing:
        raise RuntimeError(f"non-payment command drift: commands={commands}, missing={missing}")
    write_json(target / SKILL_TARGET / "component-manifest.json", {
        "name": "viral-product-copy-video-generator",
        "version": contract.VERSION,
        "sourceCommit": source_commit,
        "runtime": "Python 3.11 and Codex",
        "entryPoints": ["SKILL.md", "scripts/skill_entry.py"],
        "capabilityIds": list(contract.NON_PAYMENT_COMMANDS),
    })
    write_json(target / EXTENSION_TARGET / "component-manifest.json", {
        "name": contract.PRODUCT_EN,
        "version": contract.VERSION,
        "sourceCommit": source_commit,
        "runtime": "Chrome Manifest V3",
        "entryPoints": ["manifest.json", "popup.html", "popup.js"],
        "nonPaymentCapabilityIds": list(contract.NON_PAYMENT_COMMANDS),
        "billingParityIncluded": False,
    })
    write_json(target / "release-manifest.json", {
        "version": contract.VERSION,
        "sourceRepository": "https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator",
        "sourceCommit": source_commit,
        "publicRepository": f"https://github.com/{contract.PUBLIC_REPOSITORY}",
        "treeDigest": "pending-final-build",
        "skillArchive": f"enhe-product-promo-maker-skill-{contract.VERSION}.zip",
        "extensionArchive": f"enhe-promotion-manager-extension-{contract.VERSION}.zip",
        "chromeWebStore": {
            "itemId": contract.STORE_ITEM_ID,
            "publishedVersion": contract.PUBLISHED_STORE_VERSION,
            "submittedVersion": None,
            "status": "not_submitted",
        },
        "syncAudit": {
            "scope": "non-payment extension commands to shipped Skill scripts",
            "excluded": ["payment", "subscription", "license purchase", "credits", "billing backend"],
            "commands": list(contract.NON_PAYMENT_COMMANDS),
            "status": "ready",
        },
        "artifacts": {},
        "verification": {"status": "pending", "commands": [
            "python scripts/build_release.py --validated-extension-zip dist/validated/enhe-promotion-manager-0.5.3.zip",
            "python scripts/verify_distribution.py",
            "python -m unittest discover -s tests -v",
        ]},
    })
    violations = contract.scan_forbidden(target)
    if violations:
        raise RuntimeError(f"forbidden public content: {violations}")


def clean_source_commit(source: Path) -> str:
    status = subprocess.run(["git", "status", "--porcelain"], cwd=source, capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise RuntimeError("source repository must be clean before public distribution build")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--validated-extension-zip", required=True)
    args = parser.parse_args()
    source_commit = clean_source_commit(ROOT)
    target = Path(args.output_dir).resolve()
    validated_extension_zip = Path(args.validated_extension_zip).resolve()
    if not validated_extension_zip.is_file():
        raise RuntimeError(f"validated extension zip is missing: {validated_extension_zip}")
    build_repository(ROOT, target, source_commit)
    copy_file(
        validated_extension_zip,
        target / "dist" / "validated" / "enhe-promotion-manager-0.5.3.zip",
    )
    print(f"Public repository assembled at: {target}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implement deterministic public release scripts**

Create `distribution/scripts/generate_checksums.py` with this complete implementation:

```python
from __future__ import annotations

import argparse
from pathlib import Path

import distribution_contract as contract


ROOT = Path(__file__).resolve().parents[1]


def write_checksums(root: Path, relative_paths: list[str], output: Path) -> None:
    lines: list[str] = []
    for name in sorted(relative_paths):
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"checksum input is missing: {name}")
        lines.append(f"{contract.sha256_file(path).upper()}  {name}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--output", default="SHA256SUMS")
    args = parser.parse_args()
    write_checksums(ROOT, args.paths, ROOT / args.output)


if __name__ == "__main__":
    main()
```

Create `distribution/scripts/verify_distribution.py` with the following complete validation flow:

```python
from __future__ import annotations

import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import distribution_contract as contract


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = tuple(
    f"docs/{locale}/{name}.md"
    for locale in ("zh-CN", "en")
    for name in (
        "features", "installation", "quick-start", "skill-guide", "extension-guide",
        "platform-research", "publishing-and-review", "data-and-privacy",
        "troubleshooting", "version-sync",
    )
)
REQUIRED_FILES = (
    "README.md", "README.en.md", "LICENSE", "NOTICE.md", "SECURITY.md", "CHANGELOG.md",
    "release-manifest.json", "skill/viral-product-copy-video-generator/SKILL.md",
    "skill/viral-product-copy-video-generator/requirements-youtube.txt",
    "skill/viral-product-copy-video-generator/component-manifest.json",
    "extension/chrome/manifest.json", "extension/chrome/component-manifest.json",
    "scripts/build_release.py", "scripts/generate_checksums.py",
    "scripts/verify_distribution.py", "scripts/distribution_contract.py",
    "tests/test_distribution.py",
) + REQUIRED_DOCS
BANNED_CLAIMS = ("guaranteed viral", "保证爆款", "自动点击最终发布", "bypass captcha", "绕过验证码")


def read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def public_text(root: Path) -> str:
    chunks: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if ".git" not in path.parts and "dist" not in path.parts:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def verify_required_files(root: Path) -> list[str]:
    return [f"missing required file: {name}" for name in REQUIRED_FILES if not (root / name).is_file()]


def verify_identity_and_links(root: Path) -> list[str]:
    errors: list[str] = []
    zh = (root / "README.md").read_text(encoding="utf-8")
    en = (root / "README.en.md").read_text(encoding="utf-8")
    required_zh = (contract.PRODUCT_ZH, contract.PRODUCT_PROMISE_ZH, "https://www.enhe-tech.com.cn/", "huqingwei5942@gmail.com")
    required_en = (contract.PRODUCT_EN, contract.PRODUCT_PROMISE_EN, "https://www.enhe-tech.com.cn/promotion-manager", "https://github.com/hqwzhu")
    errors.extend(f"README.md missing identity: {value}" for value in required_zh if value not in zh)
    errors.extend(f"README.en.md missing identity: {value}" for value in required_en if value not in en)
    return errors


def verify_versions(root: Path, release: dict) -> list[str]:
    errors: list[str] = []
    extension = read_json(root / "extension/chrome/manifest.json")
    skill_component = read_json(root / "skill/viral-product-copy-video-generator/component-manifest.json")
    extension_component = read_json(root / "extension/chrome/component-manifest.json")
    for label, value in (
        ("release", release.get("version")),
        ("extension", extension.get("version")),
        ("skill component", skill_component.get("version")),
        ("extension component", extension_component.get("version")),
    ):
        if value != contract.VERSION:
            errors.append(f"{label} version is {value!r}, expected {contract.VERSION}")
    return errors


def verify_extension_boundary(root: Path) -> list[str]:
    manifest = read_json(root / "extension/chrome/manifest.json")
    errors: list[str] = []
    if manifest.get("manifest_version") != 3:
        errors.append("extension is not Manifest V3")
    if manifest.get("permissions") != ["activeTab", "storage", "clipboardWrite"]:
        errors.append(f"unexpected extension permissions: {manifest.get('permissions')}")
    if manifest.get("host_permissions") != ["https://www.enhe-tech.com.cn/*"]:
        errors.append(f"unexpected extension host permissions: {manifest.get('host_permissions')}")
    return errors


def verify_non_payment_sync(root: Path, release: dict) -> list[str]:
    popup = (root / "extension/chrome/popup.js").read_text(encoding="utf-8")
    commands = tuple(contract.extension_command_refs(popup))
    errors: list[str] = []
    if commands != contract.NON_PAYMENT_COMMANDS:
        errors.append(f"extension command drift: {commands}")
    if release.get("syncAudit", {}).get("commands") != list(contract.NON_PAYMENT_COMMANDS):
        errors.append("release manifest command list differs from the contract")
    if read_json(root / "extension/chrome/component-manifest.json").get("billingParityIncluded") is not False:
        errors.append("billing parity must remain excluded")
    for name in contract.NON_PAYMENT_COMMANDS:
        if not (root / "skill/viral-product-copy-video-generator/scripts" / name).is_file():
            errors.append(f"shipped Skill is missing command script: {name}")
    return errors


def verify_hosted_worker_language(root: Path) -> list[str]:
    zh = (root / "docs/zh-CN/version-sync.md").read_text(encoding="utf-8")
    en = (root / "docs/en/version-sync.md").read_text(encoding="utf-8")
    errors: list[str] = []
    if "Hosted Worker：关闭" not in zh:
        errors.append("Chinese version guide must state Hosted Worker is off")
    if "Hosted Worker: disabled" not in en:
        errors.append("English version guide must state Hosted Worker is disabled")
    return errors


def verify_claim_boundaries(root: Path) -> list[str]:
    text = public_text(root).lower()
    return [f"unsafe public claim: {claim}" for claim in BANNED_CLAIMS if claim.lower() in text]


def verify_archives(root: Path, release: dict) -> list[str]:
    errors: list[str] = []
    dist = root / "dist" / f"v{contract.VERSION}"
    skill_zip = dist / str(release.get("skillArchive", ""))
    extension_zip = dist / str(release.get("extensionArchive", ""))
    for path in (skill_zip, extension_zip):
        if not path.is_file():
            errors.append(f"release archive is missing: {path.name}")
    if errors:
        return errors
    with zipfile.ZipFile(skill_zip) as archive:
        names = set(archive.namelist())
        if not any(name == "viral-product-copy-video-generator/SKILL.md" for name in names):
            errors.append("Skill ZIP does not contain the expected top-level Skill directory")
    expected_extension = {
        path.relative_to(root / "extension/chrome").as_posix(): path
        for path in (root / "extension/chrome").rglob("*")
        if path.is_file() and path.name != "component-manifest.json"
    }
    with zipfile.ZipFile(extension_zip) as archive:
        names = set(archive.namelist())
        if "manifest.json" not in names:
            errors.append("extension ZIP is missing root manifest.json")
        if "component-manifest.json" in names:
            errors.append("public component-manifest.json must not enter the Chrome ZIP")
        if names != set(expected_extension):
            errors.append("extension ZIP member list differs from extension/chrome source")
        else:
            for name, source in expected_extension.items():
                if archive.read(name) != source.read_bytes():
                    errors.append(f"extension ZIP bytes differ from source: {name}")
    artifacts = release.get("artifacts", {})
    for path in (skill_zip, extension_zip):
        record = artifacts.get(path.name, {})
        if record.get("sha256") != contract.sha256_file(path).upper():
            errors.append(f"artifact hash mismatch in release manifest: {path.name}")
    with tempfile.TemporaryDirectory() as temp:
        extracted = Path(temp)
        with zipfile.ZipFile(skill_zip) as archive:
            archive.extractall(extracted / "skill")
        with zipfile.ZipFile(extension_zip) as archive:
            archive.extractall(extracted / "extension")
        for item in contract.scan_forbidden(extracted):
            errors.append(f"archive forbidden content: {item['path']} ({item['rule']})")
    return errors


def verify_checksums(root: Path) -> list[str]:
    checksum_path = root / "SHA256SUMS"
    if not checksum_path.is_file():
        return ["SHA256SUMS is missing"]
    errors: list[str] = []
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9A-F]{64})  (.+)", line)
        if not match:
            errors.append(f"invalid checksum line: {line}")
            continue
        expected, name = match.groups()
        path = root / name
        if not path.is_file() or contract.sha256_file(path).upper() != expected:
            errors.append(f"checksum mismatch: {name}")
    return errors


def validate(root: Path, check_checksums: bool = True) -> list[str]:
    errors = verify_required_files(root)
    if errors:
        return errors
    release = read_json(root / "release-manifest.json")
    errors.extend(verify_identity_and_links(root))
    errors.extend(verify_versions(root, release))
    errors.extend(verify_extension_boundary(root))
    errors.extend(verify_non_payment_sync(root, release))
    errors.extend(verify_hosted_worker_language(root))
    errors.extend(verify_claim_boundaries(root))
    errors.extend(verify_archives(root, release))
    if check_checksums:
        errors.extend(verify_checksums(root))
    errors.extend(f"forbidden public content: {item['path']} ({item['rule']})" for item in contract.scan_forbidden(root))
    return errors


def main() -> None:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Distribution verification status: ready")


if __name__ == "__main__":
    main()
```

Create `distribution/scripts/build_release.py` with this complete official-artifact flow:

```python
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

import distribution_contract as contract
import generate_checksums
import verify_distribution


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build_skill_zip(output: Path) -> None:
    source = ROOT / "skill" / "viral-product-copy-video-generator"
    with zipfile.ZipFile(output, "w") as archive:
        for path in sorted((item for item in source.rglob("*") if item.is_file()), key=lambda item: item.relative_to(source).as_posix()):
            name = f"viral-product-copy-video-generator/{path.relative_to(source).as_posix()}"
            add_bytes(archive, name, path.read_bytes())


def copy_validated_extension(source_zip: Path, output: Path) -> None:
    expected = {
        path.relative_to(ROOT / "extension/chrome").as_posix(): path
        for path in (ROOT / "extension/chrome").rglob("*")
        if path.is_file() and path.name != "component-manifest.json"
    }
    with zipfile.ZipFile(source_zip) as archive:
        names = set(archive.namelist())
        if names != set(expected) or "manifest.json" not in names or "component-manifest.json" in names:
            raise RuntimeError("validated extension ZIP member list differs from public source")
        for name, path in expected.items():
            if archive.read(name) != path.read_bytes():
                raise RuntimeError(f"validated extension ZIP differs from public source: {name}")
    shutil.copyfile(source_zip, output)


def canonical_tree_digest(release: dict) -> str:
    digest = __import__("hashlib").sha256()
    for path in sorted((item for item in ROOT.rglob("*") if item.is_file()), key=lambda item: item.relative_to(ROOT).as_posix()):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in {".git", "dist"} or rel.as_posix() == "SHA256SUMS":
            continue
        data = path.read_bytes()
        if rel.as_posix() == "release-manifest.json":
            normalized = dict(release)
            normalized["treeDigest"] = "normalized"
            normalized["artifacts"] = {}
            normalized["verification"] = {"status": "normalized", "commands": release["verification"]["commands"]}
            data = (json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        digest.update(rel.as_posix().encode("utf-8") + b"\0" + data)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validated-extension-zip", required=True)
    args = parser.parse_args()
    validated_extension_zip = Path(args.validated_extension_zip).resolve()
    if not validated_extension_zip.is_file():
        raise FileNotFoundError(validated_extension_zip)
    release_path = ROOT / "release-manifest.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if release.get("version") != contract.VERSION:
        raise RuntimeError("release version differs from distribution contract")
    dist = ROOT / "dist" / f"v{contract.VERSION}"
    dist.mkdir(parents=True, exist_ok=True)
    skill_zip = dist / release["skillArchive"]
    extension_zip = dist / release["extensionArchive"]
    build_skill_zip(skill_zip)
    copy_validated_extension(validated_extension_zip, extension_zip)
    release["artifacts"] = {
        path.name: {"bytes": path.stat().st_size, "sha256": contract.sha256_file(path).upper()}
        for path in (skill_zip, extension_zip)
    }
    release["treeDigest"] = canonical_tree_digest(release)
    release["verification"]["status"] = "built"
    write_json(release_path, release)
    errors = verify_distribution.validate(ROOT, check_checksums=False)
    if errors:
        raise RuntimeError("pre-checksum verification failed: " + "; ".join(errors))
    release["verification"]["status"] = "ready"
    write_json(release_path, release)
    generate_checksums.write_checksums(
        ROOT,
        [skill_zip.relative_to(ROOT).as_posix(), extension_zip.relative_to(ROOT).as_posix(), "release-manifest.json"],
        ROOT / "SHA256SUMS",
    )
    final_errors = verify_distribution.validate(ROOT)
    if final_errors:
        raise RuntimeError("final distribution verification failed: " + "; ".join(final_errors))
    print(f"Release assets ready: {dist}")


if __name__ == "__main__":
    main()
```

Create `distribution/tests/test_distribution.py` to run the validator against the repository root, assert all 11 scripts exist, assert billing parity is false, and open both ZIPs to confirm their root layout. The extension ZIP assertion must require `manifest.json` and forbid `component-manifest.json`.

- [ ] **Step 5: Add generated-output ignore rules**

Append to the source `.gitignore`:

```gitignore
dist/public-repository-*/
```

Create `distribution/.gitignore`:

```gitignore
dist/
tmp-release-download/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 6: Run builder tests**

Run:

```powershell
python -m unittest scripts.test_public_distribution -v
python -m compileall -q scripts distribution/scripts distribution/tests
```

Expected: all distribution tests pass and compilation emits no errors.

- [ ] **Step 7: Commit the builder and release tooling**

Run:

```powershell
git add -- .gitignore scripts/distribution_contract.py scripts/build_public_distribution.py scripts/test_public_distribution.py distribution/.gitignore distribution/scripts distribution/tests
git diff --cached --check
git commit -m "feat: add verified public distribution builder"
```

### Task 5: Write the Chinese sales and operating documentation

**Files:**
- Create: `distribution/README.md`
- Create: `distribution/NOTICE.md`
- Create: `distribution/SECURITY.md`
- Create: `distribution/CHANGELOG.md`
- Create: `distribution/docs/zh-CN/features.md`
- Create: `distribution/docs/zh-CN/installation.md`
- Create: `distribution/docs/zh-CN/quick-start.md`
- Create: `distribution/docs/zh-CN/skill-guide.md`
- Create: `distribution/docs/zh-CN/extension-guide.md`
- Create: `distribution/docs/zh-CN/platform-research.md`
- Create: `distribution/docs/zh-CN/publishing-and-review.md`
- Create: `distribution/docs/zh-CN/data-and-privacy.md`
- Create: `distribution/docs/zh-CN/troubleshooting.md`
- Create: `distribution/docs/zh-CN/version-sync.md`

- [ ] **Step 1: Create the Chinese README with the approved sales flow**

Use these exact top-level sections in order:

```markdown
# ENHE 产品推广素材生成器

把产品网页变成推广文案、视频脚本和发布素材。

[English](README.en.md) | [官方网站](https://www.enhe-tech.com.cn/) | [产品页面](https://www.enhe-tech.com.cn/promotion-manager) | [Chrome 商店](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)

## 你提供一个产品网页，我们交付什么
## 它解决的不是“写一篇文案”，而是整套推广准备
## Skill 与 Chrome 插件如何配合
## 核心功能与用户收益
## 五分钟开始使用
## 支持的平台和当前边界
## 本地优先、安全可审计
## 当前版本与下载
## 创作者与联系信息
## 开源许可与第三方组件
```

The first viewport must contain the product name, promise, website, product page, store link, and a compact workflow:

```text
产品网页 -> 产品事实 -> 爆款/竞品证据 -> 平台文案 -> 视频脚本与素材 -> 发布包 -> 真实数据复盘
```

State these creator details exactly:

```text
品牌与创作者：ENHE AI
运营主体：深圳市龙岗区恩禾网络科技工作室
网站：https://www.enhe-tech.com.cn/
产品页面：https://www.enhe-tech.com.cn/promotion-manager
联系邮箱：huqingwei5942@gmail.com
GitHub：https://github.com/hqwzhu
```

- [ ] **Step 2: Write the complete Chinese feature-benefit catalog**

`distribution/docs/zh-CN/features.md` must contain one row for each of these 16 capabilities and exactly these columns:

```text
功能 | 它做什么 | 解决什么问题 | 给用户带来的收益 | 典型场景
```

Required capability rows:

```text
产品网页读取
多链接与网站产品发现
竞品与爆款内容研究
本机登录态 Sidecar 研究
事实、证据与风险控制
平台原生文案生成
视频口播稿与分镜
MP4 视频草稿
封面图与详情图
完整发布包
受控发布辅助
发布后真实证据导入
复盘与下一轮优化
Chrome 当前页面转任务
中英文界面
本地优先隐私
```

Each row must make a factual claim only. Use `可生成草稿` rather than `保证效果`, and state that platform login, CAPTCHA, risk controls, final publication, and application review are never bypassed.

- [ ] **Step 3: Write Chinese installation and quick-start guides**

`installation.md` must document three paths: Chrome Web Store install, unpacked extension load, and Skill ZIP/source install. Include Windows commands first:

```powershell
python --version
python -m pip install playwright pillow
python -m playwright install chromium
python scripts\self_evolution_audit.py --skip-runtime-checks --out-dir ".\promotion-output\install-audit"
```

Explain optional FFmpeg and YouTube dependencies separately. State that MediaCrawler Sidecar is installed separately from its upstream source and that its checkout, Chrome profile, cookies, and runtime output are not included.

`quick-start.md` must use a public example URL and this local-first command shape:

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

Explain the output directories and how to use the extension to generate the same command. Do not require a subscription or Hosted Worker.

- [ ] **Step 4: Write Chinese Skill, extension, research, publishing, privacy, troubleshooting, and sync guides**

The guides must include these exact boundaries:

```text
Hosted Worker：关闭，当前文档不将其描述为可用服务。
Cookie 与 Chrome 登录资料：保留在用户本机，不上传到公开仓库或 Release。
最终发布：必须由用户审核并执行最终确认。
验证码与风控：不绕过；遇到后停止自动化并给出人工操作步骤。
真实效果数据：只导入真实 URL、指标、评论、订单和收入证据，不编造。
支付同步结论：不包含支付、订阅、License 购买、积分或账单后端。
```

`version-sync.md` must distinguish:

```text
公开仓库/Skill/扩展源码版本：0.5.3
Chrome 商店当前公开版本（发布前）：0.5.2
非支付命令引用：11/11 已在随包 Skill 中存在
支付与订阅：不纳入功能同步结论，但扩展原有 UI 和 billing-contract.json 保留
```

- [ ] **Step 5: Write public legal and support metadata**

`NOTICE.md` must identify ENHE-owned MIT code and state that MediaCrawler is a separate upstream dependency whose authorization does not automatically sublicense its source to public users. `SECURITY.md` must direct private vulnerability reports to `huqingwei5942@gmail.com` and instruct users not to open public issues containing secrets or account data. `CHANGELOG.md` must create a `0.5.3 - 2026-07-17` entry covering rebrand, bilingual UI, verified local Skill parity, Sidecar robustness, public distribution, and Hosted Worker remaining disabled.

- [ ] **Step 6: Run Chinese documentation checks**

Run:

```powershell
Select-String -Path "distribution\README.md","distribution\docs\zh-CN\*.md" -Pattern "待定|TODO|保证爆款|绕过验证码"
```

Expected: no output.

- [ ] **Step 7: Commit Chinese documentation**

Run:

```powershell
git add -- distribution/README.md distribution/NOTICE.md distribution/SECURITY.md distribution/CHANGELOG.md distribution/docs/zh-CN
git diff --cached --check
git commit -m "docs: add chinese product distribution guide"
```

### Task 6: Write equivalent English documentation

**Files:**
- Create: `distribution/README.en.md`
- Create: `distribution/docs/en/features.md`
- Create: `distribution/docs/en/installation.md`
- Create: `distribution/docs/en/quick-start.md`
- Create: `distribution/docs/en/skill-guide.md`
- Create: `distribution/docs/en/extension-guide.md`
- Create: `distribution/docs/en/platform-research.md`
- Create: `distribution/docs/en/publishing-and-review.md`
- Create: `distribution/docs/en/data-and-privacy.md`
- Create: `distribution/docs/en/troubleshooting.md`
- Create: `distribution/docs/en/version-sync.md`
- Modify: `scripts/test_public_distribution.py`

- [ ] **Step 1: Add a failing bilingual-document parity test**

Add this test:

```python
def test_distribution_templates_have_matching_bilingual_documents(self) -> None:
    zh = {path.name for path in (ROOT / "distribution" / "docs" / "zh-CN").glob("*.md")}
    en = {path.name for path in (ROOT / "distribution" / "docs" / "en").glob("*.md")}
    self.assertEqual(zh, en)
    self.assertEqual(len(zh), 10)
    self.assertIn(contract.PRODUCT_PROMISE_ZH, (ROOT / "distribution" / "README.md").read_text(encoding="utf-8"))
    self.assertIn(contract.PRODUCT_PROMISE_EN, (ROOT / "distribution" / "README.en.md").read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the parity test and confirm English files are missing**

Run:

```powershell
python -m unittest scripts.test_public_distribution.DistributionContractTest.test_distribution_templates_have_matching_bilingual_documents -v
```

Expected: `FAIL` because the English document set is incomplete.

- [ ] **Step 3: Create the English README and matching guide set**

Use these exact README sections:

```markdown
# ENHE Product Promo Maker

Turn product pages into promotional copy, video scripts, and publishing assets.

[中文](README.md) | [Official website](https://www.enhe-tech.com.cn/) | [Product page](https://www.enhe-tech.com.cn/promotion-manager) | [Chrome Web Store](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)

## What you provide and what the product delivers
## More than one piece of copy: a complete promotion-preparation workflow
## How the Skill and Chrome extension work together
## Capabilities and customer benefits
## Start in five minutes
## Supported platforms and current boundaries
## Local-first and auditable by design
## Current version and downloads
## Creator and contact
## License and third-party components
```

The English feature table uses exactly:

```text
Capability | What it does | Problem it solves | User benefit | Typical use case
```

Translate all 16 Chinese capability rows by meaning, preserve the same limits, and do not shorten the installation, privacy, publishing, troubleshooting, or version-sync guidance.

- [ ] **Step 4: Run bilingual parity and placeholder checks**

Run:

```powershell
python -m unittest scripts.test_public_distribution.DistributionContractTest.test_distribution_templates_have_matching_bilingual_documents -v
Select-String -Path "distribution\README.en.md","distribution\docs\en\*.md" -Pattern "TBD|TODO|guaranteed viral|bypass captcha"
```

Expected: test passes and `Select-String` emits no output.

- [ ] **Step 5: Commit English documentation and parity test**

Run:

```powershell
git add -- distribution/README.en.md distribution/docs/en scripts/test_public_distribution.py
git diff --cached --check
git commit -m "docs: add english product distribution guide"
```

### Task 7: Build and verify the release candidate locally

**Files:**
- Generated outside Git: `C:\Users\HU\Documents\enhe-promotion-manager`
- Generated release assets: `C:\Users\HU\Documents\enhe-promotion-manager\dist\v0.5.3\*`
- Generated/updated: `release-manifest.json`, `SHA256SUMS`

- [ ] **Step 1: Run all source distribution tests**

Run from the source worktree:

```powershell
python -m unittest scripts.test_public_distribution -v
python -m unittest scripts.test_mediacrawler_sidecar -v
python -m unittest scripts.test_promotion_manager -v
python -m compileall -q scripts distribution/scripts distribution/tests
```

Expected: all tests pass and compilation emits no errors.

- [ ] **Step 2: Confirm the source branch is clean before building**

Run:

```powershell
git status --short
```

Expected: no output. If `docs/zh-CN/installation.md` still appears status-only, inspect it and resolve only the line-ending metadata without changing or discarding user content before continuing.

- [ ] **Step 3: Refuse to overwrite an existing public checkout**

Run:

```powershell
if (Test-Path "C:\Users\HU\Documents\enhe-promotion-manager") { throw "Public checkout already exists; inspect it before continuing." }
```

Expected: no output and no exception for the first build. Never delete an existing directory automatically.

- [ ] **Step 4: Assemble the standalone repository**

Run:

```powershell
python scripts\build_public_distribution.py `
  --output-dir "C:\Users\HU\Documents\enhe-promotion-manager" `
  --validated-extension-zip ".\dist\v0.5.3\enhe-promotion-manager-0.5.3.zip"
```

Expected: a clean public tree is created and the reported source commit equals `git rev-parse HEAD`.

- [ ] **Step 5: Build public release archives and checksums**

Run from `C:\Users\HU\Documents\enhe-promotion-manager`:

```powershell
python scripts\build_release.py --validated-extension-zip ".\dist\validated\enhe-promotion-manager-0.5.3.zip"
python scripts\verify_distribution.py
python -m unittest discover -s tests -v
```

Expected: validator status `ready`, all public tests pass, and these files exist:

```text
dist/v0.5.3/enhe-product-promo-maker-skill-0.5.3.zip
dist/v0.5.3/enhe-promotion-manager-extension-0.5.3.zip
release-manifest.json
SHA256SUMS
```

- [ ] **Step 6: Compare the extension archive with the validated package**

Run:

```powershell
Get-FileHash "C:\Users\HU\Documents\enhe-promotion-manager\dist\v0.5.3\enhe-promotion-manager-extension-0.5.3.zip" -Algorithm SHA256
Get-FileHash ".\dist\v0.5.3\enhe-promotion-manager-0.5.3.zip" -Algorithm SHA256
```

Expected: identical SHA-256 values. The accepted validated value is `D01BCCD2D1D8F2AC25B44BF615F4B9F4F3CD4C9E4461C9BF26AA3DCB849CA7B0`. If bytes differ, rerun `scripts/package_browser_extension.py`, inspect the ZIP member list and validation report, update evidence and checksums, and do not publish until the difference is explained.

- [ ] **Step 7: Render-check both README files**

Use a local Markdown preview or GitHub-compatible renderer and verify desktop and mobile widths. Confirm that tables wrap, code blocks scroll, the first viewport shows the promise and product links, and Chinese/English links point to each other.

### Task 8: Push the source changes through the existing PR workflow

**Files:**
- Source branch commits from Tasks 1-6
- No new implementation files in this task

- [ ] **Step 1: Re-run the final source verification**

Run:

```powershell
git status --short
python -m unittest scripts.test_public_distribution scripts.test_mediacrawler_sidecar -v
python -m unittest scripts.test_promotion_manager -v
git log --oneline origin/main..HEAD
```

Expected: clean source branch, green tests, and the distribution commits are visible after `origin/main`.

- [ ] **Step 2: Push the source branch**

After loading `web-access`, run:

```powershell
git push origin agent/product-promo-maker-rebrand
```

Expected: remote branch updates successfully.

- [ ] **Step 3: Create or update one pull request**

Run:

```powershell
gh pr list --head agent/product-promo-maker-rebrand --base main --json number,url,state
```

If no open PR exists, create it:

```powershell
gh pr create `
  --base main `
  --head agent/product-promo-maker-rebrand `
  --title "feat: publish ENHE Product Promo Maker distribution" `
  --body "## Summary`n- publish the bilingual ENHE Product Promo Maker distribution builder and documentation`n- include validated Skill/extension parity and Sidecar fixes`n- keep Hosted Worker disabled`n`n## Verification`n- Python distribution, Sidecar, and full promotion-manager regression suites"
```

If an open PR exists, keep the same PR and verify the new commits are included. Expected: exactly one open PR for the branch.

- [ ] **Step 4: Verify checks and merge**

Run:

```powershell
gh pr checks --watch
gh pr merge --squash
```

Expected: required checks pass and the PR state becomes `MERGED`. Do not merge if a check fails; fix the source branch and repeat verification.

- [ ] **Step 5: Record the merged source commit**

Run:

```powershell
git fetch origin main
git rev-parse origin/main
```

Expected: a full 40-character commit hash used as the public release `sourceCommit`.

### Task 9: Rebuild from merged main and publish the GitHub repository and Release

**Files:**
- Clean release worktree: `C:\Users\HU\Documents\viral-product-copy-video-generator\.worktrees\public-distribution-release`
- Public checkout: `C:\Users\HU\Documents\enhe-promotion-manager`
- GitHub repository: `hqwzhu/enhe-promotion-manager`
- GitHub Release: `v0.5.3`

- [ ] **Step 1: Create a clean release worktree from merged main**

At execution time load `superpowers:using-git-worktrees`, then run from the source repository root:

```powershell
git worktree add "C:\Users\HU\Documents\viral-product-copy-video-generator\.worktrees\public-distribution-release" origin/main
```

Expected: detached clean worktree at the merged `origin/main` commit.

- [ ] **Step 2: Rebuild the public checkout from the merged commit**

Do not delete an unknown existing directory. Verify the existing public checkout is the unpushed generated tree from Task 7, then move it to a timestamped backup before rebuilding:

```powershell
$sourcePublic = (Resolve-Path -LiteralPath "C:\Users\HU\Documents\enhe-promotion-manager").Path
$backupPublic = "C:\Users\HU\Documents\enhe-promotion-manager-premerge-20260717"
if ($sourcePublic -ne "C:\Users\HU\Documents\enhe-promotion-manager") { throw "Unexpected public checkout path: $sourcePublic" }
if (Test-Path -LiteralPath (Join-Path $sourcePublic ".git")) { throw "Public checkout is already a Git repository; inspect before moving." }
if (Test-Path -LiteralPath $backupPublic) { throw "Backup path already exists: $backupPublic" }
Move-Item -LiteralPath $sourcePublic -Destination $backupPublic
python "C:\Users\HU\Documents\viral-product-copy-video-generator\.worktrees\public-distribution-release\scripts\build_public_distribution.py" `
  --output-dir "C:\Users\HU\Documents\enhe-promotion-manager" `
  --validated-extension-zip "C:\Users\HU\Documents\viral-product-copy-video-generator\.worktrees\product-promo-maker-rebrand\dist\v0.5.3\enhe-promotion-manager-0.5.3.zip"
```

Expected: the new `release-manifest.json.sourceCommit` equals the merged `origin/main` commit. Preserve the backup until public release verification finishes.

- [ ] **Step 3: Build and verify final release bytes**

Run from the public checkout:

```powershell
python scripts\build_release.py --validated-extension-zip ".\dist\validated\enhe-promotion-manager-0.5.3.zip"
python scripts\verify_distribution.py
python -m unittest discover -s tests -v
Get-Content .\SHA256SUMS
```

Expected: status `ready`, all tests pass, and the extension checksum remains the validated value unless a newly reviewed package report documents the change.

- [ ] **Step 4: Initialize and commit the public repository**

Run:

```powershell
git init -b main
git add -- .
git diff --cached --check
git commit -m "release: publish ENHE Product Promo Maker 0.5.3"
```

Expected: tracked source, docs, manifests, and checksums; `dist/` remains ignored and is not committed.

- [ ] **Step 5: Create the public GitHub repository**

After loading `web-access`, first verify the repository does not already exist:

```powershell
gh repo view hqwzhu/enhe-promotion-manager --json nameWithOwner,visibility,url
```

Expected before first creation: not found. Then run:

```powershell
gh repo create hqwzhu/enhe-promotion-manager --public --source . --remote origin --push
```

Expected: repository URL `https://github.com/hqwzhu/enhe-promotion-manager`, visibility `PUBLIC`, default branch `main`.

- [ ] **Step 6: Tag and publish GitHub Release v0.5.3**

Run:

```powershell
git tag -a v0.5.3 -m "ENHE Product Promo Maker 0.5.3"
git push origin v0.5.3
gh release create v0.5.3 `
  ".\dist\v0.5.3\enhe-product-promo-maker-skill-0.5.3.zip" `
  ".\dist\v0.5.3\enhe-promotion-manager-extension-0.5.3.zip" `
  ".\release-manifest.json" `
  ".\SHA256SUMS" `
  --title "ENHE Product Promo Maker v0.5.3" `
  --notes "中文：首个独立公开分发版本，包含 Skill、Chrome 扩展、双语安装与功能说明、非支付能力同步审计和 SHA-256 校验。Hosted Worker 保持关闭。`n`nEnglish: First standalone public distribution with the Skill, Chrome extension, bilingual guides, non-payment capability parity audit, and SHA-256 verification. Hosted Worker remains disabled."
```

Expected: one published release attached to tag `v0.5.3`.

- [ ] **Step 7: Download and independently verify public assets**

Run:

```powershell
New-Item -ItemType Directory -Path ".\tmp-release-download" | Out-Null
gh release download v0.5.3 --repo hqwzhu/enhe-promotion-manager --dir ".\tmp-release-download"
Get-FileHash ".\tmp-release-download\enhe-product-promo-maker-skill-0.5.3.zip" -Algorithm SHA256
Get-FileHash ".\tmp-release-download\enhe-promotion-manager-extension-0.5.3.zip" -Algorithm SHA256
```

Expected: hashes match `SHA256SUMS`. The temporary download directory remains untracked and may be removed only after its resolved path is confirmed inside the public checkout.

### Task 10: Submit extension v0.5.3 to the existing Chrome Web Store item

**Files and external state:**
- Upload: `C:\Users\HU\Documents\enhe-promotion-manager\dist\v0.5.3\enhe-promotion-manager-extension-0.5.3.zip`
- Existing item: `dloklkbnmoigemnfigbkibogmgbieppl`
- Update after submission: `CHANGELOG.md`, `docs/zh-CN/version-sync.md`, `docs/en/version-sync.md`

- [ ] **Step 1: Reconfirm the exact upload package**

Run:

```powershell
python scripts\verify_distribution.py
Get-FileHash ".\dist\v0.5.3\enhe-promotion-manager-extension-0.5.3.zip" -Algorithm SHA256
```

Expected: validator `ready` and SHA-256 `D01BCCD2D1D8F2AC25B44BF615F4B9F4F3CD4C9E4461C9BF26AA3DCB849CA7B0`, unless a newly reviewed report explicitly replaces it.

- [ ] **Step 2: Open the Chrome Web Store developer dashboard**

Load `web-access` and `playwright-interactive`, reuse the user's already authenticated Chrome session, open the developer dashboard, and select the existing item whose ID is exactly `dloklkbnmoigemnfigbkibogmgbieppl`.

Expected: current public version is `0.5.2`. Stop if the item ID differs or the dashboard asks to create a new item.

- [ ] **Step 3: Upload version 0.5.3 without changing permissions or listing identity**

Upload the exact ZIP. Confirm the dashboard detects `0.5.3`, Manifest V3, and the same permissions:

```text
activeTab
storage
clipboardWrite
https://www.enhe-tech.com.cn/*
```

Expected: package accepted with no permission-expansion warning. Do not alter pricing, payment, privacy-policy URL, support URL, store item ID, or Hosted Worker state.

- [ ] **Step 4: Save and submit the update for review**

Review the localized store text and screenshots, then submit the existing-item update. This action is authorized by the approved plan. If GitHub/Google requests a fresh one-time verification code, stop only at that gate and request the current code from the user; do not attempt to bypass it.

Expected: dashboard status becomes pending review, under review, or the current Google equivalent for version `0.5.3`.

- [ ] **Step 5: Capture non-sensitive submission evidence**

Save a local screenshot showing only item ID, submitted version, and status. Exclude account email, verification codes, tokens, revenue, or private dashboard details from the public repository.

- [ ] **Step 6: Record the store submission status after the v0.5.3 tag**

Append the submission date, item ID, submitted version `0.5.3`, and status `pending_review` to `CHANGELOG.md`, `docs/zh-CN/version-sync.md`, and `docs/en/version-sync.md`. Keep the tagged `release-manifest.json`, `SHA256SUMS`, and Release assets immutable; do not replace or regenerate them after submission.

- [ ] **Step 7: Commit and push the post-submission status note**

Run:

```powershell
git add -- CHANGELOG.md docs/zh-CN/version-sync.md docs/en/version-sync.md
git commit -m "docs: record chrome 0.5.3 review submission"
git push origin main
```

Expected: tag `v0.5.3` and its assets remain unchanged; the default branch documents the live review state.

### Task 11: Perform the final synchronization and progress audit

**Files and evidence:**
- Source audit output: `promotion-output/distribution-final-audit/`
- Public repository `release-manifest.json`, `SHA256SUMS`, and GitHub Release
- Chrome Web Store submission evidence kept locally

- [ ] **Step 1: Audit the installed Skill against merged source**

Run from the merged source release worktree:

```powershell
python scripts\self_evolution_audit.py `
  --sync-installed-skill `
  --approval I_APPROVE_SKILL_SYNC `
  --skip-runtime-checks `
  --out-dir ".\promotion-output\distribution-final-sync"

python scripts\self_evolution_audit.py `
  --skip-runtime-checks `
  --out-dir ".\promotion-output\distribution-final-audit"
```

Expected: no installed-Skill missing files and no unexpected drift after the approved sync.

- [ ] **Step 2: Reconfirm non-payment Skill/extension parity**

Run from the public repository:

```powershell
python scripts\verify_distribution.py
python -m unittest discover -s tests -v
```

Expected: all 11 extension command references map to shipped Skill scripts; billing parity remains explicitly excluded.

- [ ] **Step 3: Verify public repository and Release state**

After loading `web-access`, run:

```powershell
gh repo view hqwzhu/enhe-promotion-manager --json nameWithOwner,visibility,url,defaultBranchRef
gh release view v0.5.3 --repo hqwzhu/enhe-promotion-manager --json tagName,url,isDraft,isPrerelease,assets
```

Expected: public repository, default branch `main`, non-draft/non-prerelease `v0.5.3`, and four expected assets.

- [ ] **Step 4: Prepare the final user-facing progress report**

Report these sections with current evidence rather than remembered status:

```text
1. 当前阶段
2. Skill 已完成
3. Chrome 插件已完成
4. GitHub 公开仓库与 Release
5. Skill/插件非支付功能同步结论
6. Chrome 商店审核状态
7. Hosted Worker 状态（保持关闭）
8. 未完成事项及原因
9. 用户需要手动完成的事项
10. 每个手动事项的逐步操作与验收标准
```

If Chrome review is pending, state that Google review is the only remaining external gate and no user action is required unless Google requests information. If a fresh 2FA code is required, list only the exact dashboard location and next button; never repeat an expired code or any secret in the report.

## Final Acceptance Commands

Run these immediately before declaring completion:

```powershell
# Source repository
python -m unittest scripts.test_public_distribution scripts.test_mediacrawler_sidecar -v
python -m unittest scripts.test_promotion_manager -v
python -m compileall -q scripts distribution/scripts distribution/tests

# Public repository
python scripts\build_release.py --validated-extension-zip ".\dist\validated\enhe-promotion-manager-0.5.3.zip"
python scripts\verify_distribution.py
python -m unittest discover -s tests -v
Get-Content .\SHA256SUMS

# GitHub state, after loading web-access
gh repo view hqwzhu/enhe-promotion-manager --json nameWithOwner,visibility,url,defaultBranchRef
gh release view v0.5.3 --repo hqwzhu/enhe-promotion-manager --json tagName,url,isDraft,isPrerelease,assets
```

Completion requires all local checks green, the public GitHub repository and release available, the installed Skill synchronized, the existing Chrome item updated to `0.5.3` and submitted for review, Hosted Worker still disabled, and a detailed manual-action report delivered to the user.

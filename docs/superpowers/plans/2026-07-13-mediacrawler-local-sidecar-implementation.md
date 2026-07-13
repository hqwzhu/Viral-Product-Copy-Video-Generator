# MediaCrawler Local Sidecar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a privacy-preserving local MediaCrawler Sidecar for Xiaohongshu, Douyin, and Zhihu that feeds Promotion Manager competitor, comment, creator, and strictly matched own-performance evidence.

**Architecture:** Keep MediaCrawler in a pinned external checkout at commit `3bde9e2015f912f2e19ee63b615a0f48b9a90315` and invoke it through a bounded subprocess adapter. Normalize its JSONL output inside the ENHE project, redact sensitive fields before persistence, and adapt normalized records into the existing Promotion Manager report contracts without importing MediaCrawler as a library.

**Tech Stack:** Python 3 standard library, `unittest`, existing Promotion Manager Python modules, MediaCrawler managed by `uv`, Chrome CDP, Manifest V3 extension JavaScript.

---

## File structure

- Create `scripts/mediacrawler_contract.py`: three-platform normalization, URL sanitization, redaction, JSONL utilities, and manifest-safe values.
- Create `scripts/mediacrawler_sidecar.py`: pinned install metadata, read-only setup checks, safe install command execution, process lock, command building, timeout/cancel/status handling, and raw cleanup.
- Create `scripts/mediacrawler_downstream.py`: conversion into viral library, creator leaderboard, comment evidence, and strictly matched own-performance exports.
- Create `scripts/platform_data_manager.py`: `setup --check`, `setup --install`, and `collect` CLI orchestration.
- Create `scripts/test_mediacrawler_sidecar.py`: isolated offline tests for all new behavior.
- Create `scripts/fixtures/mediacrawler/{xiaohongshu,douyin,zhihu}-{contents,comments}.jsonl`: sanitized upstream fixtures.
- Modify `scripts/promotion_manager.py`: early delegation of the `platform-data` command without changing the current report parser.
- Modify `browser-extension/popup.html`: add local Sidecar command fields.
- Modify `browser-extension/popup.js`: generate copy-only Sidecar commands.
- Create `docs/mediacrawler-sidecar.md`: install, login, run, troubleshooting, safety, and pinned-update instructions.

## Task 1: Establish sanitized fixtures and the normalized contract

**Files:**
- Create: `scripts/fixtures/mediacrawler/xiaohongshu-contents.jsonl`
- Create: `scripts/fixtures/mediacrawler/xiaohongshu-comments.jsonl`
- Create: `scripts/fixtures/mediacrawler/douyin-contents.jsonl`
- Create: `scripts/fixtures/mediacrawler/douyin-comments.jsonl`
- Create: `scripts/fixtures/mediacrawler/zhihu-contents.jsonl`
- Create: `scripts/fixtures/mediacrawler/zhihu-comments.jsonl`
- Create: `scripts/test_mediacrawler_sidecar.py`
- Create: `scripts/mediacrawler_contract.py`

- [ ] **Step 1: Add one sanitized content and two related comment rows per platform**

Use real upstream field names but invented IDs, text, counts, and already-masked nicknames. The Xiaohongshu content fixture must include `note_id`, `note_url`, `xsec_token`, `creator_hash`, `nickname`, `liked_count`, `collected_count`, `comment_count`, `share_count`, `tag_list`, and `source_keyword`. Douyin uses `aweme_id`, `aweme_url`, and the same visible count aliases. Zhihu uses `content_id`, `content_type`, `content_url`, `content_text`, `voteup_count`, and `comment_count`.

- [ ] **Step 2: Write failing normalization tests**

```python
def test_normalizes_three_platform_content_without_sensitive_fields(self):
    expected_ids = {
        "xiaohongshu": "xhs-note-001",
        "douyin": "dy-aweme-001",
        "zhihu": "zh-content-001",
    }
    for platform, expected_id in expected_ids.items():
        raw = self.load_fixture(f"{platform}-contents.jsonl")[0]
        record = self.contract.normalize_content(platform, raw, "fixture", self.salt)
        self.assertEqual(record["schemaVersion"], 1)
        self.assertEqual(record["provider"], "mediacrawler")
        self.assertEqual(record["contentId"], expected_id)
        serialized = json.dumps(record, ensure_ascii=False)
        self.assertNotIn("xsec_token", serialized.lower())
        self.assertNotIn("raw-user", serialized)

def test_normalizes_parent_child_comments_and_deduplicates(self):
    rows = self.load_fixture("xiaohongshu-comments.jsonl")
    normalized = self.contract.normalize_comments("xiaohongshu", rows + [rows[0]], "fixture", self.salt)
    self.assertEqual(len(normalized), 2)
    self.assertIsNone(normalized[0]["parentCommentId"])
    self.assertEqual(normalized[1]["parentCommentId"], normalized[0]["commentId"])
```

- [ ] **Step 3: Run the tests and verify the missing module failure**

Run: `python scripts/test_mediacrawler_sidecar.py ContractTests -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'mediacrawler_contract'`.

- [ ] **Step 4: Implement the minimal contract API**

```python
SCHEMA_VERSION = 1
PROVIDER = "mediacrawler"
PLATFORM_ALIASES = {"xhs": "xiaohongshu", "dy": "douyin", "zhihu": "zhihu"}

def normalize_content(platform: str, raw: dict[str, Any], evidence_path: str, salt: bytes) -> dict[str, Any]:
    mapper = CONTENT_MAPPERS[canonical_platform(platform)]
    record = mapper(raw)
    return sanitize_mapping({
        "schemaVersion": SCHEMA_VERSION,
        "provider": PROVIDER,
        **record,
        "authorHash": local_author_hash(record.pop("_authorHash", ""), salt),
        "authorDisplayName": mask_display_name(record.pop("_authorDisplayName", "")),
        "capturedAt": utc_now(),
        "evidencePath": evidence_path,
    })

def normalize_comments(platform: str, rows: list[dict[str, Any]], evidence_path: str, salt: bytes) -> list[dict[str, Any]]:
    records = [normalize_comment(platform, row, evidence_path, salt) for row in rows]
    return dedupe_by(records, lambda item: (item["platform"], item["contentId"], item["commentId"]))
```

Implement explicit mappers for the exact fixture fields. Missing metrics stay `None`; do not convert missing values to zero.

- [ ] **Step 5: Add and verify URL/recursive redaction tests**

```python
def test_sanitizer_removes_tokens_signatures_cookies_and_raw_ids_recursively(self):
    value = {
        "url": "https://www.xiaohongshu.com/explore/xhs-note-001?xsec_token=secret&xsec_source=pc_search",
        "Authorization": "Bearer secret",
        "nested": {"cookie": "a=b", "signature": "signed", "user_id": "raw-user-001"},
    }
    sanitized = self.contract.sanitize_mapping(value)
    text = json.dumps(sanitized, ensure_ascii=False).lower()
    for secret in ("secret", "bearer", "a=b", "signed", "raw-user-001", "xsec_token"):
        self.assertNotIn(secret, text)
```

Run: `python scripts/test_mediacrawler_sidecar.py ContractTests -v`

Expected: PASS.

- [ ] **Step 6: Commit the isolated contract files**

```powershell
git add -- scripts/mediacrawler_contract.py scripts/test_mediacrawler_sidecar.py scripts/fixtures/mediacrawler
git commit -m "feat: normalize MediaCrawler evidence safely"
```

## Task 2: Build the pinned Sidecar runner

**Files:**
- Create: `scripts/mediacrawler_sidecar.py`
- Modify: `scripts/test_mediacrawler_sidecar.py`

- [ ] **Step 1: Write failing command-boundary tests**

```python
def test_build_command_enforces_safe_limits_and_never_accepts_cookies(self):
    request = self.sidecar.CollectRequest(
        platform="xiaohongshu", mode="search", query="AI 工具", max_contents=20,
        max_comments=30, include_sub_comments=False, timeout_seconds=900,
    )
    command = self.sidecar.build_mediacrawler_command(self.install, request, self.raw_dir)
    self.assertIn("--platform", command)
    self.assertIn("xhs", command)
    self.assertIn("--save_data_option", command)
    self.assertIn("jsonl", command)
    self.assertIn("--max_concurrency_num", command)
    self.assertIn("1", command)
    self.assertNotIn("--cookies", command)

def test_build_command_rejects_limits_above_hard_caps(self):
    with self.assertRaisesRegex(ValueError, "max_contents"):
        self.sidecar.CollectRequest(platform="douyin", mode="search", query="AI", max_contents=21)
```

- [ ] **Step 2: Run and verify the missing runner failure**

Run: `python scripts/test_mediacrawler_sidecar.py SidecarCommandTests -v`

Expected: FAIL because `mediacrawler_sidecar.py` does not exist.

- [ ] **Step 3: Implement pinned metadata and command construction**

```python
UPSTREAM_REPOSITORY = "https://github.com/NanmiCoder/MediaCrawler.git"
UPSTREAM_COMMIT = "3bde9e2015f912f2e19ee63b615a0f48b9a90315"
PLATFORM_FLAGS = {"xiaohongshu": "xhs", "douyin": "dy", "zhihu": "zhihu"}
MAX_CONTENTS = 20
MAX_COMMENTS = 30
DEFAULT_TIMEOUT_SECONDS = 900

@dataclass(frozen=True)
class CollectRequest:
    platform: str
    mode: str
    query: str = ""
    target: str = ""
    max_contents: int = 20
    max_comments: int = 30
    include_sub_comments: bool = False
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        validate_request(self)
```

The command must always set visible mode, JSONL, comments explicitly, subcomments explicitly, concurrency `1`, proxy `false`, the bounded output path, and mode-specific `--keywords`, `--specified_id`, or `--creator_id`.

- [ ] **Step 4: Add failing setup-check tests**

```python
def test_setup_check_is_read_only_and_reports_commit_mismatch(self):
    before = sorted(path.relative_to(self.temp_dir) for path in self.temp_dir.rglob("*"))
    report = self.sidecar.check_setup(self.install)
    after = sorted(path.relative_to(self.temp_dir) for path in self.temp_dir.rglob("*"))
    self.assertEqual(before, after)
    self.assertEqual(report["status"], "provider_unavailable")
    self.assertFalse(report["writesPerformed"])
```

- [ ] **Step 5: Implement read-only checks and explicit installation**

`check_setup()` checks `git`, `uv`, Chrome, checkout, exact commit, environment executable, and writable parent without creating any file. `install_sidecar()` is called only by `setup --install`, clones with `git clone --no-checkout`, checks out the fixed commit, runs `uv sync --python 3.11`, then writes an install manifest outside the project.

- [ ] **Step 6: Add fake-process tests for status, timeout, cancel, lock, and cleanup**

```python
def test_runner_times_out_releases_lock_and_removes_raw_by_default(self):
    result = self.sidecar.run_sidecar(
        self.install,
        self.request,
        self.run_dir,
        process_factory=self.fake_timeout_process,
        sleep=lambda _: None,
    )
    self.assertEqual(result.status, "error")
    self.assertEqual(result.reason, "timeout")
    self.assertFalse(self.sidecar.lock_path(self.install).exists())
    self.assertFalse((self.run_dir / "raw").exists())
```

Add separate tests for `waiting_login`, `manual_verification_required`, `blocked_by_platform`, `no_results`, nonzero exit, one transient retry, and partial normalized output. Fake processes write fixture JSONL into the expected MediaCrawler directory tree; no real Chrome or network is used.

- [ ] **Step 7: Implement the minimal process runner**

Use `subprocess.Popen` with a list of arguments, `cwd` set to the pinned checkout, captured text streams, and a 15-minute default timeout. Persist only redacted tails. On timeout/cancel terminate only the spawned process tree, release the lock in `finally`, and never enumerate or terminate Chrome.

- [ ] **Step 8: Run runner tests and commit**

Run: `python scripts/test_mediacrawler_sidecar.py SidecarCommandTests SidecarRuntimeTests -v`

Expected: PASS.

```powershell
git add -- scripts/mediacrawler_sidecar.py scripts/test_mediacrawler_sidecar.py
git commit -m "feat: add pinned MediaCrawler sidecar runner"
```

## Task 3: Connect normalized data to existing Promotion Manager evidence

**Files:**
- Create: `scripts/mediacrawler_downstream.py`
- Modify: `scripts/test_mediacrawler_sidecar.py`

- [ ] **Step 1: Write failing competitor and comment adapter tests**

```python
def test_downstream_builds_viral_creator_and_comment_outputs(self):
    artifacts = self.downstream.write_downstream_artifacts(
        self.out_dir,
        self.run_dir,
        self.contents,
        self.comments,
        published_items=[],
    )
    self.assertTrue(Path(artifacts["viralContentLibrary"]).exists())
    self.assertTrue(Path(artifacts["creatorLeaderboard"]).exists())
    comment_report = json.loads(Path(artifacts["commentEvidence"]).read_text(encoding="utf-8"))
    self.assertEqual(comment_report["summary"]["commentCount"], len(self.comments))
```

- [ ] **Step 2: Write failing strict own-performance tests**

```python
def test_only_exact_registered_content_enters_owned_metrics(self):
    published = [{
        "platform": "douyin", "contentId": "dy-aweme-001",
        "publishedUrl": "https://www.douyin.com/video/dy-aweme-001", "publishStatus": "published",
    }]
    competitor = {**self.contents[0], "platform": "douyin", "contentId": "competitor-999", "sourceUrl": "https://www.douyin.com/video/competitor-999"}
    matched = self.downstream.match_owned_metrics([self.contents[1], competitor], published)
    self.assertEqual([item["contentId"] for item in matched], ["dy-aweme-001"])
```

Add a second test proving that equal titles, author hashes, keywords, or similar text never match. Add URL-only matching where both canonical URLs are exactly equal after removing fragments, tracking parameters, and sensitive query parameters.

- [ ] **Step 3: Run and verify missing adapter failures**

Run: `python scripts/test_mediacrawler_sidecar.py DownstreamTests -v`

Expected: FAIL because `mediacrawler_downstream.py` does not exist.

- [ ] **Step 4: Implement adapters using existing modules**

```python
def match_owned_metrics(contents: list[dict[str, Any]], published_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {(clean(item.get("platform")), clean(item.get("contentId"))): item for item in published_items if item.get("contentId")}
    by_url = {(clean(item.get("platform")), canonical_public_url(item.get("publishedUrl", ""))): item for item in published_items if item.get("publishedUrl")}
    matches = []
    for content in contents:
        platform = clean(content.get("platform"))
        registered = by_id.get((platform, clean(content.get("contentId"))))
        if registered is None:
            registered = by_url.get((platform, canonical_public_url(content.get("sourceUrl", ""))))
        if registered is not None:
            matches.append(metric_record(content, registered))
    return matches
```

Build search-capture records with `platform_search_capture.normalize_records`, then call `viral_content_library.build_materials` and `creator_leaderboard.build_creators`. Convert normalized comments to the existing comment evidence shape and use `comment_evidence_capture.demand_signals_for_comments`, `build_report`, and `write_outputs`. Write own metrics as a `records` JSON export accepted by `metrics_intake.records_from_json`.

- [ ] **Step 5: Run downstream tests and commit**

Run: `python scripts/test_mediacrawler_sidecar.py DownstreamTests -v`

Expected: PASS.

```powershell
git add -- scripts/mediacrawler_downstream.py scripts/test_mediacrawler_sidecar.py
git commit -m "feat: feed MediaCrawler evidence into promotion reports"
```

## Task 4: Add the CLI and Promotion Manager delegation

**Files:**
- Create: `scripts/platform_data_manager.py`
- Modify: `scripts/promotion_manager.py`
- Modify: `scripts/test_mediacrawler_sidecar.py`

- [ ] **Step 1: Write failing CLI tests**

```python
def test_collect_parser_rejects_cookie_arguments_and_applies_safe_defaults(self):
    args = self.cli.parse_args(["collect", "--platform", "xiaohongshu", "--mode", "search", "--query", "AI 工具"])
    self.assertEqual(args.max_contents, 20)
    self.assertEqual(args.max_comments, 30)
    self.assertFalse(args.include_sub_comments)
    with self.assertRaises(SystemExit):
        self.cli.parse_args(["collect", "--platform", "xiaohongshu", "--mode", "search", "--query", "AI", "--cookies", "secret"])
```

Add CLI subprocess tests for `setup --check` and an offline `collect --fixture-dir scripts/fixtures/mediacrawler` path. The fixture path exists only for tests and local review; it must be recorded as `captureMode: fixture`.

- [ ] **Step 2: Run and verify missing CLI failure**

Run: `python scripts/test_mediacrawler_sidecar.py CliTests -v`

Expected: FAIL because `platform_data_manager.py` does not exist.

- [ ] **Step 3: Implement the CLI**

```python
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect guarded local platform evidence.")
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup")
    setup_mode = setup.add_mutually_exclusive_group(required=True)
    setup_mode.add_argument("--check", action="store_true")
    setup_mode.add_argument("--install", action="store_true")
    collect = sub.add_parser("collect")
    collect.add_argument("--platform", required=True, choices=["xiaohongshu", "douyin", "zhihu"])
    collect.add_argument("--mode", required=True, choices=["search", "detail", "creator"])
    collect.add_argument("--query", default="")
    collect.add_argument("--target", default="")
    collect.add_argument("--max-contents", type=bounded_contents, default=20)
    collect.add_argument("--max-comments", type=bounded_comments, default=30)
    collect.add_argument("--include-sub-comments", action="store_true")
    collect.add_argument("--keep-raw", action="store_true")
    collect.add_argument("--timeout-seconds", type=bounded_timeout, default=900)
    collect.add_argument("--fixture-dir", default="", help="Offline sanitized MediaCrawler fixture directory.")
    collect.add_argument("--out-dir", default="./promotion-output")
    return parser.parse_args(argv)
```

Each collect run creates a unique run directory, writes normalized JSONL and `run-manifest.json`, invokes downstream adapters for available records, and returns a manifest status instead of raising for user-action states. Raw data is deleted by default after normalization and a final secret scan.

- [ ] **Step 4: Add an early delegate in `promotion_manager.py`**

At the start of `main()` before `parse_args()`:

```python
if len(sys.argv) > 1 and sys.argv[1] == "platform-data":
    from platform_data_manager import main as platform_data_main
    platform_data_main(sys.argv[2:])
    return
```

Add `import sys`. Do not change the existing report-command choices or required product arguments.

- [ ] **Step 5: Run CLI and existing Promotion Manager regression tests**

Run:

```powershell
python scripts/test_mediacrawler_sidecar.py CliTests -v
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_web_data_provider_scrape_fixture_writes_report_without_secrets
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_viral_content_library_ranks_multiplatform_capture_reports
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_comment_evidence_capture_extracts_public_comments_and_demand_signals
```

Expected: all selected tests PASS.

- [ ] **Step 6: Commit only clean new files**

```powershell
git add -- scripts/platform_data_manager.py scripts/test_mediacrawler_sidecar.py
git commit -m "feat: add platform data sidecar CLI"
```

Keep the pre-existing dirty `scripts/promotion_manager.py` unstaged and report its added delegation hunk separately.

## Task 5: Add copy-only browser extension command generation

**Files:**
- Modify: `browser-extension/popup.html`
- Modify: `browser-extension/popup.js`
- Modify: `scripts/test_mediacrawler_sidecar.py`

- [ ] **Step 1: Write failing static extension tests**

```python
def test_extension_generates_sidecar_command_without_new_high_privilege_permissions(self):
    manifest = json.loads((ROOT / "browser-extension/manifest.json").read_text(encoding="utf-8"))
    html = (ROOT / "browser-extension/popup.html").read_text(encoding="utf-8")
    javascript = (ROOT / "browser-extension/popup.js").read_text(encoding="utf-8")
    self.assertIn('value="platform_data_collect"', html)
    self.assertIn("generatePlatformDataCommand", javascript)
    self.assertIn("scripts/promotion_manager.py platform-data collect", javascript)
    self.assertNotIn("nativeMessaging", manifest.get("permissions", []))
    self.assertFalse(any("localhost" in value for value in manifest.get("host_permissions", [])))
```

- [ ] **Step 2: Run and verify the missing UI failure**

Run: `python scripts/test_mediacrawler_sidecar.py ExtensionTests -v`

Expected: FAIL because the Sidecar command type is absent.

- [ ] **Step 3: Add minimal Sidecar fields and command generation**

Add command type `platform_data_collect`, one platform select limited to Xiaohongshu/Douyin/Zhihu, mode select, query/target input, and subcomment checkbox. Generate only this command form:

```javascript
function generatePlatformDataCommand() {
  const args = [
    "python scripts/promotion_manager.py platform-data collect",
    `--platform ${els.platformDataPlatform.value}`,
    `--mode ${els.platformDataMode.value}`,
    `--out-dir ${quote(els.outDir.value || ".\\promotion-output")}`
  ];
  if (els.platformDataMode.value === "search") args.push(`--query ${quote(els.platformDataTarget.value.trim())}`);
  else args.push(`--target ${quote(els.platformDataTarget.value.trim())}`);
  if (els.platformDataSubComments.checked) args.push("--include-sub-comments");
  els.commandOutput.value = args.join(" ");
}
```

Do not change `browser-extension/manifest.json` permissions or host permissions.

- [ ] **Step 4: Run extension tests**

Run:

```powershell
python scripts/test_mediacrawler_sidecar.py ExtensionTests -v
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_browser_extension_manifest_popup_and_subscription_ui_are_static_mv3
```

Expected: PASS.

Keep the pre-existing dirty browser extension files unstaged and report the exact Sidecar UI hunks separately.

## Task 6: Document operation and verify the full offline boundary

**Files:**
- Create: `docs/mediacrawler-sidecar.md`
- Modify: `scripts/test_mediacrawler_sidecar.py`

- [ ] **Step 1: Write the operational guide**

Document:

- `setup --check` as read-only.
- `setup --install` as the only network installation action.
- Local visible Chrome login and manual captcha/slider handling.
- Search, detail, and creator examples for all three platforms.
- Safe defaults, hard caps, statuses, cancellation, raw cleanup, and `--keep-raw` warning.
- Output paths and downstream artifacts.
- Troubleshooting for missing `uv`, Chrome/CDP unavailable, login wait, manual verification, platform block, timeout, and upstream schema change.
- Exact pinned commit and the fixture/regression/manual-smoke gates required before updating it.
- Commercial authorization evidence stays outside the public repository.

- [ ] **Step 2: Add a final offline acceptance test**

The test runs the CLI against all six fixtures, verifies three normalized content rows and six comments, runs downstream adapters, scans every generated JSON/JSONL/log file for secret markers, and confirms no `raw/` directory remains.

- [ ] **Step 3: Run the complete dedicated suite**

Run: `python scripts/test_mediacrawler_sidecar.py -v`

Expected: all MediaCrawler tests PASS with no network or real browser access.

- [ ] **Step 4: Run focused project regression tests**

Run:

```powershell
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_web_data_provider_scrape_fixture_writes_report_without_secrets
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_viral_content_library_ranks_multiplatform_capture_reports
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_creator_leaderboard_groups_viral_materials_by_creator
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_comment_evidence_capture_extracts_public_comments_and_demand_signals
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_metrics_recovery_reads_default_published_items_report
python scripts/test_promotion_manager.py PromotionManagerScriptTest.test_browser_extension_manifest_popup_and_subscription_ui_are_static_mv3
```

Expected: all selected tests PASS.

- [ ] **Step 5: Commit clean documentation and tests**

```powershell
git add -- docs/mediacrawler-sidecar.md scripts/test_mediacrawler_sidecar.py
git commit -m "docs: explain MediaCrawler sidecar operation"
```

- [ ] **Step 6: Record the manual smoke gate without executing it automatically**

Report that real Xiaohongshu, Douyin, and Zhihu smoke tests still require the user to log in locally. Do not launch a real collection until the user is present to handle login or verification. The implementation is code-complete only after offline tests pass; release completion still requires the manual smoke criteria in the approved design.

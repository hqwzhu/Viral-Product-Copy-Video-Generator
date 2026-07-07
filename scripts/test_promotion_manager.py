#!/usr/bin/env python3
"""Regression tests for the viral product promotion skill script."""

from __future__ import annotations

import json
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promotion_manager.py"
PRODUCT_INTAKE = ROOT / "scripts" / "product_intake.py"
BROWSER_SNAPSHOT = ROOT / "scripts" / "browser_snapshot.py"
PRODUCT_URL_READER = ROOT / "scripts" / "product_url_reader.py"
RENDER_VIDEO = ROOT / "scripts" / "render_video.py"
COMPETITOR_INTAKE = ROOT / "scripts" / "competitor_intake.py"
COMPETITOR_DISCOVERY = ROOT / "scripts" / "competitor_discovery.py"
COMPETITOR_COLLECTOR = ROOT / "scripts" / "competitor_collector.py"
METRICS_INTAKE = ROOT / "scripts" / "metrics_intake.py"
METRICS_RECOVERY = ROOT / "scripts" / "metrics_recovery.py"
PUBLISHED_ITEMS = ROOT / "scripts" / "published_items.py"
PUBLISH_EXECUTOR = ROOT / "scripts" / "publish_executor.py"
PUBLISH_QUEUE = ROOT / "scripts" / "publish_queue.py"
PUBLISH_READINESS = ROOT / "scripts" / "publish_readiness_runner.py"
PUBLISH_URL_CAPTURE = ROOT / "scripts" / "publish_url_capture.py"
YOUTUBE_OAUTH_PUBLISH = ROOT / "scripts" / "youtube_oauth_publish.py"
RUN_WORKFLOW = ROOT / "scripts" / "run_promotion_workflow.py"
PROMOTION_CYCLE_RUNNER = ROOT / "scripts" / "promotion_cycle_runner.py"
AUTOMATION_SCHEDULER = ROOT / "scripts" / "automation_scheduler.py"
PLATFORM_SEARCH_CAPTURE = ROOT / "scripts" / "platform_search_capture.py"
PLATFORM_SEARCH_BROWSER = ROOT / "scripts" / "platform_search_browser.py"
VIRAL_CONTENT_LIBRARY = ROOT / "scripts" / "viral_content_library.py"
FOLLOW_UP_CAPTURE_RUNNER = ROOT / "scripts" / "follow_up_capture_runner.py"
COMPETITOR_CONTENT_ENHANCER = ROOT / "scripts" / "competitor_content_enhancer.py"
CREATOR_LEADERBOARD = ROOT / "scripts" / "creator_leaderboard.py"
CREATOR_FOLLOW_UP_RUNNER = ROOT / "scripts" / "creator_follow_up_runner.py"
FINAL_CAPABILITY_AUDIT = ROOT / "scripts" / "final_capability_audit.py"
PLATFORM_ACCESS_AUDIT = ROOT / "scripts" / "platform_access_audit.py"
VIRAL_DISCOVERY_RUNNER = ROOT / "scripts" / "viral_discovery_runner.py"


def playwright_chromium_available() -> bool:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from playwright.sync_api import sync_playwright\n"
                "p=sync_playwright().start()\n"
                "b=p.chromium.launch(headless=True)\n"
                "b.close()\n"
                "p.stop()\n"
            ),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


class PromotionManagerScriptTest(unittest.TestCase):
    def run_all(self) -> Path:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-manager-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "all",
                "--product-name",
                "AI Prompt Kit",
                "--product-url",
                "https://www.enhe-tech.com.cn/validation/ai-prompt-kit",
                "--audience",
                "AI tool operators, creators, ecommerce sellers",
                "--value-proposition",
                "Prompt templates for product copy, SEO content, and video scripts",
                "--goal",
                "leads",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        return out_dir

    def load_json(self, out_dir: Path, relative: str):
        return json.loads((out_dir / relative).read_text(encoding="utf-8"))

    def test_full_pipeline_outputs_required_reports(self) -> None:
        out_dir = self.run_all()
        required = [
            "docs/promotion-manager/01-platform-publishing-feasibility.md",
            "docs/promotion-manager/02-github-reference-projects.md",
            "docs/promotion-manager/03-platform-risk-matrix.md",
            "docs/promotion-manager/04-self-learning-notes.md",
            "docs/promotion-manager/05-browser-extension-roadmap.md",
            "docs/promotion-manager/06-saas-product-roadmap.md",
            "reports/promotion-manager/research/platform-publishing-feasibility.json",
            "reports/promotion-manager/research/github-reference-projects.json",
            "reports/promotion-manager/content-plans/ai-prompt-kit-content-plan.json",
            "reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json",
            "reports/promotion-manager/generated-content/ai-prompt-kit-content-review.json",
            "reports/promotion-manager/publish-packs/ai-prompt-kit-publish-pack.json",
            "reports/promotion-manager/publish-results/ai-prompt-kit-publish-result-input.json",
            "reports/promotion-manager/retrospectives/ai-prompt-kit-retrospective.json",
        ]
        for relative in required:
            self.assertTrue((out_dir / relative).exists(), relative)

    def test_platform_capability_safety_defaults(self) -> None:
        out_dir = self.run_all()
        capabilities = self.load_json(out_dir, "reports/promotion-manager/publish-packs/platform-publish-capability-map.json")
        by_platform = {item["platform"]: item for item in capabilities}
        self.assertEqual(by_platform["youtube"]["recommendedMode"], "official_api_publish")
        self.assertEqual(by_platform["github"]["recommendedMode"], "official_api_publish")
        self.assertTrue(by_platform["youtube"]["approvalRequired"])
        self.assertTrue(by_platform["github"]["approvalRequired"])
        self.assertEqual(by_platform["xiaohongshu"]["recommendedMode"], "manual_publish_required")
        self.assertFalse(by_platform["xiaohongshu"]["supportsDirectPublish"])
        self.assertEqual(by_platform["zhihu"]["recommendedMode"], "manual_publish_required")
        self.assertFalse(by_platform["zhihu"]["supportsDirectPublish"])
        self.assertEqual(by_platform["douyin"]["recommendedMode"], "browser_assisted_publish")

    def test_generated_content_counts_and_cta(self) -> None:
        out_dir = self.run_all()
        content = self.load_json(out_dir, "reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json")
        self.assertEqual(len(content["youtube"]["formats"]["longVideoTitles"]), 10)
        self.assertEqual(len(content["youtube"]["formats"]["shortsTitles"]), 10)
        self.assertEqual(len(content["xiaohongshu"]["formats"]["noteTitles"]), 20)
        self.assertEqual(len(content["xiaohongshu"]["formats"]["notes"]), 5)
        self.assertEqual(len(content["douyin"]["formats"]["voiceoverTitles"]), 20)
        self.assertEqual(len(content["douyin"]["formats"]["thirtySecondScripts"]), 5)
        for item in content.values():
            self.assertTrue(item["cta"])

    def test_review_publish_result_and_retrospective_guardrails(self) -> None:
        out_dir = self.run_all()
        review = self.load_json(out_dir, "reports/promotion-manager/generated-content/ai-prompt-kit-content-review.json")
        self.assertTrue(all("complianceScore" in item for item in review))
        self.assertTrue(all(item["cheatOnContent"]["status"] == "fallback_scorecard_used" for item in review))

        publish_pack = self.load_json(out_dir, "reports/promotion-manager/publish-packs/ai-prompt-kit-publish-pack.json")
        self.assertTrue(all(item["approvalRequired"] for item in publish_pack))
        self.assertTrue(all(item["publishSteps"] for item in publish_pack))
        warnings = " ".join(" ".join(item["warnings"]) for item in publish_pack)
        self.assertIn("No cookie/token/password storage", warnings)
        self.assertIn("No captcha bypass", warnings)

        results = self.load_json(out_dir, "reports/promotion-manager/publish-results/ai-prompt-kit-publish-result-input.json")
        self.assertTrue(all(item["published"] is False for item in results))
        self.assertTrue(all(item["views"] is None and item["revenue"] is None for item in results))

        retrospective = self.load_json(out_dir, "reports/promotion-manager/retrospectives/ai-prompt-kit-retrospective.json")
        self.assertEqual(retrospective["status"], "waiting_real_data")
        self.assertEqual(retrospective["publishedItems"], [])

    def test_product_intake_extracts_profile_from_html(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="product-intake-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_path = out_dir / "product.html"
        html_path.write_text(
            """<!doctype html>
<html>
<head>
  <title>AI Prompt Kit - ENHE</title>
  <meta name="description" content="Prompt templates for product copy, SEO content, and video scripts.">
  <meta property="og:title" content="AI Prompt Kit">
  <meta property="og:image" content="https://example.com/cover.png">
  <script type="application/ld+json">{"@type":"Product","name":"AI Prompt Kit","offers":{"price":"19"}}</script>
</head>
<body>AI Prompt Kit</body>
</html>""",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(PRODUCT_INTAKE), "--html-file", str(html_path), "--out-dir", str(out_dir / "intake")],
            check=True,
            cwd=ROOT,
        )
        profile = json.loads((out_dir / "intake" / "product-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["productName"], "AI Prompt Kit")
        self.assertEqual(profile["pricing"], "19")
        self.assertIn("Prompt templates", profile["valueProposition"])
        self.assertTrue((out_dir / "intake" / "product-profile.md").exists())

    def test_product_intake_accepts_structured_page_snapshot(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="product-structured-intake-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "pricing": "$19",
                    "images": [{"url": "https://example.com/cover.png"}],
                    "targetAudience": ["AI operators", "content marketers"],
                    "painPoints": ["Blank page copywriting", "Slow launch content"],
                    "text": "AI Prompt Kit helps turn a product URL into platform-native promotion content.",
                }
            ),
            encoding="utf-8-sig",
        )
        subprocess.run(
            [
                sys.executable,
                str(PRODUCT_INTAKE),
                "--structured-json",
                str(snapshot_path),
                "--out-dir",
                str(out_dir / "intake"),
            ],
            check=True,
            cwd=ROOT,
        )
        profile = json.loads((out_dir / "intake" / "product-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["sourceType"], "structured_json")
        self.assertEqual(profile["productName"], "AI Prompt Kit")
        self.assertEqual(profile["pricing"], "$19")
        self.assertEqual(profile["targetAudienceAssumptions"], ["AI operators", "content marketers"])
        self.assertEqual(profile["painPointAssumptions"], ["Blank page copywriting", "Slow launch content"])

    def test_product_intake_accepts_rendered_text_snapshot(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="product-text-intake-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        text_path = out_dir / "rendered.txt"
        text_path.write_text(
            """Product: AI Prompt Kit
URL: https://example.com/ai-prompt-kit
Pricing: $19
Audience: AI operators, content marketers
Pain Points: Blank page copywriting, slow launch content

Prompt templates for product copy, SEO content, and video scripts.
""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PRODUCT_INTAKE),
                "--text-file",
                str(text_path),
                "--out-dir",
                str(out_dir / "intake"),
            ],
            check=True,
            cwd=ROOT,
        )
        profile = json.loads((out_dir / "intake" / "product-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["sourceType"], "text")
        self.assertEqual(profile["productName"], "AI Prompt Kit")
        self.assertEqual(profile["pricing"], "$19")
        self.assertIn("AI operators", profile["targetAudienceAssumptions"])

    def test_browser_snapshot_normalizes_html_for_product_intake(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="browser-snapshot-html-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_path = out_dir / "product.html"
        html_path.write_text(
            """<!doctype html>
<html>
<head>
  <title>AI Prompt Kit</title>
  <meta name="description" content="Prompt templates for product copy, SEO content, and video scripts.">
  <link rel="canonical" href="https://example.com/ai-prompt-kit">
  <script type="application/ld+json">{"@type":"Product","name":"AI Prompt Kit","offers":{"price":"19"}}</script>
</head>
<body>
  <h1>AI Prompt Kit</h1>
  <p>Turn one product URL into platform-native promotion content. Start for $19.</p>
  <a href="/start">Start free</a>
  <img src="https://example.com/cover.png" alt="AI Prompt Kit cover">
</body>
</html>""",
            encoding="utf-8",
        )
        snapshot_path = out_dir / "snapshot.json"
        subprocess.run(
            [
                sys.executable,
                str(BROWSER_SNAPSHOT),
                "--html-file",
                str(html_path),
                "--base-url",
                "https://example.com/ai-prompt-kit",
                "--out-file",
                str(snapshot_path),
            ],
            check=True,
            cwd=ROOT,
        )
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["snapshotType"], "browser_rendered")
        self.assertEqual(snapshot["productName"], "AI Prompt Kit")
        self.assertIn("Start free", snapshot["ctaCandidates"])
        self.assertIn("$19", snapshot["priceCandidates"])
        subprocess.run(
            [
                sys.executable,
                str(PRODUCT_INTAKE),
                "--structured-json",
                str(snapshot_path),
                "--out-dir",
                str(out_dir / "intake"),
            ],
            check=True,
            cwd=ROOT,
        )
        profile = json.loads((out_dir / "intake/product-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["sourceType"], "browser_rendered_snapshot")
        self.assertEqual(profile["productName"], "AI Prompt Kit")
        self.assertEqual(profile["pricing"], "19")

    def test_product_url_reader_creates_structured_snapshot_then_profile(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="product-url-reader-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_path = out_dir / "product.html"
        html_path.write_text(
            """<!doctype html>
<html>
<head>
  <title>AI Prompt Kit</title>
  <meta name="description" content="Prompt templates for product copy, SEO content, and video scripts.">
  <link rel="canonical" href="https://example.com/ai-prompt-kit">
  <script type="application/ld+json">{"@type":"Product","name":"AI Prompt Kit","offers":{"price":"19"}}</script>
</head>
<body>
  <h1>AI Prompt Kit</h1>
  <p>Turn one product URL into platform-native promotion content. Start for $19.</p>
  <button>Start free</button>
</body>
</html>""",
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(PRODUCT_URL_READER),
            "--url",
            html_path.as_uri(),
            "--out-dir",
            str(out_dir / "output"),
        ]
        expect_browser_structured = playwright_chromium_available()
        if not expect_browser_structured:
            command.append("--skip-browser")
        subprocess.run(command, check=True, cwd=ROOT)
        report_path = out_dir / "output/reports/promotion-manager/intake/product-url-reader.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["requestedUrls"], 1)
        record = report["records"][0]
        self.assertTrue(Path(record["intake"]["profile"]).exists())
        self.assertEqual(record["product"]["productName"], "AI Prompt Kit")
        if expect_browser_structured:
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["summary"]["browserStructuredProfiles"], 1)
            self.assertEqual(record["sourceMode"], "browser_structured_snapshot")
            self.assertTrue(Path(record["browser"]["snapshot"]).exists())
            self.assertEqual(record["product"]["sourceType"], "browser_rendered_snapshot")
            self.assertIn("--structured-json", record["nextWorkflowCommand"])
        else:
            self.assertEqual(report["status"], "partial_ready")
            self.assertEqual(report["summary"]["staticFallbackProfiles"], 1)
            self.assertEqual(record["sourceMode"], "static_url_fallback")
            self.assertEqual(record["product"]["sourceType"], "html")
            self.assertIn("--product-url", record["nextWorkflowCommand"])
        self.assertTrue((out_dir / "output/reports/promotion-manager/intake/product-url-reader.md").exists())

    def test_agent_workflow_runs_from_structured_snapshot(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-agent-workflow-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "pricing": "$19",
                    "targetAudience": ["AI operators", "content marketers"],
                    "painPoints": ["Blank page copywriting", "Slow launch content"],
                    "text": "AI Prompt Kit helps turn a product URL into platform-native promotion content.",
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--structured-json",
                str(snapshot_path),
                "--platforms",
                "youtube,zhihu,xiaohongshu,douyin,github",
                "--skip-video",
                "--top-n",
                "3",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        manifest_path = out_dir / "output/reports/promotion-manager/agent-run/workflow-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["product"]["name"], "AI Prompt Kit")
        self.assertEqual(manifest["input"]["sourceType"], "structured_json")
        self.assertEqual(manifest["competitorDiscovery"]["status"], "ready")
        self.assertIn("youtube", manifest["competitorDiscovery"]["platforms"])
        self.assertEqual(manifest["videoGeneration"][0]["status"], "skipped")
        self.assertEqual(manifest["metricsRecovery"]["status"], "waiting_real_data")
        publish_by_platform = {item["platform"]: item for item in manifest["publishAutomation"]}
        self.assertEqual(publish_by_platform["youtube"]["automationStatus"], "dry_run_ready_requires_credentials_and_approval")
        self.assertEqual(publish_by_platform["xiaohongshu"]["automationStatus"], "copy_pack_ready_manual_publish")
        self.assertFalse(manifest["selfEvolution"]["canInstallWithoutReview"])
        self.assertTrue((out_dir / "output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json").exists())
        self.assertTrue((out_dir / "output/reports/promotion-manager/competitors/competitor-discovery.json").exists())

    def test_agent_workflow_runs_from_browser_url_when_browser_exists(self) -> None:
        if not playwright_chromium_available():
            self.skipTest("Playwright Chromium is not installed")
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-browser-workflow-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_path = out_dir / "product.html"
        html_path.write_text(
            """<!doctype html>
<html>
<head>
  <title>AI Prompt Kit</title>
  <meta name="description" content="Prompt templates for product copy, SEO content, and video scripts.">
  <script type="application/ld+json">{"@type":"Product","name":"AI Prompt Kit","offers":{"price":"19"}}</script>
</head>
<body>
  <h1>AI Prompt Kit</h1>
  <p>Turn one product URL into platform-native promotion content. Start for $19.</p>
  <button>Start free</button>
</body>
</html>""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--browser-url",
                html_path.as_uri(),
                "--platforms",
                "github",
                "--skip-video",
                "--skip-competitor-discovery",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        manifest_path = out_dir / "output/reports/promotion-manager/agent-run/workflow-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["product"]["name"], "AI Prompt Kit")
        self.assertEqual(manifest["input"]["sourceType"], "browser_rendered_snapshot")
        self.assertTrue(Path(manifest["artifacts"]["browserSnapshot"]).exists())

    def test_platform_search_capture_imports_structured_results(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="platform-search-capture-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "xiaohongshu.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "query": "AI product copy generator",
                    "items": [
                        {
                            "title": "7 prompts that turn one product page into launch content",
                            "url": "https://www.xiaohongshu.com/explore/test-note-1",
                            "creator": "Growth Notes",
                            "hook": "Stop rewriting the same product intro.",
                            "content": "Use one URL to create hooks, notes, and CTA variants. comments 87 likes 1.2k saves 420",
                            "likes": "1.2k",
                            "favorites": "420",
                            "comments": "87",
                        },
                        {
                            "title": "Product launch content checklist",
                            "url": "https://www.xiaohongshu.com/explore/test-note-2",
                            "creator": "AI Operator",
                            "content": "Before posting, verify the claim, audience, offer, and evidence. likes 800 comments 35",
                            "likes": "800",
                            "comments": "35",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PLATFORM_SEARCH_CAPTURE),
                "--structured-json",
                str(snapshot_path),
                "--platform",
                "xiaohongshu",
                "--top-n",
                "5",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "output/reports/promotion-manager/competitors/captured-search-results-xiaohongshu.json").read_text(encoding="utf-8"))
        self.assertEqual(report["platform"], "xiaohongshu")
        self.assertEqual(report["recordCount"], 2)
        self.assertEqual(report["records"][0]["visibleMetrics"]["likes"]["normalized"], 1200.0)
        self.assertEqual(report["records"][0]["contentFormat"], "note")
        self.assertEqual(report["aggregatePatterns"]["recordsWithObservedMetrics"], 2)

    def test_viral_content_library_ranks_multiplatform_capture_reports(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="viral-content-library-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        capture_dir = out_dir / "captures"
        capture_dir.mkdir()
        (capture_dir / "captured-search-results-youtube.json").write_text(
            json.dumps(
                {
                    "platform": "youtube",
                    "query": "AI product copy generator",
                    "records": [
                        {
                            "id": "search-result-001",
                            "platform": "youtube",
                            "rank": 1,
                            "normalizedRank": 1,
                            "title": "One product URL into 30 launch videos",
                            "url": "https://www.youtube.com/watch?v=abc123",
                            "creatorName": "Launch Lab",
                            "hook": "Your product page is already a content plan.",
                            "contentExcerpt": "views 120k likes 9k comments 500",
                            "visibleMetrics": {
                                "views": {"raw": "120k", "normalized": 120000.0},
                                "likes": {"raw": "9k", "normalized": 9000.0},
                                "comments": {"raw": "500", "normalized": 500.0},
                            },
                            "viralSignals": {"score": 160000.0, "hasObservedMetrics": True},
                            "reusablePatterns": ["visible_social_proof"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (capture_dir / "captured-search-results-xiaohongshu.json").write_text(
            json.dumps(
                {
                    "platform": "xiaohongshu",
                    "query": "AI product copy generator",
                    "records": [
                        {
                            "id": "search-result-001",
                            "platform": "xiaohongshu",
                            "rank": 1,
                            "normalizedRank": 1,
                            "title": "7 prompts that turn one product page into launch notes",
                            "url": "https://www.xiaohongshu.com/explore/test-note-1",
                            "creatorName": "Growth Notes",
                            "hook": "Stop rewriting the same product intro.",
                            "visibleMetrics": {"likes": {"raw": "1.2k", "normalized": 1200.0}},
                            "viralSignals": {"score": 5800.0, "hasObservedMetrics": True},
                            "reusablePatterns": ["numbered_title_or_claim"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(VIRAL_CONTENT_LIBRARY),
                "--search-capture-dir",
                str(capture_dir),
                "--top-n",
                "5",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        library = json.loads((out_dir / "output/reports/promotion-manager/competitors/viral-content-library.json").read_text(encoding="utf-8"))
        self.assertEqual(library["recordCount"], 2)
        self.assertEqual(library["materials"][0]["platform"], "youtube")
        self.assertEqual(library["materials"][0]["followUpCapture"]["mode"], "public_url_capture_candidate")
        self.assertEqual(library["materials"][1]["followUpCapture"]["mode"], "browser_assisted_capture_required")
        tasks = json.loads((out_dir / "output/reports/promotion-manager/competitors/follow-up-capture-tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(tasks["summary"]["modes"]["public_url_capture_candidate"], 1)
        self.assertEqual(tasks["summary"]["modes"]["browser_assisted_capture_required"], 1)
        self.assertIn(str(out_dir / "output"), tasks["tasks"][0]["command"])

    def test_creator_leaderboard_groups_viral_materials_by_creator(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="creator-leaderboard-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        library_path = out_dir / "viral-content-library.json"
        library_path.write_text(
            json.dumps(
                {
                    "materials": [
                        {
                            "id": "viral-material-001",
                            "libraryRank": 1,
                            "platform": "youtube",
                            "title": "One product URL into 30 launch videos",
                            "url": "https://www.youtube.com/watch?v=abc123",
                            "creatorName": "Launch Lab",
                            "hook": "Your product page is already a content plan.",
                            "visibleMetrics": {
                                "views": {"raw": "120k", "normalized": 120000.0},
                                "likes": {"raw": "9k", "normalized": 9000.0},
                                "comments": {"raw": "500", "normalized": 500.0},
                            },
                            "viralSignals": {"score": 160000.0, "hasObservedMetrics": True},
                            "reusablePatterns": ["visible_social_proof"],
                            "followUpCapture": {"mode": "public_url_capture_candidate", "status": "ready"},
                        },
                        {
                            "id": "viral-material-002",
                            "libraryRank": 2,
                            "platform": "youtube",
                            "title": "Product copy system teardown",
                            "url": "https://www.youtube.com/watch?v=def456",
                            "creatorName": "Launch Lab",
                            "hook": "Stop writing launch copy from scratch.",
                            "visibleMetrics": {"views": {"raw": "80k", "normalized": 80000.0}},
                            "viralSignals": {"score": 85000.0, "hasObservedMetrics": True},
                            "reusablePatterns": ["explicit_call_to_action"],
                            "followUpCapture": {"mode": "public_url_capture_candidate", "status": "ready"},
                        },
                        {
                            "id": "viral-material-003",
                            "libraryRank": 3,
                            "platform": "xiaohongshu",
                            "title": "7 prompts that turn one product page into launch notes",
                            "url": "https://www.xiaohongshu.com/explore/test-note-1",
                            "creatorName": "Growth Notes",
                            "hook": "Stop rewriting the same product intro.",
                            "visibleMetrics": {"likes": {"raw": "1.2k", "normalized": 1200.0}},
                            "viralSignals": {"score": 5800.0, "hasObservedMetrics": True},
                            "reusablePatterns": ["numbered_title_or_claim"],
                            "followUpCapture": {"mode": "browser_assisted_capture_required", "status": "queued"},
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(CREATOR_LEADERBOARD),
                "--viral-library",
                str(library_path),
                "--top-n",
                "10",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        leaderboard = json.loads((out_dir / "output/reports/promotion-manager/competitors/creator-leaderboard.json").read_text(encoding="utf-8"))
        self.assertEqual(leaderboard["creatorCount"], 2)
        self.assertEqual(leaderboard["creators"][0]["creatorName"], "Launch Lab")
        self.assertEqual(leaderboard["creators"][0]["materialCount"], 2)
        self.assertEqual(leaderboard["creators"][0]["metricTotals"]["views"], 200000.0)
        self.assertEqual(leaderboard["creators"][0]["trackingMode"], "public_or_official_research_candidate")
        self.assertEqual(leaderboard["creators"][1]["trackingMode"], "browser_assisted_or_user_export_required")
        tasks = json.loads((out_dir / "output/reports/promotion-manager/competitors/creator-follow-up-tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(tasks["taskCount"], 2)
        self.assertIn("Launch Lab", tasks["tasks"][0]["creatorName"])
        self.assertIn("official/public profile", tasks["tasks"][0]["requiredEvidence"][0])

    def test_creator_follow_up_runner_plans_public_and_queues_manual_tasks(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="creator-follow-up-runner-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        tasks_path = out_dir / "creator-follow-up-tasks.json"
        tasks_path.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "creator-follow-up-001",
                            "creatorId": "creator-001",
                            "priority": 1,
                            "creatorName": "Launch Lab",
                            "platform": "youtube",
                            "trackingMode": "public_or_official_research_candidate",
                            "status": "ready",
                            "sampleUrls": ["https://www.youtube.com/watch?v=abc123"],
                            "requiredEvidence": ["official/public profile or channel URL"],
                        },
                        {
                            "id": "creator-follow-up-002",
                            "creatorId": "creator-002",
                            "priority": 2,
                            "creatorName": "Growth Notes",
                            "platform": "xiaohongshu",
                            "trackingMode": "browser_assisted_or_user_export_required",
                            "status": "queued_browser_assisted",
                            "sampleUrls": ["https://www.xiaohongshu.com/explore/test-note-1"],
                            "requiredEvidence": ["browser-visible creator profile or user export"],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(CREATOR_FOLLOW_UP_RUNNER),
                "--tasks-json",
                str(tasks_path),
                "--dry-run",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        result_path = out_dir / "output/reports/promotion-manager/competitors/creator-follow-up-results.json"
        report = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["statuses"]["dry_run"], 1)
        self.assertEqual(report["summary"]["statuses"]["queued_manual_evidence"], 1)
        self.assertIn("--platform", report["results"][0]["command"])
        evidence_path = Path(report["results"][1]["evidenceRequest"])
        self.assertTrue(evidence_path.exists())
        library = json.loads((out_dir / "output/reports/promotion-manager/competitors/creator-deep-library.json").read_text(encoding="utf-8"))
        self.assertEqual(library["recordCount"], 0)

    def test_follow_up_capture_runner_executes_public_and_queues_manual_tasks(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="follow-up-capture-runner-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        site_dir = out_dir / "site"
        site_dir.mkdir()
        (site_dir / "competitor.html").write_text(
            """<!doctype html>
<html>
<head>
  <title>Launch workflow repo</title>
  <meta name="description" content="Turn one product URL into a repeatable launch content workflow.">
</head>
<body>
  <h1>Launch workflow repo</h1>
  <p>Hook: your product page is already a campaign brief.</p>
  <p>Use it to generate titles, scripts, and GitHub launch copy. stars 42 forks 7</p>
</body>
</html>""",
            encoding="utf-8",
        )

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

        handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(site_dir), **kwargs)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def stop_server() -> None:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.addCleanup(stop_server)
        url = f"http://127.0.0.1:{server.server_address[1]}/competitor.html"

        tasks_path = out_dir / "follow-up-capture-tasks.json"
        tasks_path.write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "follow-up-001",
                            "materialId": "viral-material-001",
                            "priority": 1,
                            "platform": "github",
                            "title": "Launch workflow repo",
                            "url": url,
                            "mode": "public_url_capture_candidate",
                            "status": "ready",
                            "requiredEvidence": ["public URL content"],
                        },
                        {
                            "id": "follow-up-002",
                            "materialId": "viral-material-002",
                            "priority": 2,
                            "platform": "xiaohongshu",
                            "title": "Launch note teardown",
                            "url": "https://www.xiaohongshu.com/explore/test-note-1",
                            "mode": "browser_assisted_capture_required",
                            "status": "queued",
                            "requiredEvidence": ["browser-visible page text"],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(FOLLOW_UP_CAPTURE_RUNNER),
                "--tasks-json",
                str(tasks_path),
                "--out-dir",
                str(out_dir / "output"),
                "--allow-localhost",
            ],
            check=True,
            cwd=ROOT,
        )
        results = json.loads((out_dir / "output/reports/promotion-manager/competitors/follow-up-capture-results.json").read_text(encoding="utf-8"))
        self.assertEqual(results["summary"]["statuses"]["ready"], 1)
        self.assertEqual(results["summary"]["statuses"]["queued_manual_evidence"], 1)
        deep = json.loads((out_dir / "output/reports/promotion-manager/competitors/deep-competitor-library.json").read_text(encoding="utf-8"))
        self.assertEqual(deep["recordCount"], 1)
        self.assertEqual(deep["records"][0]["platform"], "github")
        self.assertEqual(deep["records"][0]["sourceFollowUpTask"]["materialId"], "viral-material-001")
        self.assertTrue((out_dir / "output/reports/promotion-manager/competitors/follow-up-captures/manual-evidence/follow-up-002.md").exists())

    def test_competitor_content_enhancer_writes_back_content_and_publish_pack(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="competitor-content-enhancer-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        content_path = out_dir / "ai-prompt-kit-platform-content.json"
        content_path.write_text(
            json.dumps(
                {
                    "youtube": {
                        "platform": "youtube",
                        "title": "AI Prompt Kit launch",
                        "description": "Base YouTube description.",
                        "shortVideoScript": "Base script.",
                        "voiceover": "Base voiceover.",
                        "storyboard": [],
                        "formats": {"videoScripts": ["Base script."]},
                        "sourceProduct": {"name": "AI Prompt Kit", "url": "https://example.com/ai-prompt-kit"},
                        "cta": "Try AI Prompt Kit",
                    },
                    "github": {
                        "platform": "github",
                        "title": "AI Prompt Kit repo launch",
                        "description": "Base GitHub description.",
                        "formats": {},
                        "sourceProduct": {"name": "AI Prompt Kit", "url": "https://example.com/ai-prompt-kit"},
                    },
                    "xiaohongshu": {
                        "platform": "xiaohongshu",
                        "title": "AI Prompt Kit note",
                        "description": "Base note.",
                        "formats": {},
                        "sourceProduct": {"name": "AI Prompt Kit", "url": "https://example.com/ai-prompt-kit"},
                    },
                    "douyin": {
                        "platform": "douyin",
                        "title": "AI Prompt Kit short video",
                        "description": "Base short video.",
                        "shortVideoScript": "Base short script.",
                        "voiceover": "Base voiceover.",
                        "storyboard": [],
                        "formats": {},
                        "sourceProduct": {"name": "AI Prompt Kit", "url": "https://example.com/ai-prompt-kit"},
                    },
                }
            ),
            encoding="utf-8",
        )
        viral_path = out_dir / "viral-content-library.json"
        viral_path.write_text(
            json.dumps(
                {
                    "materials": [
                        {
                            "platform": "youtube",
                            "title": "One product URL into 30 launch videos",
                            "url": "https://www.youtube.com/watch?v=abc123",
                            "creatorName": "Launch Lab",
                            "hook": "Your product page is already a content plan.",
                            "reusablePatterns": ["numbered_title_or_claim", "visible_social_proof"],
                            "viralSignals": {"score": 160000.0},
                            "visibleMetrics": {"views": {"raw": "120k", "normalized": 120000.0}},
                        },
                        {
                            "platform": "github",
                            "title": "Launch workflow repo",
                            "url": "https://github.com/example/launch-workflow",
                            "hook": "Stop writing launch copy from scratch.",
                            "reusablePatterns": ["explicit_call_to_action"],
                            "viralSignals": {"score": 4200.0},
                        },
                        {
                            "platform": "xiaohongshu",
                            "title": "7 prompts that turn one product page into launch notes",
                            "url": "https://www.xiaohongshu.com/explore/test-note-1",
                            "hook": "Stop rewriting the same product intro.",
                            "reusablePatterns": ["numbered_title_or_claim"],
                            "viralSignals": {"score": 5800.0},
                        },
                        {
                            "platform": "douyin",
                            "title": "One URL into 10 short videos",
                            "url": "https://www.douyin.com/video/123",
                            "hook": "Your product page is already a script.",
                            "reusablePatterns": ["visible_social_proof"],
                            "viralSignals": {"score": 9600.0},
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        publish_pack_path = out_dir / "ai-prompt-kit-publish-pack.json"
        publish_pack_path.write_text(
            json.dumps(
                [
                    {"platform": "youtube", "content": {"title": "Old title"}},
                    {"platform": "github", "content": {"title": "Old repo title"}},
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(COMPETITOR_CONTENT_ENHANCER),
                "--content-json",
                str(content_path),
                "--viral-library",
                str(viral_path),
                "--publish-pack",
                str(publish_pack_path),
                "--write-back",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        enhanced = json.loads(content_path.read_text(encoding="utf-8"))
        self.assertEqual(enhanced["youtube"]["competitorInformed"]["status"], "ready")
        self.assertIn("Your product page is already a content plan", enhanced["youtube"]["shortVideoScript"])
        self.assertIn("Observed viral pattern", enhanced["xiaohongshu"]["description"])
        self.assertIn("Observed viral pattern", enhanced["douyin"]["voiceover"])
        self.assertTrue((out_dir / "ai-prompt-kit-platform-content.base.json").exists())
        self.assertTrue((out_dir / "output/reports/promotion-manager/generated-content/ai-prompt-kit-competitor-informed-content.json").exists())
        publish_pack = json.loads(publish_pack_path.read_text(encoding="utf-8"))
        self.assertEqual(publish_pack[0]["content"]["competitorInformed"]["status"], "ready")
        self.assertIn("AI Prompt Kit", publish_pack[1]["content"]["formats"]["readmePromotion"])

    def test_agent_workflow_uses_competitor_informed_content_before_video_and_publish(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-competitor-informed-workflow-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        product_path = out_dir / "product.json"
        product_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        snapshot_dir = out_dir / "search"
        snapshot_dir.mkdir()
        (snapshot_dir / "youtube.json").write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "title": "One product URL into 30 launch videos",
                            "url": "https://www.youtube.com/watch?v=abc123",
                            "creatorName": "Launch Lab",
                            "hook": "Your product page is already a content plan.",
                            "content": "views 120k likes 9k comments 500",
                            "views": "120k",
                            "likes": "9k",
                            "comments": "500",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--structured-json",
                str(product_path),
                "--platforms",
                "youtube",
                "--search-snapshot-dir",
                str(snapshot_dir),
                "--use-competitor-informed-content",
                "--skip-video",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        manifest = json.loads((out_dir / "output/reports/promotion-manager/agent-run/workflow-manifest.json").read_text(encoding="utf-8"))
        enhancer_run = manifest["competitorDiscovery"]["competitorInformedContent"]
        self.assertEqual(enhancer_run["status"], "ready")
        self.assertTrue(Path(manifest["artifacts"]["competitorInformedContent"]).exists())
        content = json.loads(Path(manifest["artifacts"]["contentJson"]).read_text(encoding="utf-8"))
        self.assertEqual(content["youtube"]["competitorInformed"]["status"], "ready")
        self.assertIn("Your product page is already a content plan", content["youtube"]["shortVideoScript"])

    def test_platform_search_browser_generates_snapshots_from_saved_html(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="platform-search-browser-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_dir = out_dir / "html"
        html_dir.mkdir()
        (html_dir / "youtube.html").write_text(
            """<!doctype html>
<html>
<head><title>YouTube search</title></head>
<body>
  <section>
    <a href="https://www.youtube.com/watch?v=abc123">One URL into 30 launch videos</a>
    <p>Launch Lab shows a product URL workflow. views 120k likes 9k comments 500</p>
  </section>
  <section>
    <a href="https://www.youtube.com/watch?v=def456">Product copy system teardown</a>
    <p>Breaks title, hook, proof, and CTA. views 80k likes 5k comments 240</p>
  </section>
</body>
</html>""",
            encoding="utf-8",
        )
        snapshot_dir = out_dir / "snapshots"
        subprocess.run(
            [
                sys.executable,
                str(PLATFORM_SEARCH_BROWSER),
                "--query",
                "AI product copy generator",
                "--platforms",
                "youtube",
                "--html-snapshot-dir",
                str(html_dir),
                "--snapshot-dir",
                str(snapshot_dir),
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        snapshot = json.loads((snapshot_dir / "youtube.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["platform"], "youtube")
        self.assertEqual(snapshot["captureMode"], "saved_html_snapshot")
        self.assertEqual(len(snapshot["items"]), 2)
        self.assertIn("One URL", snapshot["items"][0]["title"])
        summary = json.loads((out_dir / "output/reports/promotion-manager/competitors/browser-search-snapshots.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["records"][0]["status"], "ready")

    def test_agent_workflow_auto_searches_competitors_from_saved_html(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-auto-search-workflow-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        product_path = out_dir / "product.json"
        product_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        html_dir = out_dir / "html"
        html_dir.mkdir()
        (html_dir / "youtube.html").write_text(
            """<!doctype html>
<html><body>
  <article>
    <a href="https://www.youtube.com/watch?v=abc123">One URL into 30 launch videos</a>
    <p>Hook: your product page is already a content plan. views 120k likes 9k comments 500</p>
  </article>
</body></html>""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--structured-json",
                str(product_path),
                "--platforms",
                "youtube",
                "--auto-search-competitors",
                "--search-html-snapshot-dir",
                str(html_dir),
                "--skip-video",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        manifest = json.loads((out_dir / "output/reports/promotion-manager/agent-run/workflow-manifest.json").read_text(encoding="utf-8"))
        browser_search = manifest["competitorDiscovery"]["browserSearchSnapshots"]
        self.assertEqual(browser_search["status"], "ready")
        self.assertEqual(browser_search["records"][0]["recordCount"], 1)
        captures = manifest["competitorDiscovery"]["searchCaptures"]
        self.assertEqual(captures[0]["status"], "ready")
        self.assertEqual(captures[0]["recordCount"], 1)
        self.assertTrue((out_dir / "output/reports/promotion-manager/competitors/captured-search-results-youtube.json").exists())

    def test_agent_workflow_captures_search_snapshot_directory(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-search-snapshot-workflow-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        product_path = out_dir / "product.json"
        product_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        snapshot_dir = out_dir / "search"
        snapshot_dir.mkdir()
        (snapshot_dir / "douyin.json").write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "title": "One URL into 10 short videos",
                            "url": "https://www.douyin.com/video/123",
                            "creatorName": "Launch Lab",
                            "content": "Hook: your product page is already a script. views 120k likes 9k comments 500",
                            "views": "120k",
                            "likes": "9k",
                            "comments": "500",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--structured-json",
                str(product_path),
                "--platforms",
                "douyin",
                "--search-snapshot-dir",
                str(snapshot_dir),
                "--run-creator-follow-up",
                "--creator-follow-up-dry-run",
                "--run-follow-up-captures",
                "--skip-video",
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        manifest = json.loads((out_dir / "output/reports/promotion-manager/agent-run/workflow-manifest.json").read_text(encoding="utf-8"))
        captures = manifest["competitorDiscovery"]["searchCaptures"]
        self.assertEqual(captures[0]["platform"], "douyin")
        self.assertEqual(captures[0]["status"], "ready")
        self.assertEqual(captures[0]["recordCount"], 1)
        report_path = out_dir / "output/reports/promotion-manager/competitors/captured-search-results-douyin.json"
        self.assertTrue(report_path.exists())
        viral_library = manifest["competitorDiscovery"]["viralContentLibrary"]
        self.assertEqual(viral_library["status"], "ready")
        self.assertEqual(viral_library["recordCount"], 1)
        self.assertTrue(Path(viral_library["library"]).exists())
        creator_leaderboard = manifest["competitorDiscovery"]["creatorLeaderboard"]
        self.assertEqual(creator_leaderboard["status"], "ready")
        self.assertEqual(creator_leaderboard["creatorCount"], 1)
        self.assertTrue(Path(manifest["artifacts"]["creatorLeaderboard"]).exists())
        creator_follow_up = manifest["competitorDiscovery"]["creatorFollowUpRun"]
        self.assertEqual(creator_follow_up["status"], "ready")
        self.assertEqual(creator_follow_up["deepRecordCount"], 0)
        self.assertEqual(creator_follow_up["resultSummary"]["statuses"]["queued_manual_evidence"], 1)
        self.assertTrue(Path(manifest["artifacts"]["creatorFollowUpResults"]).exists())
        library = json.loads(Path(viral_library["library"]).read_text(encoding="utf-8"))
        self.assertEqual(library["materials"][0]["platform"], "douyin")
        self.assertEqual(library["materials"][0]["followUpCapture"]["mode"], "browser_assisted_capture_required")
        follow_up = manifest["competitorDiscovery"]["followUpCaptureRun"]
        self.assertEqual(follow_up["status"], "ready")
        self.assertEqual(follow_up["deepRecordCount"], 0)
        self.assertEqual(follow_up["resultSummary"]["statuses"]["queued_manual_evidence"], 1)
        self.assertTrue(Path(follow_up["results"]).exists())

    def test_automation_scheduler_runs_due_workflow_job(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-automation-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "pricing": "$19",
                    "targetAudience": ["AI operators", "content marketers"],
                    "painPoints": ["Blank page copywriting", "Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        config_path = out_dir / "automation.json"
        config_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "defaultOutputRoot": "./automation-output",
                    "jobs": [
                        {
                            "id": "ai-prompt-kit-weekly",
                            "enabled": True,
                            "schedule": {"intervalDays": 7},
                            "input": {"structuredJson": "snapshot.json"},
                            "platforms": ["youtube", "douyin", "github"],
                            "topN": 2,
                            "skipVideo": True,
                            "publish": {"enabled": False, "mode": "approval_required"},
                        }
                    ],
                    "guardrails": ["No automatic publishing without approval."],
                }
            ),
            encoding="utf-8",
        )
        state_path = out_dir / "state.json"
        subprocess.run(
            [
                sys.executable,
                str(AUTOMATION_SCHEDULER),
                "run",
                "--config",
                str(config_path),
                "--state-file",
                str(state_path),
                "--now",
                "2026-07-07T00:00:00+00:00",
            ],
            check=True,
            cwd=ROOT,
        )
        state = json.loads(state_path.read_text(encoding="utf-8"))
        job_state = state["jobs"]["ai-prompt-kit-weekly"]
        self.assertEqual(job_state["lastStatus"], "ready")
        manifest_path = Path(job_state["lastManifest"])
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["product"]["name"], "AI Prompt Kit")
        self.assertEqual(manifest["videoGeneration"][0]["status"], "skipped")
        run_report = json.loads((out_dir / "automation-output/scheduler/automation-run.json").read_text(encoding="utf-8"))
        self.assertEqual(run_report["records"][0]["status"], "ready")
        self.assertFalse(run_report["records"][0]["publish"]["enabled"])

    def test_automation_scheduler_can_run_publish_queue_after_workflow(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-automation-publish-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        business_csv = out_dir / "business.csv"
        business_csv.write_text(
            "\n".join(
                [
                    "platform,publishedUrl,title,clicks,orders,revenue,evidence",
                    "xiaohongshu,https://www.xiaohongshu.com/explore/note123,Launch Note,90,2,$88.00,xhs-export.csv",
                ]
            ),
            encoding="utf-8",
        )
        config_path = out_dir / "automation.json"
        config_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "defaultOutputRoot": "./automation-output",
                    "jobs": [
                        {
                            "id": "ai-prompt-kit-publish-weekly",
                            "enabled": True,
                            "schedule": {"intervalDays": 7},
                            "input": {"structuredJson": "snapshot.json"},
                            "platforms": ["github", "xiaohongshu"],
                            "topN": 2,
                            "skipVideo": True,
                            "publish": {
                                "enabled": True,
                                "platforms": ["github", "xiaohongshu"],
                                "github": {
                                    "repo": "hqwzhu/Viral-Product-Copy-Video-Generator",
                                    "action": "file",
                                    "path": "PROMOTION.md",
                                },
                            },
                            "metricsRecovery": {
                                "enabled": True,
                                "businessCsv": "business.csv",
                            },
                        }
                    ],
                    "guardrails": ["No automatic publishing without approval."],
                }
            ),
            encoding="utf-8",
        )
        state_path = out_dir / "state.json"
        subprocess.run(
            [
                sys.executable,
                str(AUTOMATION_SCHEDULER),
                "run",
                "--config",
                str(config_path),
                "--state-file",
                str(state_path),
                "--now",
                "2026-07-07T00:00:00+00:00",
            ],
            check=True,
            cwd=ROOT,
        )
        state = json.loads(state_path.read_text(encoding="utf-8"))
        job_state = state["jobs"]["ai-prompt-kit-publish-weekly"]
        self.assertEqual(job_state["lastStatus"], "ready")
        self.assertTrue(Path(job_state["lastPublishQueue"]).exists())
        run_report = json.loads((out_dir / "automation-output/scheduler/automation-run.json").read_text(encoding="utf-8"))
        publish_queue = run_report["records"][0]["publishQueue"]
        self.assertEqual(publish_queue["status"], "ready")
        self.assertEqual(publish_queue["summary"]["officialDryRuns"], 1)
        self.assertEqual(publish_queue["summary"]["manualQueued"], 1)
        self.assertTrue(Path(job_state["lastMetricsRecovery"]).exists())
        recovery = run_report["records"][0]["metricsRecovery"]
        self.assertEqual(recovery["status"], "ready")
        self.assertEqual(recovery["summary"]["recordsWithMetrics"], 1)

    def test_automation_scheduler_passes_competitor_informed_content_flags(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-automation-enhancer-flags-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                }
            ),
            encoding="utf-8",
        )
        config_path = out_dir / "automation.json"
        config_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "defaultOutputRoot": "./automation-output",
                    "jobs": [
                        {
                            "id": "enhancer-enabled",
                            "enabled": True,
                            "schedule": {"intervalDays": 7},
                            "input": {"structuredJson": "snapshot.json"},
                            "platforms": ["youtube"],
                            "skipCreatorLeaderboard": True,
                            "creatorFollowUp": {"enabled": True, "limit": 7, "topN": 3, "dryRun": True},
                            "competitorInformedContent": {"enabled": True},
                            "skipVideo": True,
                        },
                        {
                            "id": "enhancer-disabled",
                            "enabled": True,
                            "schedule": {"intervalDays": 7},
                            "input": {"structuredJson": "snapshot.json"},
                            "platforms": ["youtube"],
                            "competitorInformedContent": {"enabled": False},
                            "skipVideo": True,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(AUTOMATION_SCHEDULER),
                "run",
                "--config",
                str(config_path),
                "--now",
                "2026-07-07T00:00:00+00:00",
                "--dry-run",
            ],
            check=True,
            cwd=ROOT,
        )
        run_report = json.loads((out_dir / "automation-output/scheduler/automation-run.json").read_text(encoding="utf-8"))
        commands = {record["jobId"]: record["command"] for record in run_report["records"]}
        self.assertIn("--skip-creator-leaderboard", commands["enhancer-enabled"])
        self.assertIn("--run-creator-follow-up", commands["enhancer-enabled"])
        self.assertIn("--creator-follow-up-limit", commands["enhancer-enabled"])
        self.assertIn("7", commands["enhancer-enabled"])
        self.assertIn("--creator-follow-up-top-n", commands["enhancer-enabled"])
        self.assertIn("3", commands["enhancer-enabled"])
        self.assertIn("--creator-follow-up-dry-run", commands["enhancer-enabled"])
        self.assertIn("--use-competitor-informed-content", commands["enhancer-enabled"])
        self.assertIn("--skip-competitor-informed-content", commands["enhancer-disabled"])

    def test_automation_scheduler_writes_windows_task_script(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-windows-task-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        config_path = out_dir / "automation.json"
        config_path.write_text(json.dumps({"version": 1, "jobs": []}), encoding="utf-8")
        script_path = out_dir / "register-task.ps1"
        subprocess.run(
            [
                sys.executable,
                str(AUTOMATION_SCHEDULER),
                "windows-task",
                "--config",
                str(config_path),
                "--out-file",
                str(script_path),
                "--task-name",
                "ENHE Promotion Manager Test",
                "--time",
                "09:30",
            ],
            check=True,
            cwd=ROOT,
        )
        script = script_path.read_text(encoding="utf-8")
        self.assertIn("Register-ScheduledTask", script)
        self.assertIn("automation_scheduler.py", script)
        self.assertIn("ENHE Promotion Manager Test", script)

    def test_competitor_intake_imports_html_evidence(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="competitor-intake-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_path = out_dir / "competitor.html"
        html_path.write_text(
            """<!doctype html>
<html>
<head>
  <title>One URL Into 30 Posts</title>
  <meta property="og:title" content="One URL Into 30 Posts">
  <meta property="og:description" content="A creator breaks down a product URL into platform-native posts.">
  <meta property="og:site_name" content="Growth Creator">
</head>
<body>
  <h1>One URL Into 30 Posts</h1>
  <p>Hook: Stop writing from a blank page. Turn one product URL into a week of content.</p>
  <p>12K views 1.2K likes 87 comments. Visit the template link to try it.</p>
</body>
</html>""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(COMPETITOR_INTAKE),
                "--html-file",
                str(html_path),
                "--platform",
                "youtube",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/competitors/imported-competitors.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["records"][0]["platform"], "youtube")
        self.assertEqual(report["records"][0]["title"], "One URL Into 30 Posts")
        self.assertEqual(report["records"][0]["creatorName"], "Growth Creator")
        self.assertEqual(report["records"][0]["visibleMetrics"]["views"]["normalized"], 12000.0)
        self.assertEqual(report["aggregatePatterns"]["recordsWithObservedMetrics"], 1)
        self.assertTrue((out_dir / "reports/promotion-manager/competitors/imported-competitors.md").exists())

    def test_competitor_discovery_generates_platform_tasks(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="competitor-discovery-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        subprocess.run(
            [
                sys.executable,
                str(COMPETITOR_DISCOVERY),
                "--query",
                "AI product copy generator",
                "--platforms",
                "youtube,zhihu,xiaohongshu,douyin,github",
                "--top-n",
                "5",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/competitors/competitor-discovery.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        tasks = {item["platform"]: item for item in report["tasks"]}
        self.assertIn("youtube.com/results", tasks["youtube"]["searchUrl"])
        self.assertIn("github.com/search", tasks["github"]["searchUrl"])
        self.assertTrue(tasks["github"]["canRunFullyAutomatedNow"])
        self.assertFalse(tasks["xiaohongshu"]["canRunFullyAutomatedNow"])
        self.assertEqual(report["liveResults"], {})
        self.assertTrue((out_dir / "reports/promotion-manager/competitors/competitor-discovery.md").exists())

    def test_competitor_collector_imports_youtube_official_fixtures(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="competitor-collector-youtube-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        search_path = out_dir / "youtube-search.json"
        videos_path = out_dir / "youtube-videos.json"
        channels_path = out_dir / "youtube-channels.json"
        search_path.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "id": {"videoId": "vid123"},
                            "snippet": {
                                "title": "One URL Into 30 Posts",
                                "channelId": "chan123",
                                "channelTitle": "Growth Creator",
                                "description": "Turn one product URL into a week of content.",
                                "publishedAt": "2026-01-01T00:00:00Z",
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        videos_path.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "id": "vid123",
                            "snippet": {
                                "title": "One URL Into 30 Posts",
                                "channelId": "chan123",
                                "channelTitle": "Growth Creator",
                                "description": "Turn one product URL into a week of content.",
                                "publishedAt": "2026-01-01T00:00:00Z",
                            },
                            "statistics": {"viewCount": "12000", "likeCount": "1200", "commentCount": "87"},
                            "contentDetails": {"duration": "PT30S"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        channels_path.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "id": "chan123",
                            "snippet": {"title": "Growth Creator"},
                            "statistics": {"subscriberCount": "5000", "viewCount": "90000", "videoCount": "42"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(COMPETITOR_COLLECTOR),
                "--platform",
                "youtube",
                "--query",
                "product copy generator",
                "--youtube-search-json",
                str(search_path),
                "--youtube-videos-json",
                str(videos_path),
                "--youtube-channels-json",
                str(channels_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/competitors/auto-collected-competitors.json").read_text(encoding="utf-8"))
        record = report["records"][0]
        self.assertEqual(record["platform"], "youtube")
        self.assertEqual(record["creatorName"], "Growth Creator")
        self.assertEqual(record["visibleMetrics"]["views"]["normalized"], 12000.0)
        self.assertEqual(record["visibleMetrics"]["channelSubscribers"]["normalized"], 5000.0)
        self.assertEqual(report["connectorStatus"][0]["status"], "ready")

    def test_competitor_collector_imports_github_public_fixtures(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="competitor-collector-github-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        search_path = out_dir / "github-search.json"
        search_path.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "full_name": "example/product-copy-generator",
                            "name": "product-copy-generator",
                            "html_url": "https://github.com/example/product-copy-generator",
                            "description": "Generate product copy from one URL.",
                            "owner": {"login": "example"},
                            "stargazers_count": 3400,
                            "forks_count": 210,
                            "watchers_count": 3400,
                            "open_issues_count": 12,
                            "language": "Python",
                            "created_at": "2025-01-01T00:00:00Z",
                            "updated_at": "2026-01-01T00:00:00Z",
                            "topics": ["ai", "copywriting"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(COMPETITOR_COLLECTOR),
                "--platform",
                "github",
                "--query",
                "product copy generator",
                "--github-search-json",
                str(search_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/competitors/auto-collected-competitors.json").read_text(encoding="utf-8"))
        record = report["records"][0]
        self.assertEqual(record["platform"], "github")
        self.assertEqual(record["creatorName"], "example")
        self.assertEqual(record["visibleMetrics"]["stars"]["normalized"], 3400.0)
        self.assertEqual(record["language"], "Python")
        self.assertEqual(report["connectorStatus"][0]["source"], "GitHub Search REST API")

    def test_metrics_intake_imports_real_csv_metrics(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="metrics-intake-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        csv_path = out_dir / "metrics.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "platform,publishedUrl,title,views,likes,comments,shares,clicks,leads,orders,revenue,evidence",
                    "youtube,https://www.youtube.com/watch?v=abc123,Launch Video,12K,1.2K,87,33,240,28,6,$420.50,https://studio.youtube.com/export.csv",
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(METRICS_INTAKE),
                "--csv-file",
                str(csv_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/metrics/imported-metrics.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        record = report["records"][0]
        self.assertEqual(record["metrics"]["views"]["normalized"], 12000.0)
        self.assertEqual(record["metrics"]["revenue"]["normalized"], 420.5)
        self.assertGreater(record["derived"]["engagementRate"], 0)
        self.assertEqual(report["aggregates"]["totals"]["orders"], 6.0)
        self.assertEqual(report["retrospective"]["status"], "ready")
        self.assertTrue((out_dir / "reports/promotion-manager/metrics/imported-metrics.md").exists())

    def test_metrics_intake_imports_structured_browser_snapshot_metrics(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="metrics-structured-intake-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "published-metrics-snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://www.xiaohongshu.com/explore/note123",
                    "title": "AI Prompt Kit launch note analytics",
                    "text": "浏览量: 3,000 点赞: 380 评论: 42 收藏: 55 订单: 2 收入: $88.00",
                    "screenshot": "xhs-analytics.png",
                    "capturedAt": "2026-07-08T09:00:00+08:00",
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(METRICS_INTAKE),
                "--structured-json",
                str(snapshot_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/metrics/imported-metrics.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        record = report["records"][0]
        self.assertEqual(report["inputMode"], "structured_json")
        self.assertEqual(record["platform"], "xiaohongshu")
        self.assertEqual(record["publishedUrl"], "https://www.xiaohongshu.com/explore/note123")
        self.assertEqual(record["metrics"]["views"]["normalized"], 3000.0)
        self.assertEqual(record["metrics"]["likes"]["normalized"], 380.0)
        self.assertEqual(record["metrics"]["comments"]["normalized"], 42.0)
        self.assertEqual(record["metrics"]["orders"]["normalized"], 2.0)
        self.assertEqual(record["metrics"]["revenue"]["normalized"], 88.0)
        self.assertIn("xhs-analytics.png", record["evidence"])

    def test_metrics_recovery_merges_published_items_and_business_exports(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="metrics-recovery-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        published_items = out_dir / "published-items.json"
        published_items.write_text(
            json.dumps(
                [
                    {
                        "platform": "youtube",
                        "publishedUrl": "https://www.youtube.com/watch?v=abc123",
                        "title": "Launch Video",
                    },
                    {
                        "platform": "xiaohongshu",
                        "publishedUrl": "https://www.xiaohongshu.com/explore/note123",
                        "title": "Launch Note",
                    },
                ]
            ),
            encoding="utf-8",
        )
        business_csv = out_dir / "business.csv"
        business_csv.write_text(
            "\n".join(
                [
                    "platform,publishedUrl,title,views,likes,comments,clicks,orders,revenue,evidence",
                    "youtube,https://www.youtube.com/watch?v=abc123,Launch Video,12000,1200,87,240,6,$420.50,shop-export.csv",
                    "xiaohongshu,https://www.xiaohongshu.com/explore/note123,Launch Note,3000,380,44,90,2,$88.00,xhs-export.csv",
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(METRICS_RECOVERY),
                "--published-items-json",
                str(published_items),
                "--business-csv",
                str(business_csv),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/metrics-recovery/metrics-recovery.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["recoveryStatus"], "ready")
        self.assertEqual(report["aggregates"]["totals"]["orders"], 8.0)
        self.assertEqual(report["aggregates"]["totals"]["revenue"], 508.5)
        self.assertEqual(report["coverage"]["recordsWithMetrics"], 2)
        statuses = {(item["platform"], item["status"]) for item in report["connectorStatus"]}
        self.assertIn(("youtube", "requires_env_var"), statuses)
        self.assertIn(("xiaohongshu", "manual_export_required"), statuses)
        self.assertTrue((out_dir / "reports/promotion-manager/metrics-recovery/metrics-recovery.md").exists())
        serialized = json.dumps(report)
        self.assertNotIn("YOUTUBE_OAUTH_ACCESS_TOKEN", serialized)
        self.assertNotIn("GITHUB_TOKEN", serialized)

    def test_metrics_recovery_imports_structured_metrics_snapshot(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="metrics-recovery-structured-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        published_dir = out_dir / "reports/promotion-manager/published-items"
        published_dir.mkdir(parents=True)
        (published_dir / "published-items.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "platform": "xiaohongshu",
                            "publishedUrl": "https://www.xiaohongshu.com/explore/note123",
                            "title": "AI Prompt Kit launch note analytics",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        snapshot_path = out_dir / "published-metrics-snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://www.xiaohongshu.com/explore/note123",
                    "title": "AI Prompt Kit launch note analytics",
                    "text": "views: 3,000 likes: 380 comments: 42 orders: 2 revenue: $88.00",
                    "screenshot": "xhs-analytics.png",
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(METRICS_RECOVERY),
                "--metrics-structured-json",
                str(snapshot_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/metrics-recovery/metrics-recovery.json").read_text(encoding="utf-8"))
        self.assertEqual(report["recoveryStatus"], "ready")
        self.assertEqual(report["coverage"]["publishedItemsDiscovered"], 1)
        self.assertEqual(report["coverage"]["recordsWithMetrics"], 1)
        self.assertEqual(report["coverage"]["manualOrPendingRequirements"], 0)
        self.assertEqual(report["aggregates"]["totals"]["orders"], 2.0)
        self.assertEqual(report["aggregates"]["totals"]["revenue"], 88.0)

    def test_metrics_recovery_marks_publish_queue_items_pending(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="metrics-recovery-pending-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        queue_dir = out_dir / "reports/promotion-manager/publish-queue"
        queue_dir.mkdir(parents=True)
        queue_path = queue_dir / "publish-queue.json"
        queue_path.write_text(
            json.dumps(
                {
                    "records": [
                        {"platform": "github", "status": "dry_run", "publishMode": "official_api_publish", "contentDraft": ""},
                        {"platform": "xiaohongshu", "status": "queued_manual", "publishMode": "manual_publish_required", "contentDraft": ""},
                        {"platform": "douyin", "status": "queued_browser_assisted", "publishMode": "browser_assisted_publish", "contentDraft": ""},
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(METRICS_RECOVERY),
                "--publish-queue",
                str(queue_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/metrics-recovery/metrics-recovery.json").read_text(encoding="utf-8"))
        self.assertEqual(report["recoveryStatus"], "waiting_real_data")
        self.assertEqual(report["coverage"]["plannedOrQueuedItems"], 3)
        self.assertEqual(report["coverage"]["recordsWithMetrics"], 0)
        pending = {(item["platform"], item["status"]) for item in report["manualExportRequired"]}
        self.assertIn(("github", "publish_pending"), pending)
        self.assertIn(("xiaohongshu", "publish_pending"), pending)
        self.assertIn(("douyin", "publish_pending"), pending)

    def test_published_items_registers_queue_and_manual_urls(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="published-items-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        queue_dir = out_dir / "reports/promotion-manager/publish-queue"
        queue_dir.mkdir(parents=True)
        draft_path = queue_dir / "drafts/github-draft.md"
        draft_path.parent.mkdir(parents=True)
        draft_path.write_text("# github Publish Draft\n\n- Title: GitHub Launch Draft\n", encoding="utf-8")
        execution_path = queue_dir / "official-executions/github/reports/promotion-manager/publish-results/publish-execution.json"
        execution_path.parent.mkdir(parents=True)
        execution_path.write_text(
            json.dumps(
                {
                    "platform": "github",
                    "status": "published",
                    "publishedUrl": "https://github.com/example/repo/blob/main/PROMOTION.md",
                    "commitSha": "abc123",
                    "request": {"title": "GitHub Launch Draft"},
                }
            ),
            encoding="utf-8",
        )
        queue_path = queue_dir / "publish-queue.json"
        queue_path.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "platform": "github",
                            "status": "published",
                            "publishMode": "official_api_publish",
                            "contentDraft": str(draft_path),
                            "officialExecution": {
                                "publishedUrl": "https://github.com/example/repo/blob/main/PROMOTION.md",
                                "report": str(execution_path),
                            },
                        },
                        {"platform": "douyin", "status": "queued_browser_assisted", "publishMode": "browser_assisted_publish"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PUBLISHED_ITEMS),
                "--publish-queue",
                str(queue_path),
                "--platform",
                "xiaohongshu",
                "--published-url",
                "https://www.xiaohongshu.com/explore/note123",
                "--title",
                "Manual Launch Note",
                "--evidence",
                "xhs-screenshot.png",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/published-items/published-items.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        by_platform = {item["platform"]: item for item in report["records"]}
        self.assertEqual(report["summary"]["published"], 2)
        self.assertEqual(report["summary"]["pending"], 1)
        self.assertEqual(by_platform["github"]["title"], "GitHub Launch Draft")
        self.assertEqual(by_platform["xiaohongshu"]["contentId"], "note123")
        self.assertIn("xhs-screenshot.png", by_platform["xiaohongshu"]["evidence"])
        self.assertEqual(report["pendingQueueItems"][0]["platform"], "douyin")
        self.assertTrue((out_dir / "reports/promotion-manager/published-items/published-items.md").exists())

    def test_promotion_cycle_runner_connects_publish_queue_and_metrics_recovery(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="promotion-cycle-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        business_csv = out_dir / "business.csv"
        business_csv.write_text(
            "\n".join(
                [
                    "platform,publishedUrl,title,views,likes,orders,revenue,evidence",
                    "xiaohongshu,https://www.xiaohongshu.com/explore/note123,Launch Note,3000,380,2,$88.00,xhs-export.csv",
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PROMOTION_CYCLE_RUNNER),
                "--structured-json",
                str(snapshot_path),
                "--platforms",
                "github,xiaohongshu",
                "--skip-video",
                "--github-repo",
                "hqwzhu/Viral-Product-Copy-Video-Generator",
                "--github-path",
                "PROMOTION.md",
                "--published-url",
                "xiaohongshu=https://www.xiaohongshu.com/explore/note123",
                "--business-csv",
                str(business_csv),
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        cycle_path = out_dir / "output/reports/promotion-manager/cycle/promotion-cycle.json"
        cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
        self.assertEqual(cycle["workflow"]["status"], "ready")
        self.assertEqual(cycle["publishQueue"]["status"], "ready")
        self.assertEqual(cycle["publishedItems"]["status"], "ready")
        self.assertEqual(cycle["metricsRecovery"]["status"], "ready")
        self.assertEqual(cycle["automationStatus"], "partial_ready_with_real_metrics")
        self.assertTrue(Path(cycle["publishQueue"]["queue"]).exists())
        self.assertTrue(Path(cycle["publishedItems"]["publishedItems"]).exists())
        recovery = json.loads(Path(cycle["metricsRecovery"]["metricsRecovery"]).read_text(encoding="utf-8"))
        self.assertEqual(recovery["coverage"]["recordsWithMetrics"], 1)
        self.assertEqual(recovery["aggregates"]["totals"]["orders"], 2.0)
        self.assertEqual(recovery["aggregates"]["totals"]["revenue"], 88.0)
        self.assertTrue((out_dir / "output/reports/promotion-manager/cycle/promotion-cycle.md").exists())

    def test_final_capability_audit_reports_real_limits_without_secret_values(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="final-capability-audit-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        env = os.environ.copy()
        secret_value = "super-secret-token-for-test"
        for name in [
            "YOUTUBE_API_KEY",
            "YOUTUBE_OAUTH_ACCESS_TOKEN",
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "DOUYIN_CLIENT_KEY",
            "DOUYIN_CLIENT_SECRET",
            "DOUYIN_ACCESS_TOKEN",
            "DOUYIN_OPEN_ID",
            "TIKTOK_CLIENT_KEY",
            "TIKTOK_CLIENT_SECRET",
            "TIKTOK_ACCESS_TOKEN",
            "TIKTOK_OPEN_ID",
        ]:
            env.pop(name, None)
        env["GITHUB_TOKEN"] = secret_value
        subprocess.run(
            [
                sys.executable,
                str(FINAL_CAPABILITY_AUDIT),
                "--skip-runtime-checks",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
            env=env,
        )
        report_path = out_dir / "reports/promotion-manager/capability/final-capability-audit.json"
        report_text = report_path.read_text(encoding="utf-8")
        self.assertNotIn(secret_value, report_text)
        report = json.loads(report_text)
        self.assertEqual(report["credentials"]["github_write"]["presentEnv"], ["GITHUB_TOKEN"])
        self.assertFalse(report["credentials"]["github_write"]["valuesStored"])
        by_requirement = {item["id"]: item for item in report["requirements"]}
        self.assertIn(by_requirement["product_url_structured_intake"]["status"], {"ready", "partial_ready"})
        self.assertEqual(by_requirement["viral_creator_content_research"]["status"], "partial_ready")
        self.assertIn(by_requirement["copy_and_real_video_generation"]["status"], {"ready", "partial_ready"})
        self.assertEqual(
            by_requirement["all_platform_auto_publish"]["status"],
            "blocked_by_authorization_or_platform_limits",
        )
        self.assertEqual(
            by_requirement["fully_autonomous_self_evolution"]["status"],
            "blocked_by_safety_boundary",
        )
        self.assertEqual(report["platforms"]["xiaohongshu"]["directPublish"], "manual_or_browser_assisted_only")
        self.assertTrue(any(item["purpose"] == "one_command_cycle" for item in report["recommendedCommands"]))
        self.assertTrue(report["platformAccessAudit"]["ready"])
        self.assertTrue(any(item["purpose"] == "audit_platform_official_access" for item in report["recommendedCommands"]))
        self.assertTrue((out_dir / "reports/promotion-manager/capability/final-capability-audit.md").exists())

    def test_platform_access_audit_maps_official_paths_without_secret_values(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="platform-access-audit-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        env = os.environ.copy()
        secret_value = "super-secret-platform-token"
        for name in [
            "YOUTUBE_API_KEY",
            "YOUTUBE_OAUTH_ACCESS_TOKEN",
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "DOUYIN_CLIENT_KEY",
            "DOUYIN_CLIENT_SECRET",
            "DOUYIN_ACCESS_TOKEN",
            "DOUYIN_OPEN_ID",
            "TIKTOK_CLIENT_KEY",
            "TIKTOK_CLIENT_SECRET",
            "TIKTOK_ACCESS_TOKEN",
            "TIKTOK_OPEN_ID",
        ]:
            env.pop(name, None)
        env["YOUTUBE_OAUTH_ACCESS_TOKEN"] = secret_value
        subprocess.run(
            [
                sys.executable,
                str(PLATFORM_ACCESS_AUDIT),
                "--platforms",
                "youtube,github,xiaohongshu,zhihu,douyin,tiktok",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
            env=env,
        )
        report_path = out_dir / "reports/promotion-manager/platform-access/platform-access-audit.json"
        report_text = report_path.read_text(encoding="utf-8")
        self.assertNotIn(secret_value, report_text)
        report = json.loads(report_text)
        by_platform = {item["platform"]: item for item in report["platforms"]}
        self.assertEqual(by_platform["youtube"]["publish"]["access"], "implemented_official_api")
        self.assertTrue(by_platform["youtube"]["publish"]["readyForAutomation"])
        self.assertEqual(by_platform["github"]["publish"]["access"], "implemented_official_api")
        self.assertEqual(by_platform["xiaohongshu"]["publish"]["access"], "no_verified_public_creator_publish_endpoint")
        self.assertEqual(by_platform["zhihu"]["publish"]["mode"], "manual_or_browser_assisted_until_verified")
        self.assertEqual(by_platform["douyin"]["publish"]["access"], "official_candidate_not_integrated")
        self.assertEqual(by_platform["tiktok"]["automationLevel"], "official_app_integration_required")
        self.assertTrue(any(item["gap"] == "verified_official_creator_publish_api_missing" for item in report["implementationGaps"]))
        self.assertTrue((out_dir / "reports/promotion-manager/platform-access/platform-access-audit.md").exists())

    def test_viral_discovery_runner_builds_multiplatform_library_and_creator_tasks(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="viral-discovery-runner-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_dir = out_dir / "html"
        html_dir.mkdir()
        fixtures = {
            "youtube": (
                "https://www.youtube.com/watch?v=abc123",
                "AI workflow exploded to 1M views",
                "creator: Launch Lab views: 1.2M likes: 52K comments: 1200",
            ),
            "zhihu": (
                "https://www.zhihu.com/question/123/answer/456",
                "How AI operators build content engines",
                "creator: Zhihu Builder likes: 8800 comments: 640",
            ),
            "xiaohongshu": (
                "https://www.xiaohongshu.com/explore/note123",
                "3 steps to launch an AI product note",
                "creator: Red Launch favorites: 12000 likes: 9000 comments: 830",
            ),
            "douyin": (
                "https://www.douyin.com/video/123",
                "30 seconds AI product demo hook",
                "creator: Demo Studio views: 2.4M likes: 180K shares: 9000",
            ),
            "github": (
                "https://github.com/example/ai-promo-kit",
                "AI promo kit repository",
                "creator: example stars: 4200 forks: 380",
            ),
        }
        for platform, (url, title, body) in fixtures.items():
            (html_dir / f"{platform}.html").write_text(
                f"""
                <html><head><title>{platform} search</title></head>
                <body>
                  <article>
                    <a href="{url}">{title}</a>
                    <p>{body}</p>
                    <p>Hook: stop writing product copy from scratch.</p>
                    <p>CTA: try the workflow and follow for more.</p>
                  </article>
                </body></html>
                """,
                encoding="utf-8",
            )
        subprocess.run(
            [
                sys.executable,
                str(VIRAL_DISCOVERY_RUNNER),
                "--query",
                "AI product promotion",
                "--platforms",
                "youtube,zhihu,xiaohongshu,douyin,github",
                "--top-n",
                "5",
                "--html-snapshot-dir",
                str(html_dir),
                "--out-dir",
                str(out_dir / "output"),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "output/reports/promotion-manager/competitors/viral-discovery-run.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["coverage"]["requestedPlatforms"], 5)
        self.assertEqual(report["coverage"]["searchCapturesReady"], 5)
        self.assertEqual(report["coverage"]["viralMaterials"], 5)
        self.assertGreaterEqual(report["coverage"]["creators"], 1)
        self.assertTrue(Path(report["viralContentLibrary"]["library"]).exists())
        self.assertTrue(Path(report["creatorLeaderboard"]["leaderboard"]).exists())
        self.assertTrue(Path(report["creatorLeaderboard"]["followUpTasks"]).exists())
        task_summary = report["viralContentLibrary"]["taskSummary"]["modes"]
        self.assertEqual(task_summary["public_url_capture_candidate"], 2)
        self.assertEqual(task_summary["browser_assisted_capture_required"], 3)
        self.assertTrue((out_dir / "output/reports/promotion-manager/competitors/viral-discovery-run.md").exists())

    def test_publish_url_capture_registers_structured_snapshot(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-url-capture-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "published-snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://www.xiaohongshu.com/explore/note123",
                    "title": "AI Prompt Kit launch note",
                    "text": "Published note page visible in browser.",
                    "screenshot": "xhs-published.png",
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_URL_CAPTURE),
                "--structured-json",
                str(snapshot_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        capture = json.loads((out_dir / "reports/promotion-manager/publish-capture/publish-url-capture.json").read_text(encoding="utf-8"))
        self.assertEqual(capture["status"], "ready")
        self.assertEqual(capture["record"]["platform"], "xiaohongshu")
        self.assertEqual(capture["record"]["contentId"], "note123")
        published = json.loads((out_dir / "reports/promotion-manager/published-items/published-items.json").read_text(encoding="utf-8"))
        self.assertEqual(published["summary"]["published"], 1)
        self.assertEqual(published["records"][0]["publishedUrl"], "https://www.xiaohongshu.com/explore/note123")

    def test_publish_url_capture_extracts_html_canonical_url(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-url-capture-html-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        html_path = out_dir / "published.html"
        html_path.write_text(
            """<!doctype html>
<html>
<head>
  <title>知乎发布文章</title>
  <link rel="canonical" href="https://zhuanlan.zhihu.com/p/123456">
  <meta property="og:title" content="AI Prompt Kit launch article">
</head>
<body><h1>AI Prompt Kit launch article</h1></body>
</html>""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_URL_CAPTURE),
                "--html-file",
                str(html_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/publish-capture/publish-url-capture.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["record"]["platform"], "zhihu")
        self.assertEqual(report["record"]["publishedUrl"], "https://zhuanlan.zhihu.com/p/123456")

    def test_publish_url_capture_blocks_preview_urls(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-url-capture-preview-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        text_path = out_dir / "preview.txt"
        text_path.write_text(
            "Platform: douyin\nURL: https://www.douyin.com/user/self/preview/video123\nTitle: Draft preview\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_URL_CAPTURE),
                "--text-file",
                str(text_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/publish-capture/publish-url-capture.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "blocked")
        self.assertIn("url_looks_like_draft_or_preview", report["issues"])
        self.assertFalse((out_dir / "reports/promotion-manager/published-items/published-items.json").exists())

    def test_metrics_recovery_reads_default_published_items_report(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="metrics-recovery-published-items-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        published_dir = out_dir / "reports/promotion-manager/published-items"
        published_dir.mkdir(parents=True)
        (published_dir / "published-items.json").write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "platform": "xiaohongshu",
                            "publishedUrl": "https://www.xiaohongshu.com/explore/note123",
                            "title": "Launch Note",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        business_csv = out_dir / "business.csv"
        business_csv.write_text(
            "\n".join(
                [
                    "platform,publishedUrl,title,views,likes,orders,revenue,evidence",
                    "xiaohongshu,https://www.xiaohongshu.com/explore/note123,Launch Note,3000,380,2,$88.00,xhs-export.csv",
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(METRICS_RECOVERY),
                "--business-csv",
                str(business_csv),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report = json.loads((out_dir / "reports/promotion-manager/metrics-recovery/metrics-recovery.json").read_text(encoding="utf-8"))
        self.assertEqual(report["coverage"]["publishedItemsDiscovered"], 1)
        self.assertEqual(report["aggregates"]["totals"]["orders"], 2.0)
        self.assertEqual(report["recoveryStatus"], "ready")

    def test_publish_executor_github_dry_run_requires_explicit_execution(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-executor-github-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        body_path = out_dir / "README-promo.md"
        body_path.write_text("# Launch draft\n\nPromotion copy.", encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_EXECUTOR),
                "--platform",
                "github",
                "--github-action",
                "file",
                "--github-repo",
                "hqwzhu/Viral-Product-Copy-Video-Generator",
                "--path",
                "PROMOTION.md",
                "--content-file",
                str(body_path),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/publish-results/publish-execution.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "dry_run")
        self.assertEqual(report["platform"], "github")
        self.assertTrue(report["approvalRequired"])
        self.assertEqual(report["request"]["method"], "PUT")
        self.assertNotIn("GITHUB_TOKEN", json.dumps(report))

    def test_publish_executor_youtube_dry_run_uses_oauth_boundary(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-executor-youtube-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        video_path = out_dir / "draft.mp4"
        video_path.write_bytes(b"not a real video but enough for dry-run")
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_EXECUTOR),
                "--platform",
                "youtube",
                "--video-file",
                str(video_path),
                "--title",
                "Launch draft",
                "--description",
                "Promotion video draft.",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
        )
        report_path = out_dir / "reports/promotion-manager/publish-results/publish-execution.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "dry_run")
        self.assertEqual(report["platform"], "youtube")
        self.assertEqual(report["officialApi"], "YouTube Data API videos.insert")
        self.assertIn("upload/youtube/v3/videos", report["request"]["endpoint"])
        self.assertNotIn("YOUTUBE_OAUTH_ACCESS_TOKEN", json.dumps(report))

    def test_publish_queue_builds_official_dry_runs_and_manual_tasks(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-queue-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        workflow_out = out_dir / "output"
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--structured-json",
                str(snapshot_path),
                "--platforms",
                "youtube,zhihu,xiaohongshu,douyin,github",
                "--skip-video",
                "--out-dir",
                str(workflow_out),
            ],
            check=True,
            cwd=ROOT,
        )
        video_path = out_dir / "youtube-draft.mp4"
        video_path.write_bytes(b"dry-run video placeholder")
        manifest_path = workflow_out / "reports/promotion-manager/agent-run/workflow-manifest.json"
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_QUEUE),
                "--workflow-manifest",
                str(manifest_path),
                "--promotion-out-dir",
                str(workflow_out),
                "--out-dir",
                str(workflow_out),
                "--github-repo",
                "hqwzhu/Viral-Product-Copy-Video-Generator",
                "--github-path",
                "PROMOTION.md",
                "--youtube-video-file",
                str(video_path),
            ],
            check=True,
            cwd=ROOT,
        )
        queue_path = workflow_out / "reports/promotion-manager/publish-queue/publish-queue.json"
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        by_platform = {item["platform"]: item for item in queue["records"]}
        self.assertEqual(by_platform["github"]["status"], "dry_run")
        self.assertEqual(by_platform["youtube"]["status"], "dry_run")
        self.assertEqual(by_platform["xiaohongshu"]["status"], "queued_manual")
        self.assertEqual(by_platform["zhihu"]["status"], "queued_manual")
        self.assertEqual(by_platform["douyin"]["status"], "queued_browser_assisted")
        self.assertTrue(Path(by_platform["github"]["officialExecution"]["report"]).exists())
        self.assertTrue(Path(by_platform["youtube"]["officialExecution"]["report"]).exists())
        self.assertTrue(Path(by_platform["xiaohongshu"]["contentDraft"]).exists())
        published_items_path = workflow_out / "reports/promotion-manager/published-items/published-items.json"
        self.assertTrue(published_items_path.exists())
        published_items = json.loads(published_items_path.read_text(encoding="utf-8"))
        self.assertEqual(published_items["summary"]["published"], 0)
        self.assertEqual(published_items["summary"]["pending"], 5)
        serialized = json.dumps(queue)
        self.assertNotIn("GITHUB_TOKEN", serialized)
        self.assertNotIn("YOUTUBE_OAUTH_ACCESS_TOKEN", serialized)

    def test_publish_readiness_runner_audits_queue_without_secret_values(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="publish-readiness-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        snapshot_path = out_dir / "snapshot.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "url": "https://example.com/ai-prompt-kit",
                    "title": "AI Prompt Kit",
                    "description": "Prompt templates for product copy, SEO content, and video scripts.",
                    "targetAudience": ["AI operators"],
                    "painPoints": ["Slow launch content"],
                }
            ),
            encoding="utf-8",
        )
        workflow_out = out_dir / "output"
        subprocess.run(
            [
                sys.executable,
                str(RUN_WORKFLOW),
                "--structured-json",
                str(snapshot_path),
                "--platforms",
                "youtube,zhihu,xiaohongshu,douyin,github",
                "--skip-video",
                "--out-dir",
                str(workflow_out),
            ],
            check=True,
            cwd=ROOT,
        )
        video_path = out_dir / "youtube-draft.mp4"
        video_path.write_bytes(b"dry-run video placeholder")
        env = os.environ.copy()
        secret_value = "fake-gh-token-for-readiness-test"
        for name in [
            "YOUTUBE_OAUTH_ACCESS_TOKEN",
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "DOUYIN_CLIENT_KEY",
            "DOUYIN_CLIENT_SECRET",
            "DOUYIN_ACCESS_TOKEN",
            "DOUYIN_OPEN_ID",
        ]:
            env.pop(name, None)
        env["GITHUB_TOKEN"] = secret_value
        manifest_path = workflow_out / "reports/promotion-manager/agent-run/workflow-manifest.json"
        subprocess.run(
            [
                sys.executable,
                str(PUBLISH_READINESS),
                "--workflow-manifest",
                str(manifest_path),
                "--build-queue",
                "--github-repo",
                "hqwzhu/Viral-Product-Copy-Video-Generator",
                "--youtube-video-file",
                str(video_path),
                "--out-dir",
                str(workflow_out),
            ],
            check=True,
            cwd=ROOT,
            env=env,
        )
        report_path = workflow_out / "reports/promotion-manager/publish-readiness/publish-readiness.json"
        report_text = report_path.read_text(encoding="utf-8")
        self.assertNotIn(secret_value, report_text)
        report = json.loads(report_text)
        self.assertEqual(report["status"], "partial_ready")
        by_platform = {item["platform"]: item for item in report["records"]}
        self.assertEqual(by_platform["github"]["readiness"], "dry_run_ready")
        self.assertEqual(by_platform["github"]["credentialStatus"]["presentEnv"], ["GITHUB_TOKEN"])
        self.assertEqual(by_platform["youtube"]["readiness"], "missing_credentials")
        self.assertEqual(by_platform["zhihu"]["readiness"], "manual_publish_required")
        self.assertEqual(by_platform["xiaohongshu"]["readiness"], "manual_publish_required")
        self.assertEqual(by_platform["douyin"]["readiness"], "browser_assisted_or_official_app_required")
        self.assertTrue(Path(report["inputs"]["publishQueue"]).exists())
        self.assertTrue((workflow_out / "reports/promotion-manager/publish-readiness/publish-readiness.md").exists())

    def test_youtube_oauth_publish_dry_run_generates_auth_url_without_tokens(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="youtube-oauth-publish-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        video_path = out_dir / "draft.mp4"
        video_path.write_bytes(b"dry-run only")
        env = os.environ.copy()
        env["GOOGLE_OAUTH_CLIENT_ID"] = "client-id.apps.googleusercontent.com"
        env.pop("GOOGLE_OAUTH_CLIENT_SECRET", None)
        subprocess.run(
            [
                sys.executable,
                str(YOUTUBE_OAUTH_PUBLISH),
                "--video-file",
                str(video_path),
                "--title",
                "Launch draft",
                "--description",
                "Promotion video draft.",
                "--state",
                "test-state",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
            env=env,
        )
        report_path = out_dir / "reports/promotion-manager/publish-results/youtube-oauth-publish.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "dry_run")
        self.assertIn("accounts.google.com/o/oauth2/v2/auth", report["authUrl"])
        self.assertIn("youtube.upload", report["authUrl"])
        self.assertFalse(report["credentialStatus"]["tokensSaved"])
        self.assertNotIn("access_token", json.dumps(report))
        self.assertNotIn("GOOGLE_OAUTH_CLIENT_SECRET", json.dumps(report))

    def test_youtube_oauth_publish_execute_requires_client_secret(self) -> None:
        out_dir = Path(tempfile.mkdtemp(prefix="youtube-oauth-publish-blocked-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        video_path = out_dir / "draft.mp4"
        video_path.write_bytes(b"dry-run only")
        env = os.environ.copy()
        env["GOOGLE_OAUTH_CLIENT_ID"] = "client-id.apps.googleusercontent.com"
        env.pop("GOOGLE_OAUTH_CLIENT_SECRET", None)
        subprocess.run(
            [
                sys.executable,
                str(YOUTUBE_OAUTH_PUBLISH),
                "--execute",
                "--approval",
                "I_APPROVE_PUBLISH",
                "--video-file",
                str(video_path),
                "--title",
                "Launch draft",
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            cwd=ROOT,
            env=env,
        )
        report_path = out_dir / "reports/promotion-manager/publish-results/youtube-oauth-publish.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "blocked")
        self.assertIn("GOOGLE_OAUTH_CLIENT_SECRET", report["reason"])
        self.assertNotIn("accessToken", json.dumps(report))

    def test_video_renderer_creates_mp4_when_ffmpeg_exists(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg is not installed")
        out_dir = self.run_all()
        content_json = out_dir / "reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json"
        video_path = out_dir / "videos" / "ai-prompt-kit-douyin.mp4"
        subprocess.run(
            [
                sys.executable,
                str(RENDER_VIDEO),
                "--content-json",
                str(content_json),
                "--platform",
                "douyin",
                "--out",
                str(video_path),
            ],
            check=True,
            cwd=ROOT,
        )
        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 1000)
        metadata = json.loads(video_path.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["platform"], "douyin")

    def test_video_renderer_muxes_voiceover_audio_file(self) -> None:
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg is not installed")
        out_dir = Path(tempfile.mkdtemp(prefix="video-voiceover-test-"))
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        content_json = out_dir / "content.json"
        audio_path = out_dir / "voiceover.wav"
        video_path = out_dir / "promo-with-voiceover.mp4"
        content_json.write_text(
            json.dumps(
                {
                    "douyin": {
                        "title": "Launch draft",
                        "storyboard": [
                            {"time": "0-2s", "visual": "Show the product", "voiceover": "Turn one product URL into content."}
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2",
                str(audio_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                sys.executable,
                str(RENDER_VIDEO),
                "--content-json",
                str(content_json),
                "--platform",
                "douyin",
                "--voiceover-audio",
                str(audio_path),
                "--out",
                str(video_path),
            ],
            check=True,
            cwd=ROOT,
        )
        self.assertTrue(video_path.exists())
        metadata = json.loads(video_path.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["audioMode"], "file")
        self.assertEqual(Path(metadata["audio"]), audio_path)


if __name__ == "__main__":
    unittest.main()

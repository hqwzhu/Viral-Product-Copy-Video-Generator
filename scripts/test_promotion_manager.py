#!/usr/bin/env python3
"""Regression tests for the viral product promotion skill script."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promotion_manager.py"
PRODUCT_INTAKE = ROOT / "scripts" / "product_intake.py"
BROWSER_SNAPSHOT = ROOT / "scripts" / "browser_snapshot.py"
RENDER_VIDEO = ROOT / "scripts" / "render_video.py"
COMPETITOR_INTAKE = ROOT / "scripts" / "competitor_intake.py"
COMPETITOR_DISCOVERY = ROOT / "scripts" / "competitor_discovery.py"
COMPETITOR_COLLECTOR = ROOT / "scripts" / "competitor_collector.py"
METRICS_INTAKE = ROOT / "scripts" / "metrics_intake.py"
PUBLISH_EXECUTOR = ROOT / "scripts" / "publish_executor.py"
PUBLISH_QUEUE = ROOT / "scripts" / "publish_queue.py"
YOUTUBE_OAUTH_PUBLISH = ROOT / "scripts" / "youtube_oauth_publish.py"
RUN_WORKFLOW = ROOT / "scripts" / "run_promotion_workflow.py"
AUTOMATION_SCHEDULER = ROOT / "scripts" / "automation_scheduler.py"
PLATFORM_SEARCH_CAPTURE = ROOT / "scripts" / "platform_search_capture.py"
PLATFORM_SEARCH_BROWSER = ROOT / "scripts" / "platform_search_browser.py"


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
        serialized = json.dumps(queue)
        self.assertNotIn("GITHUB_TOKEN", serialized)
        self.assertNotIn("YOUTUBE_OAUTH_ACCESS_TOKEN", serialized)

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

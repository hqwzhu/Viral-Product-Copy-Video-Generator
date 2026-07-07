#!/usr/bin/env python3
"""Regression tests for the viral product promotion skill script."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promotion_manager.py"
PRODUCT_INTAKE = ROOT / "scripts" / "product_intake.py"
RENDER_VIDEO = ROOT / "scripts" / "render_video.py"
COMPETITOR_INTAKE = ROOT / "scripts" / "competitor_intake.py"
COMPETITOR_DISCOVERY = ROOT / "scripts" / "competitor_discovery.py"
METRICS_INTAKE = ROOT / "scripts" / "metrics_intake.py"


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


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""One command runner for the highest-automation promotion manager flow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PRODUCT_BATCH_RUNNER = SCRIPTS / "product_batch_runner.py"
PUBLISH_READINESS = SCRIPTS / "publish_readiness_runner.py"
BROWSER_PUBLISH_ASSISTANT = SCRIPTS / "browser_publish_assistant.py"
PLATFORM_ACCESS_AUDIT = SCRIPTS / "platform_access_audit.py"
FINAL_CAPABILITY_AUDIT = SCRIPTS / "final_capability_audit.py"
SELF_EVOLUTION_AUDIT = SCRIPTS / "self_evolution_audit.py"
TODAY = date.today().isoformat()
DEFAULT_PLATFORMS = "youtube,zhihu,xiaohongshu,douyin,github"


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []

    batch = run_product_batch(args, out_dir, steps)
    publish_readiness = run_publish_readiness(args, batch, steps)
    browser_publish = run_browser_publish_assistant(args, batch, steps)
    audits = run_audits(args, out_dir, steps)
    cycle_evidence = collect_cycle_evidence(batch)
    report = build_report(args, out_dir, batch, publish_readiness, browser_publish, cycle_evidence, audits, steps)
    write_report(out_dir, report)
    print(f"Final capability run written to: {(report_dir(out_dir) / 'final-capability-run.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full safe promotion manager flow from product URL to next-round optimization.")
    parser.add_argument("--url", action="append", default=[], help="Product URL. Can be repeated.")
    parser.add_argument("--urls-file", default="", help="Text file with one product URL per line.")
    parser.add_argument("--out-dir", default="./promotion-output")

    product = parser.add_argument_group("Product reading")
    product.add_argument("--skip-browser", action="store_true")
    product.add_argument("--no-static-fallback", action="store_true")
    product.add_argument("--install-browser-if-missing", action="store_true")
    product.add_argument("--timeout-ms", type=int, default=30000)
    product.add_argument("--wait-until", default="networkidle", choices=["load", "domcontentloaded", "networkidle"])

    workflow = parser.add_argument_group("Promotion workflow")
    workflow.add_argument("--platforms", default=DEFAULT_PLATFORMS)
    workflow.add_argument("--goal", default="leads", choices=["traffic", "leads", "sales", "seo", "brand", "github_stars"])
    workflow.add_argument("--language", default="zh-CN")
    workflow.add_argument("--top-n", type=int, default=10)
    workflow.add_argument("--competitor-query", default="")
    workflow.add_argument("--auto-search-competitors", action="store_true")
    workflow.add_argument("--live-official-competitors", action="store_true")
    workflow.add_argument("--run-creator-follow-up", action="store_true")
    workflow.add_argument("--creator-follow-up-dry-run", action="store_true")
    workflow.add_argument("--run-follow-up-captures", action="store_true")
    workflow.add_argument("--follow-up-dry-run", action="store_true")
    workflow.add_argument("--skip-video", action="store_true")
    workflow.add_argument("--video-platforms", default="auto")
    workflow.add_argument("--generate-voiceover", action="store_true")

    discovery = parser.add_argument_group("Viral discovery")
    discovery.add_argument("--skip-multi-query-viral-discovery", action="store_true")
    discovery.add_argument("--multi-query-dry-run", action="store_true")
    discovery.add_argument("--multi-query-query", action="append", default=[])
    discovery.add_argument("--multi-query-query-count", type=int, default=5)
    discovery.add_argument("--multi-query-platforms", default="")
    discovery.add_argument("--multi-query-top-n", type=int, default=20)
    discovery.add_argument("--multi-query-live-official", action="store_true")
    discovery.add_argument("--multi-query-run-creator-follow-up", action="store_true")
    discovery.add_argument("--multi-query-run-follow-up-captures", action="store_true")
    discovery.add_argument("--multi-query-capture-browser-assisted-follow-ups", action="store_true")

    publish = parser.add_argument_group("Publishing")
    publish.add_argument("--skip-publish-queue", action="store_true")
    publish.add_argument("--publish-platforms", default="")
    publish.add_argument("--github-repo", default="")
    publish.add_argument("--github-path", default="PROMOTION.md")
    publish.add_argument("--youtube-video-file", default="")
    publish.add_argument("--douyin-video-file", default="")
    publish.add_argument("--skip-publish-readiness", action="store_true")
    publish.add_argument("--skip-browser-publish-assistant", action="store_true")
    publish.add_argument("--browser-publish-open-browser", action="store_true")

    metrics = parser.add_argument_group("Real evidence recovery")
    metrics.add_argument("--skip-metrics-recovery", action="store_true")
    metrics.add_argument("--published-url", action="append", default=[])
    metrics.add_argument("--metrics-github-repo", action="append", default=[])
    metrics.add_argument("--metrics-youtube-video-id", action="append", default=[])
    metrics.add_argument("--business-csv", action="append", default=[])
    metrics.add_argument("--business-json", action="append", default=[])
    metrics.add_argument("--business-text", action="append", default=[])
    metrics.add_argument("--skip-post-publish-metrics-capture", action="store_true")
    metrics.add_argument("--post-publish-metrics-allow-localhost", action="store_true")
    metrics.add_argument("--post-publish-metrics-capture-browser-assisted", action="store_true")
    metrics.add_argument("--skip-comment-evidence-capture", action="store_true")
    metrics.add_argument("--comment-evidence-allow-localhost", action="store_true")
    metrics.add_argument("--comment-evidence-capture-browser-assisted", action="store_true")
    metrics.add_argument("--skip-business-attribution", action="store_true")
    metrics.add_argument("--skip-next-round-optimization", action="store_true")

    audits = parser.add_argument_group("Audits")
    audits.add_argument("--skip-platform-access-audit", action="store_true")
    audits.add_argument("--skip-final-capability-audit", action="store_true")
    audits.add_argument("--skip-self-evolution-audit", action="store_true")
    return parser.parse_args()


def run_product_batch(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    command = [sys.executable, str(PRODUCT_BATCH_RUNNER), "--out-dir", str(out_dir)]
    append_many(command, "--url", args.url)
    append_if_present(command, "--urls-file", args.urls_file)
    append_common_batch_args(command, args)
    step = run_command("product_batch_runner", command)
    steps.append(step)
    report_path = out_dir / "reports/promotion-manager/batch/product-batch-runner.json"
    report = read_json(report_path)
    return {
        "status": report.get("status", "error") if step["exitCode"] == 0 and report_path.exists() else "error",
        "report": str(report_path) if report_path.exists() else "",
        "summary": report.get("summary", {}),
        "promotionRuns": report.get("promotionRuns", []),
        "exitCode": step["exitCode"],
    }


def append_common_batch_args(command: list[str], args: argparse.Namespace) -> None:
    for flag, enabled in [
        ("--skip-browser", args.skip_browser),
        ("--no-static-fallback", args.no_static_fallback),
        ("--install-browser-if-missing", args.install_browser_if_missing),
        ("--auto-search-competitors", args.auto_search_competitors),
        ("--live-official-competitors", args.live_official_competitors),
        ("--run-creator-follow-up", args.run_creator_follow_up),
        ("--creator-follow-up-dry-run", args.creator_follow_up_dry_run),
        ("--run-follow-up-captures", args.run_follow_up_captures),
        ("--follow-up-dry-run", args.follow_up_dry_run),
        ("--skip-video", args.skip_video),
        ("--generate-voiceover", args.generate_voiceover),
        ("--skip-publish-queue", args.skip_publish_queue),
        ("--skip-metrics-recovery", args.skip_metrics_recovery),
    ]:
        if enabled:
            command.append(flag)
    command.extend(["--timeout-ms", str(args.timeout_ms), "--wait-until", args.wait_until])
    command.extend(["--platforms", args.platforms, "--goal", args.goal, "--language", args.language, "--top-n", str(args.top_n)])
    append_if_present(command, "--competitor-query", args.competitor_query)
    append_if_present(command, "--video-platforms", args.video_platforms)
    append_if_present(command, "--publish-platforms", args.publish_platforms)
    append_if_present(command, "--github-repo", args.github_repo)
    append_if_present(command, "--github-path", args.github_path)
    append_if_present(command, "--youtube-video-file", args.youtube_video_file)
    append_if_present(command, "--douyin-video-file", args.douyin_video_file)
    if not args.skip_multi_query_viral_discovery:
        command.append("--run-multi-query-viral-discovery")
        command.extend(["--multi-query-query-count", str(args.multi_query_query_count), "--multi-query-top-n", str(args.multi_query_top_n)])
        append_many(command, "--multi-query-query", args.multi_query_query)
        append_if_present(command, "--multi-query-platforms", args.multi_query_platforms)
        if args.multi_query_dry_run:
            command.append("--multi-query-dry-run")
        if args.multi_query_live_official:
            command.append("--multi-query-live-official")
        if args.multi_query_run_creator_follow_up:
            command.append("--multi-query-run-creator-follow-up")
        if args.multi_query_run_follow_up_captures:
            command.append("--multi-query-run-follow-up-captures")
        if args.multi_query_capture_browser_assisted_follow_ups:
            command.append("--multi-query-capture-browser-assisted-follow-ups")
    append_many(command, "--published-url", args.published_url)
    append_many(command, "--metrics-github-repo", args.metrics_github_repo)
    append_many(command, "--metrics-youtube-video-id", args.metrics_youtube_video_id)
    append_many(command, "--business-csv", args.business_csv)
    append_many(command, "--business-json", args.business_json)
    append_many(command, "--business-text", args.business_text)
    if not args.skip_post_publish_metrics_capture:
        command.append("--run-post-publish-metrics-capture")
    if args.post_publish_metrics_allow_localhost:
        command.append("--post-publish-metrics-allow-localhost")
    if args.post_publish_metrics_capture_browser_assisted:
        command.append("--post-publish-metrics-capture-browser-assisted")
    if not args.skip_comment_evidence_capture:
        command.append("--run-comment-evidence-capture")
    if args.comment_evidence_allow_localhost:
        command.append("--comment-evidence-allow-localhost")
    if args.comment_evidence_capture_browser_assisted:
        command.append("--comment-evidence-capture-browser-assisted")
    if not args.skip_business_attribution:
        command.append("--run-business-attribution")
    if not args.skip_next_round_optimization:
        command.append("--run-next-round-optimization")


def run_publish_readiness(args: argparse.Namespace, batch: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if args.skip_publish_readiness:
        return []
    results = []
    for run in batch.get("promotionRuns", []):
        manifest = existing_path(run.get("workflowManifest", ""))
        run_dir = existing_dir(run.get("outputDir", ""))
        if not manifest or not run_dir:
            continue
        command = [
            sys.executable,
            str(PUBLISH_READINESS),
            "--workflow-manifest",
            str(manifest),
            "--build-queue",
            "--out-dir",
            str(run_dir),
        ]
        append_publish_args(command, args)
        step = run_command(f"publish_readiness_{run.get('id', 'product')}", command, check=False)
        steps.append(step)
        report_path = run_dir / "reports/promotion-manager/publish-readiness/publish-readiness.json"
        report = read_json(report_path)
        results.append(
            {
                "productRunId": run.get("id", ""),
                "status": report.get("status", "error") if step["exitCode"] == 0 and report_path.exists() else "error",
                "report": str(report_path) if report_path.exists() else "",
                "summary": report.get("summary", {}),
                "exitCode": step["exitCode"],
            }
        )
    return results


def run_browser_publish_assistant(args: argparse.Namespace, batch: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if args.skip_browser_publish_assistant:
        return []
    results = []
    for run in batch.get("promotionRuns", []):
        run_dir = existing_dir(run.get("outputDir", ""))
        queue_path = existing_path(run.get("publishQueue", "")) or (run_dir / "reports/promotion-manager/publish-queue/publish-queue.json" if run_dir else None)
        if not run_dir or not queue_path or not queue_path.exists():
            continue
        command = [
            sys.executable,
            str(BROWSER_PUBLISH_ASSISTANT),
            "--publish-queue",
            str(queue_path),
            "--platforms",
            args.publish_platforms or args.platforms,
            "--out-dir",
            str(run_dir),
        ]
        if args.browser_publish_open_browser:
            command.append("--open-browser")
        step = run_command(f"browser_publish_assistant_{run.get('id', 'product')}", command, check=False)
        steps.append(step)
        report_path = run_dir / "reports/promotion-manager/browser-publish/browser-publish-assistant.json"
        report = read_json(report_path)
        results.append(
            {
                "productRunId": run.get("id", ""),
                "status": report.get("status", "error") if step["exitCode"] == 0 and report_path.exists() else "error",
                "report": str(report_path) if report_path.exists() else "",
                "summary": report.get("summary", {}),
                "exitCode": step["exitCode"],
            }
        )
    return results


def run_audits(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    audits: dict[str, Any] = {}
    if not args.skip_platform_access_audit:
        audits["platformAccess"] = run_audit("platform_access_audit", PLATFORM_ACCESS_AUDIT, out_dir, steps)
    if not args.skip_final_capability_audit:
        audits["finalCapability"] = run_audit("final_capability_audit", FINAL_CAPABILITY_AUDIT, out_dir, steps)
    if not args.skip_self_evolution_audit:
        audits["selfEvolution"] = run_audit("self_evolution_audit", SELF_EVOLUTION_AUDIT, out_dir, steps)
    return audits


def run_audit(name: str, script: Path, out_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    command = [sys.executable, str(script), "--out-dir", str(out_dir)]
    step = run_command(name, command, check=False)
    steps.append(step)
    path = audit_report_path(name, out_dir)
    report = read_json(path)
    return {
        "status": report.get("finalStatus") or report.get("status") or ("ready" if step["exitCode"] == 0 else "error"),
        "report": str(path) if path.exists() else "",
        "exitCode": step["exitCode"],
    }


def build_report(
    args: argparse.Namespace,
    out_dir: Path,
    batch: dict[str, Any],
    publish_readiness: list[dict[str, Any]],
    browser_publish: list[dict[str, Any]],
    cycle_evidence: list[dict[str, Any]],
    audits: dict[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = {
        "productBatchStatus": batch.get("status", ""),
        "promotionRuns": len(batch.get("promotionRuns", [])),
        "publishReadinessRuns": len(publish_readiness),
        "browserPublishAssistantRuns": len(browser_publish),
        "nextRoundOptimizationRuns": int((batch.get("summary") or {}).get("nextRoundOptimizationRuns") or 0),
        "multiQueryDiscoveryRuns": int((batch.get("summary") or {}).get("multiQueryDiscoveryRuns") or 0),
    }
    summary.update(cycle_evidence_summary(cycle_evidence))
    return {
        "generatedAt": TODAY,
        "status": final_status(batch, publish_readiness, browser_publish, audits),
        "outDir": str(out_dir),
        "input": {
            "urls": args.url,
            "urlsFile": args.urls_file,
            "platforms": args.platforms,
            "codexReadFirst": True,
        },
        "summary": summary,
        "productBatch": batch,
        "cycleEvidence": cycle_evidence,
        "publishReadiness": publish_readiness,
        "browserPublishAssistant": browser_publish,
        "audits": audits,
        "externalGates": external_gates(),
        "recommendedNextCommands": recommended_next_commands(out_dir),
        "guardrails": guardrails(),
        "steps": steps,
    }


def collect_cycle_evidence(batch: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for run in batch.get("promotionRuns", []):
        run_dir = existing_dir(run.get("outputDir", ""))
        cycle_path = existing_path(run.get("cycleReport", "")) or (
            run_dir / "reports/promotion-manager/cycle/promotion-cycle.json" if run_dir else None
        )
        manifest_path = existing_path(run.get("workflowManifest", ""))
        cycle = read_json(cycle_path) if cycle_path else {}
        manifest = read_json(manifest_path) if manifest_path else {}
        artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
        videos = manifest.get("videoGeneration") if isinstance(manifest.get("videoGeneration"), list) else []
        item = {
            "productRunId": run.get("id", ""),
            "url": run.get("url", ""),
            "status": run.get("status", ""),
            "automationStatus": cycle.get("automationStatus") or run.get("automationStatus", ""),
            "outputDir": str(run_dir) if run_dir else str(run.get("outputDir", "")),
            "cycleReport": str(cycle_path) if cycle_path and cycle_path.exists() else "",
            "workflowManifest": str(manifest_path) if manifest_path and manifest_path.exists() else "",
            "product": run.get("product") or manifest.get("product") or {},
            "content": {
                "contentJson": artifact_path(artifacts.get("contentJson", "")),
                "publishPack": artifact_path(artifacts.get("publishPack", "")),
                "competitorInformedContent": artifact_path(artifacts.get("competitorInformedContent", "")),
                "competitorInformedStrategy": artifact_path(artifacts.get("competitorInformedStrategy", "")),
            },
            "competitorResearch": {
                "viralContentLibrary": artifact_path(artifacts.get("viralContentLibrary", "")),
                "creatorLeaderboard": artifact_path(artifacts.get("creatorLeaderboard", "")),
                "creatorFollowUpResults": artifact_path(artifacts.get("creatorFollowUpResults", "")),
                "deepCompetitorLibrary": artifact_path(artifacts.get("deepCompetitorLibrary", "")),
                "multiQueryViralDiscovery": run.get("multiQueryViralDiscovery", {}),
            },
            "videoGeneration": summarize_videos(videos),
            "publishQueue": summarize_section(cycle.get("publishQueue"), "queue"),
            "publishedItems": summarize_section(cycle.get("publishedItems"), "publishedItems"),
            "postPublishMetricsCapture": summarize_section(cycle.get("postPublishMetricsCapture"), "report", ["metricExport"]),
            "commentEvidenceCapture": summarize_section(cycle.get("commentEvidenceCapture"), "report", ["commentEvidenceExport"]),
            "businessAttribution": summarize_section(cycle.get("businessAttribution"), "report", ["businessAttributionExport"]),
            "metricsRecovery": summarize_section(cycle.get("metricsRecovery"), "metricsRecovery"),
            "nextRoundOptimization": summarize_section(cycle.get("nextRoundOptimization"), "report"),
        }
        item["evidenceCounts"] = evidence_counts(item)
        evidence.append(item)
    return evidence


def summarize_videos(videos: list[dict[str, Any]]) -> dict[str, Any]:
    generated = []
    for item in videos:
        video = str(item.get("video") or "").strip()
        if video and Path(video).exists():
            generated.append(video)
    return {
        "items": videos,
        "generatedFiles": generated,
        "generatedCount": len(generated),
        "statusCounts": count_statuses(videos),
    }


def summarize_section(value: Any, path_key: str, extra_path_keys: list[str] | None = None) -> dict[str, Any]:
    section = value if isinstance(value, dict) else {}
    report_path = artifact_path(section.get(path_key, ""))
    result = {
        "status": section.get("status", "missing" if not section else ""),
        "report": report_path,
        "exists": bool(report_path and Path(report_path).exists()),
        "summary": section.get("summary", {}) if isinstance(section.get("summary"), dict) else {},
    }
    for key in extra_path_keys or []:
        result[key] = artifact_path(section.get(key, ""))
    if section.get("reason"):
        result["reason"] = section.get("reason")
    return result


def evidence_counts(item: dict[str, Any]) -> dict[str, int]:
    post_metrics = item.get("postPublishMetricsCapture", {}).get("summary", {})
    comments = item.get("commentEvidenceCapture", {}).get("summary", {})
    business = item.get("businessAttribution", {}).get("summary", {})
    metrics = item.get("metricsRecovery", {}).get("summary", {})
    optimization = item.get("nextRoundOptimization", {}).get("summary", {})
    return {
        "capturedMetricRecords": int_value(post_metrics.get("capturedMetricRecords")),
        "commentCount": int_value(comments.get("commentCount") or optimization.get("commentCount")),
        "matchedBusinessRows": int_value(business.get("matchedRows") or optimization.get("businessAttributions")),
        "recordsWithMetrics": int_value(metrics.get("recordsWithMetrics")),
        "manualOrPendingRequirements": int_value(metrics.get("manualOrPendingRequirements"))
        + int_value(optimization.get("manualOrPendingRequirements")),
        "nextRoundContent": int_value(optimization.get("nextRoundContent")),
    }


def cycle_evidence_summary(cycle_evidence: list[dict[str, Any]]) -> dict[str, int]:
    counts = [item.get("evidenceCounts", {}) for item in cycle_evidence]
    return {
        "contentArtifacts": sum(1 for item in cycle_evidence if item.get("content", {}).get("contentJson")),
        "videoFilesGenerated": sum(int_value(item.get("videoGeneration", {}).get("generatedCount")) for item in cycle_evidence),
        "publishQueues": sum(1 for item in cycle_evidence if item.get("publishQueue", {}).get("exists")),
        "publishedItemsReports": sum(1 for item in cycle_evidence if item.get("publishedItems", {}).get("exists")),
        "postPublishMetricsCaptureRuns": sum(1 for item in cycle_evidence if item.get("postPublishMetricsCapture", {}).get("status") == "ready"),
        "commentEvidenceCaptureRuns": sum(1 for item in cycle_evidence if item.get("commentEvidenceCapture", {}).get("status") == "ready"),
        "businessAttributionRuns": sum(1 for item in cycle_evidence if item.get("businessAttribution", {}).get("status") == "ready"),
        "metricsRecoveryRuns": sum(1 for item in cycle_evidence if item.get("metricsRecovery", {}).get("status") == "ready"),
        "capturedMetricRecords": sum(int_value(item.get("capturedMetricRecords")) for item in counts),
        "commentCount": sum(int_value(item.get("commentCount")) for item in counts),
        "matchedBusinessRows": sum(int_value(item.get("matchedBusinessRows")) for item in counts),
        "recordsWithMetrics": sum(int_value(item.get("recordsWithMetrics")) for item in counts),
        "manualOrPendingRequirements": sum(int_value(item.get("manualOrPendingRequirements")) for item in counts),
        "nextRoundContent": sum(int_value(item.get("nextRoundContent")) for item in counts),
    }


def count_statuses(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def artifact_path(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    return text if text and Path(text).exists() else ""


def int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def final_status(
    batch: dict[str, Any],
    publish_readiness: list[dict[str, Any]],
    browser_publish: list[dict[str, Any]],
    audits: dict[str, Any],
) -> str:
    if batch.get("status") in {"blocked", "error", ""}:
        return "blocked"
    failed_readiness = any(item.get("status") == "error" for item in publish_readiness)
    failed_browser = any(item.get("status") == "error" for item in browser_publish)
    failed_audit = any(item.get("exitCode") not in {0, None} for item in audits.values())
    if failed_readiness or failed_browser or failed_audit:
        return "partial_ready_with_errors"
    if batch.get("status") == "ready" and publish_readiness:
        return "partial_ready"
    return "partial_ready"


def external_gates() -> list[dict[str, str]]:
    return [
        {"area": "official_publish", "gate": "I_APPROVE_PUBLISH plus platform credentials are required for writes."},
        {"area": "youtube", "gate": "OAuth client credentials or a temporary OAuth access token are required for upload."},
        {"area": "github", "gate": "GITHUB_TOKEN or GH_TOKEN is required for repository writes."},
        {"area": "douyin", "gate": "Approved open-platform app credentials, user authorization, and review are required."},
        {"area": "zhihu_xiaohongshu", "gate": "Manual/browser-assisted publishing remains required unless official creator publishing access is verified."},
        {"area": "metrics_revenue", "gate": "Private analytics, orders, and revenue require official APIs, screenshots, or business exports."},
        {"area": "self_evolution", "gate": "Installed Skill sync and dependency changes require explicit reviewed approval."},
    ]


def recommended_next_commands(out_dir: Path) -> list[dict[str, str]]:
    return [
        {
            "purpose": "review_batch_report",
            "command": f"open \"{out_dir / 'reports/promotion-manager/batch/product-batch-runner.md'}\"",
        },
        {
            "purpose": "prepare_browser_assisted_publish",
            "command": f"python scripts/browser_publish_assistant.py --publish-queue \"{out_dir}/product-batch-runs/<id>/reports/promotion-manager/publish-queue/publish-queue.json\" --out-dir \"{out_dir}/product-batch-runs/<id>\"",
        },
        {
            "purpose": "sync_installed_skill_when_approved",
            "command": "python scripts/self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC --out-dir \"./promotion-output\"",
        },
    ]


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = report_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "final-capability-run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / "final-capability-run.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Final Capability Run",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Output: {report['outDir']}",
        "",
        "## Summary",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## External Gates"])
    lines.extend(f"- {item['area']}: {item['gate']}" for item in report["externalGates"])
    lines.extend(["", "## Reports"])
    lines.append(f"- Product batch: {report['productBatch'].get('report', '')}")
    lines.extend(["", "## Cycle Evidence"])
    for item in report["cycleEvidence"]:
        counts = item.get("evidenceCounts", {})
        product = item.get("product") or {}
        lines.append(f"- {item.get('productRunId', '')}: {product.get('productName') or product.get('name') or 'unknown'}")
        lines.append(f"  Content: {item.get('content', {}).get('contentJson', '')}")
        lines.append(f"  Videos: {item.get('videoGeneration', {}).get('generatedCount', 0)} generated")
        lines.append(f"  Publish queue: `{item.get('publishQueue', {}).get('status', '')}` {item.get('publishQueue', {}).get('report', '')}")
        lines.append(
            "  Evidence: "
            f"metrics={counts.get('capturedMetricRecords', 0)}, "
            f"comments={counts.get('commentCount', 0)}, "
            f"businessRows={counts.get('matchedBusinessRows', 0)}, "
            f"nextRound={counts.get('nextRoundContent', 0)}"
        )
    for item in report["publishReadiness"]:
        lines.append(f"- Publish readiness ({item['productRunId']}): `{item['status']}` {item['report']}")
    for item in report["browserPublishAssistant"]:
        lines.append(f"- Browser publish ({item['productRunId']}): `{item['status']}` {item['report']}")
    for name, item in report["audits"].items():
        lines.append(f"- {name}: `{item['status']}` {item['report']}")
    lines.extend(["", "## Next Commands"])
    lines.extend(f"- {item['purpose']}: `{item['command']}`" for item in report["recommendedNextCommands"])
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def append_publish_args(command: list[str], args: argparse.Namespace) -> None:
    append_if_present(command, "--platforms", args.publish_platforms or args.platforms)
    append_if_present(command, "--github-repo", args.github_repo)
    append_if_present(command, "--github-path", args.github_path)
    append_if_present(command, "--youtube-video-file", args.youtube_video_file)
    append_if_present(command, "--douyin-video-file", args.douyin_video_file)


def run_command(name: str, command: list[str], check: bool = True) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    step = {
        "name": name,
        "command": display_command(command),
        "exitCode": result.returncode,
        "stdoutTail": tail(result.stdout),
        "stderrTail": tail(result.stderr),
    }
    if check and result.returncode != 0:
        raise SystemExit(f"{name} failed: {step['stderrTail'] or step['stdoutTail']}")
    return step


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def audit_report_path(name: str, out_dir: Path) -> Path:
    if name == "platform_access_audit":
        return out_dir / "reports/promotion-manager/platform-access/platform-access-audit.json"
    if name == "final_capability_audit":
        return out_dir / "reports/promotion-manager/capability/final-capability-audit.json"
    return out_dir / "reports/promotion-manager/self-evolution/self-evolution-audit.json"


def report_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/final-run"


def existing_path(value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.exists() else None


def existing_dir(value: Any) -> Path | None:
    path = existing_path(value)
    return path if path and path.is_dir() else None


def append_if_present(command: list[str], flag: str, value: Any) -> None:
    text = "" if value is None else str(value).strip()
    if text:
        command.extend([flag, text])


def append_many(command: list[str], flag: str, values: list[str]) -> None:
    for value in values:
        append_if_present(command, flag, value)


def display_command(command: list[str]) -> list[str]:
    return ["python" if item == sys.executable else item for item in command]


def tail(value: str, limit: int = 1200) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[-limit:]


def guardrails() -> list[str]:
    return [
        "Read product URLs before content generation and prefer browser-visible structured snapshots when available.",
        "Use public or official evidence for competitor research; do not bypass login, captcha, risk controls, or private endpoints.",
        "Prepare publish queues and browser-assisted payloads, but do not click final publish without explicit user action.",
        "Official writes require credentials and explicit I_APPROVE_PUBLISH approval.",
        "Use only real public/official/platform/business evidence for metrics, comments, orders, and revenue.",
        "Do not store cookies, passwords, API keys, OAuth tokens, or hidden browser tokens.",
    ]


if __name__ == "__main__":
    main()

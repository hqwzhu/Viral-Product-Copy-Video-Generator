#!/usr/bin/env python3
"""Run multiple product URLs through Codex-first intake and promotion cycles."""

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
PRODUCT_URL_READER = SCRIPTS / "product_url_reader.py"
PROMOTION_CYCLE_RUNNER = SCRIPTS / "promotion_cycle_runner.py"
MULTI_QUERY_VIRAL_DISCOVERY = SCRIPTS / "multi_query_viral_discovery.py"
TODAY = date.today().isoformat()
DEFAULT_PLATFORMS = "youtube,zhihu,xiaohongshu,douyin,github"


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []

    reader = run_product_url_reader(args, out_dir, steps)
    runs = run_promotion_cycles(args, out_dir, reader, steps)
    attach_multi_query_viral_discovery(args, runs, steps)
    report = build_report(args, out_dir, reader, runs, steps)
    write_report(out_dir, report)
    print(f"Product batch runner report written to: {(batch_dir(out_dir) / 'product-batch-runner.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read product URLs first, then run one promotion cycle per ready product.")
    parser.add_argument("--url", action="append", default=[], help="Product URL. Can be repeated.")
    parser.add_argument("--urls-file", default="", help="Text file with one product URL per line.")
    parser.add_argument("--out-dir", default="./promotion-output")

    reader = parser.add_argument_group("Codex/browser URL reading")
    reader.add_argument("--skip-browser", action="store_true")
    reader.add_argument("--no-static-fallback", action="store_true")
    reader.add_argument("--install-browser-if-missing", action="store_true")
    reader.add_argument("--timeout-ms", type=int, default=30000)
    reader.add_argument("--wait-until", default="networkidle", choices=["load", "domcontentloaded", "networkidle"])
    reader.add_argument("--screenshot", action="store_true")

    workflow = parser.add_argument_group("Promotion cycle")
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

    discovery = parser.add_argument_group("Multi-query viral discovery")
    discovery.add_argument("--run-multi-query-viral-discovery", action="store_true")
    discovery.add_argument("--multi-query-dry-run", action="store_true")
    discovery.add_argument("--multi-query-query", action="append", default=[])
    discovery.add_argument("--multi-query-query-count", type=int, default=5)
    discovery.add_argument("--multi-query-platforms", default="", help="Defaults to --platforms.")
    discovery.add_argument("--multi-query-top-n", type=int, default=20)
    discovery.add_argument("--multi-query-html-snapshot-root", default="")
    discovery.add_argument("--multi-query-live-official", action="store_true")
    discovery.add_argument("--multi-query-run-creator-follow-up", action="store_true")
    discovery.add_argument("--multi-query-creator-follow-up-dry-run", action="store_true")
    discovery.add_argument("--multi-query-run-follow-up-captures", action="store_true")
    discovery.add_argument("--multi-query-follow-up-dry-run", action="store_true")
    discovery.add_argument("--multi-query-capture-browser-assisted-follow-ups", action="store_true")

    publish = parser.add_argument_group("Publish queue")
    publish.add_argument("--skip-publish-queue", action="store_true")
    publish.add_argument("--publish-platforms", default="")
    publish.add_argument("--github-repo", default="")
    publish.add_argument("--github-path", default="PROMOTION.md")
    publish.add_argument("--youtube-video-file", default="")
    publish.add_argument("--douyin-video-file", default="")

    metrics = parser.add_argument_group("Metrics recovery")
    metrics.add_argument("--skip-metrics-recovery", action="store_true")
    metrics.add_argument("--published-url", action="append", default=[])
    metrics.add_argument("--business-csv", action="append", default=[])
    metrics.add_argument("--business-json", action="append", default=[])
    metrics.add_argument("--business-text", action="append", default=[])
    metrics.add_argument("--run-post-publish-metrics-capture", action="store_true")
    metrics.add_argument("--run-comment-evidence-capture", action="store_true")
    metrics.add_argument("--run-business-attribution", action="store_true")
    return parser.parse_args()


def run_product_url_reader(args: argparse.Namespace, out_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    command = [sys.executable, str(PRODUCT_URL_READER), "--out-dir", str(out_dir)]
    for url in args.url:
        command.extend(["--url", url])
    append_if_present(command, "--urls-file", args.urls_file)
    if args.skip_browser:
        command.append("--skip-browser")
    if args.no_static_fallback:
        command.append("--no-static-fallback")
    if args.install_browser_if_missing:
        command.append("--install-browser-if-missing")
    command.extend(["--timeout-ms", str(args.timeout_ms), "--wait-until", args.wait_until])
    if args.screenshot:
        command.append("--screenshot")

    step = run_command("product_url_reader", command)
    steps.append(step)
    report_path = out_dir / "reports/promotion-manager/intake/product-url-reader.json"
    if not report_path.exists():
        raise SystemExit(f"Product URL reader did not create {report_path}")
    report = read_json(report_path)
    report["_path"] = str(report_path)
    return report


def run_promotion_cycles(
    args: argparse.Namespace,
    out_dir: Path,
    reader: dict[str, Any],
    steps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runs = []
    for index, record in enumerate(reader.get("records", []), start=1):
        source = workflow_source(record)
        run_dir = out_dir / "product-batch-runs" / f"{index:03d}-{safe_id(record.get('id', 'product'))}"
        if not source:
            runs.append(blocked_run(record, run_dir, "No ready product profile or usable workflow source was available."))
            continue

        command = build_cycle_command(args, record, source, run_dir)
        step = run_command(f"promotion_cycle_{record.get('id', index)}", command, check=False)
        steps.append(step)
        runs.append(summarize_cycle_run(record, run_dir, source, step))
    return runs


def workflow_source(record: dict[str, Any]) -> dict[str, Any] | None:
    if (record.get("intake") or {}).get("status") != "ready":
        return None
    snapshot = Path(str((record.get("browser") or {}).get("snapshot", "")))
    if record.get("sourceMode") == "browser_structured_snapshot" and snapshot.exists():
        return {"flag": "--structured-json", "value": str(snapshot), "sourceMode": "browser_structured_snapshot"}
    url = str(record.get("url", "")).strip()
    if url:
        return {"flag": "--product-url", "value": url, "sourceMode": "static_url_fallback"}
    return None


def build_cycle_command(args: argparse.Namespace, record: dict[str, Any], source: dict[str, Any], run_dir: Path) -> list[str]:
    product = record.get("product") or {}
    command = [
        sys.executable,
        str(PROMOTION_CYCLE_RUNNER),
        source["flag"],
        source["value"],
        "--platforms",
        args.platforms,
        "--goal",
        args.goal,
        "--language",
        args.language,
        "--top-n",
        str(args.top_n),
        "--out-dir",
        str(run_dir),
    ]
    append_if_present(command, "--product-name", product.get("productName", ""))
    append_if_present(command, "--value-proposition", product.get("valueProposition", ""))
    append_if_present(command, "--pricing", product.get("pricing", ""))
    append_if_present(command, "--audience", join_list(product.get("targetAudienceAssumptions")))
    append_if_present(command, "--pain-points", join_list(product.get("painPointAssumptions")))
    append_if_present(command, "--competitor-query", args.competitor_query)
    if args.auto_search_competitors:
        command.append("--auto-search-competitors")
    if args.live_official_competitors:
        command.append("--live-official-competitors")
    if args.run_creator_follow_up:
        command.append("--run-creator-follow-up")
    if args.creator_follow_up_dry_run:
        command.append("--creator-follow-up-dry-run")
    if args.run_follow_up_captures:
        command.append("--run-follow-up-captures")
    if args.follow_up_dry_run:
        command.append("--follow-up-dry-run")
    if args.skip_video:
        command.append("--skip-video")
    append_if_present(command, "--video-platforms", args.video_platforms)
    if args.generate_voiceover:
        command.append("--generate-voiceover")
    if args.install_browser_if_missing:
        command.append("--install-browser-if-missing")

    if args.skip_publish_queue:
        command.append("--skip-publish-queue")
    append_if_present(command, "--publish-platforms", args.publish_platforms)
    append_if_present(command, "--github-repo", args.github_repo)
    append_if_present(command, "--github-path", args.github_path)
    append_if_present(command, "--youtube-video-file", args.youtube_video_file)
    append_if_present(command, "--douyin-video-file", args.douyin_video_file)

    if args.skip_metrics_recovery:
        command.append("--skip-metrics-recovery")
    append_many(command, "--published-url", args.published_url)
    append_many(command, "--business-csv", args.business_csv)
    append_many(command, "--business-json", args.business_json)
    append_many(command, "--business-text", args.business_text)
    if args.run_post_publish_metrics_capture:
        command.append("--run-post-publish-metrics-capture")
    if args.run_comment_evidence_capture:
        command.append("--run-comment-evidence-capture")
    if args.run_business_attribution:
        command.append("--run-business-attribution")
    return command


def summarize_cycle_run(record: dict[str, Any], run_dir: Path, source: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
    cycle_path = run_dir / "reports/promotion-manager/cycle/promotion-cycle.json"
    cycle = read_json(cycle_path)
    workflow_manifest = str((cycle.get("workflow") or {}).get("manifest") or run_dir / "reports/promotion-manager/agent-run/workflow-manifest.json")
    publish_queue = str((cycle.get("publishQueue") or {}).get("queue") or "")
    metrics_recovery = str((cycle.get("metricsRecovery") or {}).get("metricsRecovery") or "")
    return {
        "id": record.get("id", ""),
        "url": record.get("url", ""),
        "status": "ready" if step["exitCode"] == 0 and cycle_path.exists() else "error",
        "sourceMode": source["sourceMode"],
        "outputDir": str(run_dir),
        "cycleReport": str(cycle_path) if cycle_path.exists() else "",
        "workflowManifest": workflow_manifest if Path(workflow_manifest).exists() else "",
        "publishQueue": publish_queue if publish_queue and Path(publish_queue).exists() else "",
        "metricsRecovery": metrics_recovery if metrics_recovery and Path(metrics_recovery).exists() else "",
        "automationStatus": cycle.get("automationStatus", ""),
        "product": record.get("product", {}),
        "command": step["command"],
        "exitCode": step["exitCode"],
        "stdoutTail": step["stdoutTail"],
        "stderrTail": step["stderrTail"],
        "multiQueryViralDiscovery": {"status": "skipped", "reason": "--run-multi-query-viral-discovery was not supplied."},
    }


def blocked_run(record: dict[str, Any], run_dir: Path, reason: str) -> dict[str, Any]:
    return {
        "id": record.get("id", ""),
        "url": record.get("url", ""),
        "status": "blocked",
        "sourceMode": record.get("sourceMode", "unavailable"),
        "outputDir": str(run_dir),
        "cycleReport": "",
        "workflowManifest": "",
        "publishQueue": "",
        "metricsRecovery": "",
        "automationStatus": "",
        "product": record.get("product", {}),
        "reason": reason,
        "command": [],
        "exitCode": None,
        "multiQueryViralDiscovery": {"status": "skipped", "reason": "Promotion cycle was blocked."},
    }


def attach_multi_query_viral_discovery(args: argparse.Namespace, runs: list[dict[str, Any]], steps: list[dict[str, Any]]) -> None:
    if not args.run_multi_query_viral_discovery:
        return
    for run in runs:
        run["multiQueryViralDiscovery"] = run_multi_query_for_run(args, run, steps)


def run_multi_query_for_run(args: argparse.Namespace, run: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_path = Path(str(run.get("workflowManifest") or ""))
    run_dir = Path(str(run.get("outputDir") or ""))
    if run.get("status") != "ready" or not manifest_path.exists() or not run_dir:
        return {
            "status": "blocked",
            "reason": "A ready promotion cycle and workflow manifest are required before multi-query viral discovery.",
            "report": "",
            "mergedViralLibrary": "",
            "mergedCreatorLeaderboard": "",
            "command": [],
        }
    command = build_multi_query_command(args, manifest_path, run_dir)
    step = run_command(f"multi_query_viral_discovery_{run.get('id', 'product')}", command, check=False)
    steps.append(step)
    report_path = run_dir / "reports/promotion-manager/competitors/multi-query-viral-discovery.json"
    report = read_json(report_path)
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), dict) else {}
    return {
        "status": report.get("status", "error") if step["exitCode"] == 0 and report_path.exists() else "error",
        "report": str(report_path) if report_path.exists() else "",
        "mergedViralLibrary": str(artifacts.get("mergedViralLibrary", "")),
        "mergedCreatorLeaderboard": str(artifacts.get("mergedCreatorLeaderboard", "")),
        "summary": report.get("summary", {}),
        "command": step["command"],
        "exitCode": step["exitCode"],
        "stdoutTail": step["stdoutTail"],
        "stderrTail": step["stderrTail"],
    }


def build_multi_query_command(args: argparse.Namespace, manifest_path: Path, run_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(MULTI_QUERY_VIRAL_DISCOVERY),
        "--workflow-manifest",
        str(manifest_path),
        "--platforms",
        args.multi_query_platforms or args.platforms,
        "--top-n",
        str(args.multi_query_top_n),
        "--query-count",
        str(args.multi_query_query_count),
        "--out-dir",
        str(run_dir),
    ]
    append_many(command, "--query", args.multi_query_query)
    append_if_present(command, "--html-snapshot-root", args.multi_query_html_snapshot_root)
    if args.multi_query_dry_run:
        command.append("--dry-run")
    if args.install_browser_if_missing:
        command.append("--install-browser-if-missing")
    if args.multi_query_live_official:
        command.append("--live-official")
    if args.multi_query_run_creator_follow_up:
        command.append("--run-creator-follow-up")
    if args.multi_query_creator_follow_up_dry_run:
        command.append("--creator-follow-up-dry-run")
    if args.multi_query_run_follow_up_captures:
        command.append("--run-follow-up-captures")
    if args.multi_query_follow_up_dry_run:
        command.append("--follow-up-dry-run")
    if args.multi_query_capture_browser_assisted_follow_ups:
        command.append("--capture-browser-assisted-follow-ups")
    return command


def build_report(
    args: argparse.Namespace,
    out_dir: Path,
    reader: dict[str, Any],
    runs: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = {
        "requestedUrls": (reader.get("summary") or {}).get("requestedUrls", len(reader.get("records", []))),
        "readyProductProfiles": sum(1 for item in reader.get("records", []) if (item.get("intake") or {}).get("status") == "ready"),
        "blockedProductProfiles": sum(1 for item in reader.get("records", []) if (item.get("intake") or {}).get("status") != "ready"),
        "readyPromotionRuns": sum(1 for item in runs if item.get("status") == "ready"),
        "failedPromotionRuns": sum(1 for item in runs if item.get("status") == "error"),
        "blockedPromotionRuns": sum(1 for item in runs if item.get("status") == "blocked"),
        "browserStructuredRuns": sum(1 for item in runs if item.get("sourceMode") == "browser_structured_snapshot"),
        "staticFallbackRuns": sum(1 for item in runs if item.get("sourceMode") == "static_url_fallback"),
        "multiQueryDiscoveryRuns": sum(1 for item in runs if item.get("multiQueryViralDiscovery", {}).get("status") not in {"", "skipped", None}),
        "readyMultiQueryDiscoveryRuns": sum(1 for item in runs if item.get("multiQueryViralDiscovery", {}).get("status") == "ready"),
        "plannedMultiQueryDiscoveryRuns": sum(1 for item in runs if item.get("multiQueryViralDiscovery", {}).get("status") == "planned"),
        "failedMultiQueryDiscoveryRuns": sum(1 for item in runs if item.get("multiQueryViralDiscovery", {}).get("status") == "error"),
    }
    return {
        "generatedAt": TODAY,
        "status": batch_status(runs),
        "outDir": str(out_dir),
        "readerReport": reader.get("_path", ""),
        "input": {
            "urls": args.url,
            "urlsFile": args.urls_file,
            "platforms": args.platforms,
            "codexReadFirst": True,
        },
        "summary": summary,
        "readerSummary": reader.get("summary", {}),
        "promotionRuns": runs,
        "guardrails": [
            "Each product URL is read by product_url_reader.py before a promotion cycle starts.",
            "Browser structured snapshots are passed to promotion_cycle_runner.py with --structured-json when available.",
            "Static URL intake is used only when browser capture is skipped or unavailable and fallback is allowed.",
            "Multi-query viral discovery uses public/browser-visible platform evidence, official APIs, or dry-run query plans.",
            "Official publishing still requires explicit approval, credentials, and platform authorization.",
            "No login, captcha bypass, cookie extraction, hidden token storage, or fabricated metrics.",
        ],
        "steps": steps,
    }


def batch_status(runs: list[dict[str, Any]]) -> str:
    if not runs:
        return "blocked"
    cycle_statuses = [item.get("status") for item in runs]
    multi_statuses = [item.get("multiQueryViralDiscovery", {}).get("status") for item in runs]
    failed_multi = any(status in {"blocked", "error"} for status in multi_statuses)
    if all(status == "ready" for status in cycle_statuses) and not failed_multi:
        return "ready"
    if any(status == "ready" for status in cycle_statuses):
        return "partial_ready"
    return "blocked"


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = batch_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "product-batch-runner.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / "product-batch-runner.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Product Batch Runner",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Requested URLs: {report['summary']['requestedUrls']}",
        f"- Ready product profiles: {report['summary']['readyProductProfiles']}",
        f"- Ready promotion runs: {report['summary']['readyPromotionRuns']}",
        f"- Reader report: {report['readerReport']}",
        "",
        "## Promotion Runs",
    ]
    for run in report["promotionRuns"]:
        product = run.get("product") or {}
        lines.extend(
            [
                "",
                f"### {run.get('id', '')}",
                f"- Product: {product.get('productName', 'unknown')}",
                f"- URL: {run.get('url', '')}",
                f"- Status: `{run.get('status', '')}`",
                f"- Source mode: `{run.get('sourceMode', '')}`",
                f"- Cycle: {run.get('cycleReport', '')}",
                f"- Workflow manifest: {run.get('workflowManifest', '')}",
                f"- Automation status: `{run.get('automationStatus', '')}`",
                f"- Multi-query discovery: `{run.get('multiQueryViralDiscovery', {}).get('status', 'skipped')}` {run.get('multiQueryViralDiscovery', {}).get('report', '')}",
            ]
        )
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


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


def batch_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/batch"


def append_if_present(command: list[str], flag: str, value: Any) -> None:
    text = "" if value is None else str(value).strip()
    if text:
        command.extend([flag, text])


def append_many(command: list[str], flag: str, values: list[str]) -> None:
    for value in values:
        append_if_present(command, flag, value)


def join_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip() if value else ""


def safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.lower()).strip("-") or "product"


def display_command(command: list[str]) -> list[str]:
    return ["python" if item == sys.executable else item for item in command]


def tail(value: str, limit: int = 1200) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[-limit:]


if __name__ == "__main__":
    main()

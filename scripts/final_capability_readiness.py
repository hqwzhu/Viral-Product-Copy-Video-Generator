#!/usr/bin/env python3
"""Build an operator-facing final capability readiness matrix."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


TODAY = date.today().isoformat()
OBJECTIVE_REQUIREMENTS = [
    {
        "id": "product_url_codex_structured_intake",
        "label": "Codex reads every product URL and passes structured page evidence into product intake.",
    },
    {
        "id": "viral_creator_video_research",
        "label": "Search and capture viral creators, posts, repos, and video evidence across target platforms.",
    },
    {
        "id": "copy_and_real_video_generation",
        "label": "Generate platform-native copy, scripts, storyboards, and real MP4 video files.",
    },
    {
        "id": "official_or_browser_assisted_publish",
        "label": "Publish through official APIs where authorized, or browser/manual payloads where direct APIs are unavailable.",
    },
    {
        "id": "real_metrics_comments_orders_revenue",
        "label": "Recover real views, likes, comments, orders, revenue, and evidence-backed demand signals.",
    },
    {
        "id": "next_round_optimization",
        "label": "Use real evidence for retrospective, next-round hooks, scripts, and platform actions.",
    },
    {
        "id": "controlled_self_evolution",
        "label": "Audit tools, learn from official/public sources, install allowlisted runtimes, and sync the installed Skill only with approval.",
    },
]


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    sources = load_sources(args, out_dir)
    matrix = build_matrix(args, out_dir, sources)
    write_report(out_dir, matrix)
    print(f"Final capability readiness written to: {(report_dir(out_dir) / 'final-capability-readiness.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize final capability readiness from generated promotion manager reports.")
    parser.add_argument("--out-dir", default="./promotion-output")
    parser.add_argument("--final-run", default="", help="Path to final-capability-run.json.")
    parser.add_argument("--final-audit", default="", help="Path to final-capability-audit.json.")
    parser.add_argument("--platform-access-audit", default="", help="Path to platform-access-audit.json.")
    parser.add_argument("--self-evolution-audit", default="", help="Path to self-evolution-audit.json.")
    parser.add_argument("--publish-readiness", action="append", default=[], help="Path to a publish-readiness.json file. Can repeat.")
    parser.add_argument("--publish-setup", action="append", default=[], help="Path to a publish-setup.json file. Can repeat.")
    return parser.parse_args()


def load_sources(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    final_run_path = first_existing(
        [args.final_run, out_dir / "reports/promotion-manager/final-run/final-capability-run.json"]
    )
    final_audit_path = first_existing(
        [args.final_audit, out_dir / "reports/promotion-manager/capability/final-capability-audit.json"]
    )
    platform_access_path = first_existing(
        [args.platform_access_audit, out_dir / "reports/promotion-manager/platform-access/platform-access-audit.json"]
    )
    self_evolution_path = first_existing(
        [args.self_evolution_audit, out_dir / "reports/promotion-manager/self-evolution/self-evolution-audit.json"]
    )
    publish_readiness_paths = unique_paths(
        explicit_existing(args.publish_readiness)
        + glob_existing(out_dir, "reports/promotion-manager/publish-readiness/publish-readiness.json")
        + glob_existing(out_dir, "product-batch-runs/*/reports/promotion-manager/publish-readiness/publish-readiness.json")
    )
    publish_setup_paths = unique_paths(
        explicit_existing(args.publish_setup)
        + glob_existing(out_dir, "reports/promotion-manager/publish-setup/publish-setup.json")
        + glob_existing(out_dir, "product-batch-runs/*/reports/promotion-manager/publish-setup/publish-setup.json")
    )
    return {
        "finalRunPath": final_run_path,
        "finalAuditPath": final_audit_path,
        "platformAccessPath": platform_access_path,
        "selfEvolutionPath": self_evolution_path,
        "publishReadinessPaths": publish_readiness_paths,
        "publishSetupPaths": publish_setup_paths,
        "finalRun": read_json(final_run_path),
        "finalAudit": read_json(final_audit_path),
        "platformAccess": read_json(platform_access_path),
        "selfEvolution": read_json(self_evolution_path),
        "publishReadiness": [read_json(path) for path in publish_readiness_paths],
        "publishSetup": [read_json(path) for path in publish_setup_paths],
    }


def build_matrix(args: argparse.Namespace, out_dir: Path, sources: dict[str, Any]) -> dict[str, Any]:
    final_run = sources["finalRun"]
    final_audit = sources["finalAudit"]
    self_evolution = sources["selfEvolution"]
    readiness = sources["publishReadiness"]
    setup = sources["publishSetup"]
    rows = [
        product_intake_row(final_run, final_audit),
        viral_research_row(final_run, final_audit),
        copy_video_row(final_run, final_audit),
        publish_row(final_run, final_audit, readiness, setup),
        metrics_row(final_run, final_audit),
        optimization_row(final_run, final_audit),
        self_evolution_row(self_evolution, final_audit),
    ]
    action_queue = build_action_queue(out_dir, rows, final_run, final_audit, readiness, setup, self_evolution)
    summary = summarize(rows, action_queue)
    return {
        "generatedAt": TODAY,
        "status": final_status(rows),
        "outDir": str(out_dir),
        "sourceReports": source_report_summary(sources),
        "summary": summary,
        "requirements": rows,
        "platformMatrix": platform_matrix(final_audit, readiness),
        "externalGates": external_gates(rows),
        "actionQueue": action_queue,
        "operatingSequence": operating_sequence(out_dir),
        "guardrails": [
            "This matrix uses report status and evidence paths only; it never writes credential values.",
            "Official publishing still requires platform credentials, account authorization, and exact approval.",
            "Browser-assisted publishing must stop for login, captcha, risk checks, account verification, and final publish.",
            "Metrics, comments, orders, and revenue must come from public pages, official APIs, screenshots, structured snapshots, or business exports.",
            "Installed Skill sync and dependency changes remain reviewed actions; no silent self-replacement from network code.",
        ],
    }


def product_intake_row(final_run: dict[str, Any], final_audit: dict[str, Any]) -> dict[str, Any]:
    audit_item = requirement(final_audit, "product_url_structured_intake")
    summary = final_run.get("summary") if isinstance(final_run.get("summary"), dict) else {}
    product_batch = final_run.get("productBatch") if isinstance(final_run.get("productBatch"), dict) else {}
    codex_read = bool((final_run.get("input") or {}).get("codexReadFirst")) if isinstance(final_run.get("input"), dict) else False
    runs = int_value(summary.get("promotionRuns"))
    status = "ready"
    missing: list[str] = []
    if audit_item.get("status") not in {"ready"}:
        status = "partial_ready"
        missing.extend(audit_item.get("missing") or ["verified browser structured intake"])
    if final_run and (not codex_read or runs == 0):
        status = "needs_real_run_evidence"
        if not codex_read:
            missing.append("final run did not record codexReadFirst=true")
        if runs == 0:
            missing.append("no product promotion run evidence")
    evidence = audit_item.get("evidence") or []
    if product_batch.get("report"):
        evidence = list(evidence) + [product_batch["report"]]
    return row("product_url_codex_structured_intake", status, evidence, missing, [])


def viral_research_row(final_run: dict[str, Any], final_audit: dict[str, Any]) -> dict[str, Any]:
    audit_item = requirement(final_audit, "viral_creator_content_research")
    summary = final_run.get("summary") if isinstance(final_run.get("summary"), dict) else {}
    runs = int_value(summary.get("multiQueryDiscoveryRuns"))
    status = audit_item.get("status") or "unknown"
    missing: list[str] = []
    if final_run and runs == 0:
        status = "needs_real_run_evidence"
        missing.append("no multi-query viral discovery run evidence in the final run")
    return row(
        "viral_creator_video_research",
        status,
        audit_item.get("evidence") or [],
        missing or audit_item.get("missing") or [],
        audit_item.get("limits") or [],
    )


def copy_video_row(final_run: dict[str, Any], final_audit: dict[str, Any]) -> dict[str, Any]:
    audit_item = requirement(final_audit, "copy_and_real_video_generation")
    summary = final_run.get("summary") if isinstance(final_run.get("summary"), dict) else {}
    content_count = int_value(summary.get("contentArtifacts"))
    video_count = int_value(summary.get("videoFilesGenerated"))
    status = audit_item.get("status") or "unknown"
    missing: list[str] = []
    if final_run and content_count == 0:
        status = "needs_real_run_evidence"
        missing.append("no generated content artifact in the final run")
    if final_run and video_count == 0:
        status = "partial_ready"
        missing.append("no MP4 generated in the final run")
    return row("copy_and_real_video_generation", status, audit_item.get("evidence") or [], missing or audit_item.get("missing") or [], [])


def publish_row(
    final_run: dict[str, Any],
    final_audit: dict[str, Any],
    readiness_reports: list[dict[str, Any]],
    setup_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    audit_item = requirement(final_audit, "all_platform_auto_publish")
    readiness_records = [record for report in readiness_reports for record in list_records(report, "records")]
    setup_records = [record for report in setup_reports for record in list_records(report, "records")]
    ready_to_execute = sum(1 for item in readiness_records if item.get("readiness") == "ready_to_execute")
    dry_run_ready = sum(1 for item in readiness_records if item.get("readiness") == "dry_run_ready")
    manual_required = sum(
        1
        for item in readiness_records
        if item.get("readiness") in {"manual_publish_required", "browser_assisted_or_official_app_required"}
    )
    missing: list[str] = list(audit_item.get("missing") or [])
    if not readiness_records and final_run:
        missing.append("no publish readiness records generated")
    if not setup_records and final_run:
        missing.append("no publish setup kit generated")
    status = audit_item.get("status") or "unknown"
    if ready_to_execute or dry_run_ready:
        status = "partial_ready_external_approval_required"
    if manual_required:
        status = "partial_ready_browser_or_manual_required"
    return row(
        "official_or_browser_assisted_publish",
        status,
        audit_item.get("evidence") or [],
        ordered_unique(missing),
        audit_item.get("limits") or [],
        {
            "readinessRecords": len(readiness_records),
            "setupRecords": len(setup_records),
            "readyToExecute": ready_to_execute,
            "dryRunReady": dry_run_ready,
            "manualOrBrowserRequired": manual_required,
        },
    )


def metrics_row(final_run: dict[str, Any], final_audit: dict[str, Any]) -> dict[str, Any]:
    audit_item = requirement(final_audit, "real_metrics_orders_revenue_recovery")
    summary = final_run.get("summary") if isinstance(final_run.get("summary"), dict) else {}
    evidence_count = (
        int_value(summary.get("capturedMetricRecords"))
        + int_value(summary.get("commentCount"))
        + int_value(summary.get("matchedBusinessRows"))
        + int_value(summary.get("recordsWithMetrics"))
    )
    status = audit_item.get("status") or "unknown"
    missing = list(audit_item.get("missing") or [])
    if final_run and evidence_count == 0:
        status = "waiting_real_data"
        missing.append("no real metrics, comments, business rows, or recovered metric records in final run")
    return row("real_metrics_comments_orders_revenue", status, audit_item.get("evidence") or [], ordered_unique(missing), audit_item.get("limits") or [])


def optimization_row(final_run: dict[str, Any], final_audit: dict[str, Any]) -> dict[str, Any]:
    audit_item = requirement(final_audit, "retrospective_next_round_optimization")
    summary = final_run.get("summary") if isinstance(final_run.get("summary"), dict) else {}
    next_count = int_value(summary.get("nextRoundContent"))
    status = audit_item.get("status") or "unknown"
    missing: list[str] = []
    if final_run and next_count == 0:
        status = "waiting_real_data"
        missing.append("no next-round content was generated from real evidence")
    return row("next_round_optimization", status, audit_item.get("evidence") or [], missing or audit_item.get("missing") or [], audit_item.get("limits") or [])


def self_evolution_row(self_evolution: dict[str, Any], final_audit: dict[str, Any]) -> dict[str, Any]:
    audit_item = requirement(final_audit, "fully_autonomous_self_evolution")
    installed = self_evolution.get("installedSkill") if isinstance(self_evolution.get("installedSkill"), dict) else {}
    missing = list(audit_item.get("missing") or [])
    if installed.get("status") == "drift_detected":
        missing.append("installed Codex Skill is drifted from the reviewed repository")
    status = audit_item.get("status") or self_evolution.get("status") or "unknown"
    return row(
        "controlled_self_evolution",
        status,
        audit_item.get("evidence") or [],
        ordered_unique(missing),
        audit_item.get("limits") or [],
        {
            "installedSkillStatus": installed.get("status", ""),
            "syncCommand": installed.get("syncCommand", ""),
            "repositoryClean": bool((self_evolution.get("repository") or {}).get("clean")),
        },
    )


def row(
    requirement_id: str,
    status: str,
    evidence: list[Any],
    missing: list[Any],
    limits: list[Any],
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    definition = next(item for item in OBJECTIVE_REQUIREMENTS if item["id"] == requirement_id)
    blocked = status.startswith("blocked") or status in {"waiting_real_data", "needs_real_run_evidence"}
    return {
        "id": requirement_id,
        "label": definition["label"],
        "status": status or "unknown",
        "satisfied": status in {"ready", "full_ready"},
        "blocked": blocked,
        "evidence": [str(item) for item in evidence if item],
        "missing": [str(item) for item in missing if item],
        "limits": [str(item) for item in limits if item],
        "metrics": metrics or {},
    }


def build_action_queue(
    out_dir: Path,
    rows: list[dict[str, Any]],
    final_run: dict[str, Any],
    final_audit: dict[str, Any],
    readiness_reports: list[dict[str, Any]],
    setup_reports: list[dict[str, Any]],
    self_evolution: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    by_id = {item["id"]: item for item in rows}
    if by_id["product_url_codex_structured_intake"]["status"] == "needs_real_run_evidence":
        actions.append(action(10, "run_product_url_reading", "Run final capability runner on a real product URL.", final_runner_command(out_dir)))
    if by_id["viral_creator_video_research"]["status"] == "needs_real_run_evidence":
        actions.append(
            action(
                20,
                "run_multi_query_viral_discovery",
                "Run product-driven viral discovery and follow-up captures.",
                final_runner_command(out_dir) + " --run-follow-up-captures --sample-video-frames",
            )
        )
    if "no MP4 generated" in " ".join(by_id["copy_and_real_video_generation"]["missing"]):
        actions.append(action(30, "render_video", "Run without --skip-video or provide a voiceover file for MP4 rendering.", final_runner_command(out_dir)))
    publish_status = by_id["official_or_browser_assisted_publish"]["status"]
    if publish_status.startswith("partial_ready"):
        actions.extend(publish_actions(out_dir, readiness_reports, setup_reports))
    if publish_status.startswith("blocked") and not readiness_reports:
        actions.append(
            action(
                40,
                "build_publish_readiness_after_workflow",
                "After a real workflow manifest exists, build the guarded publish queue and setup kit.",
                (
                    f"python scripts/publish_readiness_runner.py --workflow-manifest "
                    f"\"{out_dir}/reports/promotion-manager/agent-run/workflow-manifest.json\" "
                    f"--build-queue --github-repo owner/repo --youtube-video-file \"{out_dir}/videos/product-youtube.mp4\" "
                    f"--douyin-video-file \"{out_dir}/videos/product-douyin.mp4\" --out-dir \"{out_dir}\""
                ),
            )
        )
    if by_id["real_metrics_comments_orders_revenue"]["status"] == "waiting_real_data":
        actions.append(
            action(
                60,
                "register_real_published_urls",
                "Register real published URLs or evidence before metrics recovery.",
                f"python scripts/published_items.py --platform xiaohongshu --published-url \"https://...\" --evidence \"./screenshots/published.png\" --out-dir \"{out_dir}\"",
            )
        )
        actions.append(
            action(
                61,
                "import_business_exports",
                "Provide business exports with URL, UTM, content id, orders, revenue, clicks, or leads.",
                f"python scripts/business_attribution.py --business-csv \"./orders-and-revenue.csv\" --out-dir \"{out_dir}\"",
            )
        )
    if by_id["next_round_optimization"]["status"] == "waiting_real_data":
        actions.append(
            action(
                70,
                "optimize_after_real_evidence",
                "Run next-round optimization after metrics, comments, or business attribution exist.",
                f"python scripts/next_round_optimizer.py --metrics-recovery-json \"{out_dir}/reports/promotion-manager/metrics-recovery/metrics-recovery.json\" --out-dir \"{out_dir}\"",
            )
        )
    installed = self_evolution.get("installedSkill") if isinstance(self_evolution.get("installedSkill"), dict) else {}
    if installed.get("status") == "drift_detected":
        actions.append(
            action(
                80,
                "sync_installed_skill_when_approved",
                "Sync reviewed repository files into the installed Codex Skill after explicit approval.",
                installed.get("syncCommand") or "python scripts/self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC --out-dir \"./promotion-output\"",
                approval="I_APPROVE_SKILL_SYNC",
            )
        )
    for item in final_audit.get("nextActions", []) if isinstance(final_audit.get("nextActions"), list) else []:
        if isinstance(item, dict) and item.get("command"):
            actions.append(action(90 + int_value(item.get("priority")), str(item.get("area", "audit_next_action")), str(item.get("action", "")), str(item.get("command", ""))))
    return dedupe_actions(sorted(actions, key=lambda item: item["priority"]))


def publish_actions(out_dir: Path, readiness_reports: list[dict[str, Any]], setup_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for report in setup_reports:
        for record in list_records(report, "records"):
            commands = record.get("commands") if isinstance(record.get("commands"), dict) else {}
            category = record.get("setupCategory", "")
            platform = record.get("platform", "")
            if commands.get("rerunReadiness"):
                actions.append(action(40, f"rerun_{platform}_publish_readiness", f"Rerun {platform} publish readiness after setup changes.", commands["rerunReadiness"]))
            if commands.get("executeWhenReady") and category in {"execution_approval_required", "ready_to_execute", "credential_setup_required"}:
                actions.append(action(50, f"execute_{platform}_when_approved", f"Execute {platform} only after credentials, target, and approval are ready.", commands["executeWhenReady"], approval="I_APPROVE_PUBLISH"))
            if commands.get("prepareBrowserPublish"):
                actions.append(action(51, f"prepare_{platform}_browser_publish", f"Prepare browser/manual publish payloads for {platform}.", commands["prepareBrowserPublish"]))
    if not actions and readiness_reports:
        actions.append(action(40, "build_publish_setup_kit", "Build publish setup kit from readiness reports.", f"python scripts/publish_setup_assistant.py --out-dir \"{out_dir}\""))
    return actions


def action(priority: int, action_id: str, description: str, command: str, approval: str = "") -> dict[str, Any]:
    return {
        "priority": priority,
        "id": action_id,
        "description": description,
        "command": command,
        "approvalRequired": approval,
    }


def summarize(rows: list[dict[str, Any]], actions: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "requirements": len(rows),
        "satisfied": sum(1 for item in rows if item["satisfied"]),
        "blockedOrWaiting": sum(1 for item in rows if item["blocked"]),
        "partial": sum(1 for item in rows if item["status"].startswith("partial")),
        "actions": len(actions),
        "approvalActions": sum(1 for item in actions if item.get("approvalRequired")),
    }
    return summary


def final_status(rows: list[dict[str, Any]]) -> str:
    statuses = {item["status"] for item in rows}
    if all(item["satisfied"] for item in rows):
        return "full_ready"
    if any(status.startswith("blocked") for status in statuses):
        return "partial_ready_blocked_by_platform_or_safety_limits"
    if any(status in {"waiting_real_data", "needs_real_run_evidence"} for status in statuses):
        return "partial_ready_waiting_external_evidence"
    return "partial_ready"


def platform_matrix(final_audit: dict[str, Any], readiness_reports: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = {}
    platforms = final_audit.get("platforms") if isinstance(final_audit.get("platforms"), dict) else {}
    for platform, info in platforms.items():
        matrix[platform] = dict(info) if isinstance(info, dict) else {"status": info}
    for report in readiness_reports:
        for record in list_records(report, "records"):
            platform = str(record.get("platform") or "")
            if not platform:
                continue
            matrix.setdefault(platform, {})
            matrix[platform]["publishReadiness"] = record.get("readiness", "")
            matrix[platform]["publishMode"] = record.get("publishMode", "")
    return matrix


def external_gates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for item in rows:
        if item["missing"] or item["limits"]:
            gates.append(
                {
                    "requirement": item["id"],
                    "status": item["status"],
                    "missing": item["missing"],
                    "limits": item["limits"],
                }
            )
    return gates


def operating_sequence(out_dir: Path) -> list[dict[str, str]]:
    return [
        {
            "step": "run_final_capability",
            "command": final_runner_command(out_dir),
        },
        {
            "step": "review_readiness_matrix",
            "command": f"python scripts/final_capability_readiness.py --out-dir \"{out_dir}\"",
        },
        {
            "step": "prepare_publish_setup",
            "command": f"python scripts/publish_setup_assistant.py --out-dir \"{out_dir}\"",
        },
        {
            "step": "prepare_browser_publish",
            "command": f"python scripts/browser_publish_assistant.py --publish-queue \"{out_dir}/reports/promotion-manager/publish-queue/publish-queue.json\" --out-dir \"{out_dir}\"",
        },
        {
            "step": "recover_real_metrics",
            "command": f"python scripts/metrics_recovery.py --out-dir \"{out_dir}\"",
        },
        {
            "step": "optimize_next_round",
            "command": f"python scripts/next_round_optimizer.py --metrics-recovery-json \"{out_dir}/reports/promotion-manager/metrics-recovery/metrics-recovery.json\" --out-dir \"{out_dir}\"",
        },
    ]


def final_runner_command(out_dir: Path) -> str:
    return (
        "python scripts/final_capability_runner.py --url \"https://example.com/product\" "
        "--platforms youtube,zhihu,xiaohongshu,douyin,github --run-follow-up-captures "
        "--sample-video-frames --business-csv \"./orders-and-revenue.csv\" "
        f"--out-dir \"{out_dir}\""
    )


def source_report_summary(sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "finalRun": report_source(sources.get("finalRunPath")),
        "finalAudit": report_source(sources.get("finalAuditPath")),
        "platformAccess": report_source(sources.get("platformAccessPath")),
        "selfEvolution": report_source(sources.get("selfEvolutionPath")),
        "publishReadiness": [report_source(path) for path in sources.get("publishReadinessPaths", [])],
        "publishSetup": [report_source(path) for path in sources.get("publishSetupPaths", [])],
    }


def report_source(path: Path | None) -> dict[str, Any]:
    return {"path": str(path) if path else "", "exists": bool(path and path.exists())}


def requirement(final_audit: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    for item in final_audit.get("requirements", []) if isinstance(final_audit.get("requirements"), list) else []:
        if isinstance(item, dict) and item.get("id") == requirement_id:
            return item
    return {"id": requirement_id, "status": "unknown", "missing": ["final capability audit requirement missing"]}


def list_records(report: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [item for item in report.get(key, []) if isinstance(item, dict)] if isinstance(report, dict) else []


def first_existing(values: list[Any]) -> Path | None:
    for value in values:
        if not value:
            continue
        path = Path(value)
        if path.exists():
            return path
    return None


def explicit_existing(values: list[str]) -> list[Path]:
    return [Path(value) for value in values if value and Path(value).exists()]


def glob_existing(base: Path, pattern: str) -> list[Path]:
    return sorted(path for path in base.glob(pattern) if path.exists())


def unique_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.resolve())
        if key not in seen:
            result.append(path)
            seen.add(key)
    return result


def read_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def ordered_unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def dedupe_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in actions:
        key = (str(item.get("id", "")), str(item.get("command", "")))
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result


def int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = report_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "final-capability-readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (directory / "final-capability-readiness.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Final Capability Readiness",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Output: {report['outDir']}",
        "",
        "## Requirements",
    ]
    for item in report["requirements"]:
        lines.append(f"- `{item['id']}`: `{item['status']}` - {item['label']}")
        if item.get("missing"):
            lines.append(f"  Missing: {', '.join(item['missing'])}")
    lines.extend(["", "## Action Queue"])
    for item in report["actionQueue"]:
        approval = f" approval=`{item['approvalRequired']}`" if item.get("approvalRequired") else ""
        lines.append(f"- P{item['priority']} `{item['id']}`{approval}: {item['description']}")
        lines.append(f"  Command: `{item['command']}`")
    lines.extend(["", "## Platform Matrix"])
    for platform, info in report["platformMatrix"].items():
        lines.append(f"- {platform}: {json.dumps(info, ensure_ascii=False, sort_keys=True)}")
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def report_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/final-readiness"


if __name__ == "__main__":
    main()

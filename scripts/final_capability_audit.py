#!/usr/bin/env python3
"""Audit final-agent readiness for the viral product promotion skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TODAY = date.today().isoformat()
SAFE_INSTALLS = {"playwright_chromium"}


SCRIPT_REQUIREMENTS = {
    "browser_snapshot": "browser_snapshot.py",
    "product_intake": "product_intake.py",
    "run_workflow": "run_promotion_workflow.py",
    "platform_search_browser": "platform_search_browser.py",
    "platform_search_capture": "platform_search_capture.py",
    "viral_content_library": "viral_content_library.py",
    "creator_leaderboard": "creator_leaderboard.py",
    "creator_follow_up_runner": "creator_follow_up_runner.py",
    "follow_up_capture_runner": "follow_up_capture_runner.py",
    "competitor_content_enhancer": "competitor_content_enhancer.py",
    "render_video": "render_video.py",
    "publish_queue": "publish_queue.py",
    "publish_executor": "publish_executor.py",
    "youtube_oauth_publish": "youtube_oauth_publish.py",
    "published_items": "published_items.py",
    "publish_url_capture": "publish_url_capture.py",
    "metrics_intake": "metrics_intake.py",
    "metrics_recovery": "metrics_recovery.py",
    "automation_scheduler": "automation_scheduler.py",
    "promotion_cycle_runner": "promotion_cycle_runner.py",
}


CREDENTIALS = {
    "youtube_search_metrics": ["YOUTUBE_API_KEY"],
    "youtube_oauth_upload": ["YOUTUBE_OAUTH_ACCESS_TOKEN"],
    "youtube_oauth_flow": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
    "github_write": ["GITHUB_TOKEN", "GH_TOKEN"],
    "tiktok_direct_post": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN", "TIKTOK_OPEN_ID"],
    "douyin_publish": ["DOUYIN_CLIENT_KEY", "DOUYIN_CLIENT_SECRET", "DOUYIN_ACCESS_TOKEN", "DOUYIN_OPEN_ID"],
}


OFFICIAL_SOURCES = [
    {
        "platform": "youtube",
        "capability": "upload",
        "url": "https://developers.google.com/youtube/v3/docs/videos/insert",
        "notes": "Official videos.insert upload endpoint; OAuth scope, quota, and audit restrictions apply.",
    },
    {
        "platform": "github",
        "capability": "repository_content_write",
        "url": "https://docs.github.com/en/rest/repos/contents",
        "notes": "Official create/update file contents endpoint; write permissions are required.",
    },
    {
        "platform": "tiktok",
        "capability": "direct_post",
        "url": "https://developers.tiktok.com/doc/content-posting-api-get-started/",
        "notes": "Direct Post requires app product setup, video.publish approval, creator authorization, and audit for public visibility.",
    },
    {
        "platform": "douyin",
        "capability": "publishing_candidate",
        "url": "https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution",
        "notes": "Official open-platform publishing path requires app permission approval and user authorization.",
    },
    {
        "platform": "xiaohongshu",
        "capability": "open_platform_docs",
        "url": "https://open.xiaohongshu.com/document/api",
        "notes": "Treat general note publishing as manual/browser-assisted unless official creator publishing access is verified.",
    },
]


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.install_safe_missing_tools:
        install_safe_missing_tools(args)
    report = build_report(args, out_dir)
    write_report(out_dir, report)
    print(f"Final capability audit written to: {(audit_dir(out_dir) / 'final-capability-audit.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit final capability readiness for the product promotion Skill.")
    parser.add_argument("--out-dir", default="./promotion-output")
    parser.add_argument(
        "--skip-runtime-checks",
        action="store_true",
        help="Skip slower runtime launch checks such as Playwright Chromium launch.",
    )
    parser.add_argument(
        "--install-safe-missing-tools",
        action="store_true",
        help="Install only allowlisted official runtime tools that are missing.",
    )
    parser.add_argument(
        "--safe-install",
        action="append",
        default=[],
        choices=sorted(SAFE_INSTALLS),
        help="Allowlisted runtime install to attempt when --install-safe-missing-tools is supplied.",
    )
    return parser.parse_args()


def install_safe_missing_tools(args: argparse.Namespace) -> None:
    installs = set(args.safe_install or [])
    if not installs:
        installs = {"playwright_chromium"}
    unsupported = installs - SAFE_INSTALLS
    if unsupported:
        raise SystemExit(f"Unsupported safe installs: {', '.join(sorted(unsupported))}")
    if "playwright_chromium" in installs and not playwright_chromium_available(skip_runtime_checks=False):
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], cwd=ROOT, check=False)


def build_report(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    scripts = script_status()
    tools = tool_status(skip_runtime_checks=args.skip_runtime_checks)
    credentials = credential_status()
    platforms = platform_status(scripts, tools, credentials)
    requirements = requirement_status(scripts, tools, credentials, platforms)
    actions = next_actions(requirements, tools, credentials, out_dir)
    return {
        "generatedAt": TODAY,
        "root": str(ROOT),
        "outDir": str(out_dir),
        "finalStatus": final_status(requirements),
        "requirements": requirements,
        "platforms": platforms,
        "localTools": tools,
        "credentials": credentials,
        "scripts": scripts,
        "selfEvolution": self_evolution_status(tools),
        "recommendedCommands": recommended_commands(out_dir),
        "nextActions": actions,
        "officialSources": OFFICIAL_SOURCES,
        "guardrails": [
            "Do not auto-login, bypass captcha, use private endpoints, or extract browser cookies/tokens.",
            "Do not print or write credential values; only credential presence is recorded.",
            "Do not claim published content until a real official execution report or published URL exists.",
            "Do not claim platform metrics, orders, or revenue unless official APIs, exports, screenshots, or business data prove them.",
            "Self-evolution may audit, learn, and install explicit allowlisted runtime dependencies, but it must not silently replace itself from unreviewed network code.",
        ],
    }


def script_status() -> dict[str, dict[str, Any]]:
    status = {}
    for key, filename in SCRIPT_REQUIREMENTS.items():
        path = SCRIPTS / filename
        status[key] = {"file": str(path), "exists": path.exists()}
    return status


def tool_status(skip_runtime_checks: bool) -> dict[str, dict[str, Any]]:
    return {
        "python": {
            "available": True,
            "version": sys.version.split()[0],
            "path": sys.executable,
        },
        "git": command_status("git"),
        "ffmpeg": command_status("ffmpeg"),
        "playwright": python_module_status("playwright"),
        "playwrightChromium": {
            "available": playwright_chromium_available(skip_runtime_checks),
            "checked": not skip_runtime_checks,
            "installCommand": "python -m playwright install chromium",
        },
    }


def command_status(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    return {"available": bool(path), "path": path or ""}


def python_module_status(name: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-c", f"import {name}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return {"available": result.returncode == 0, "module": name}


def playwright_chromium_available(skip_runtime_checks: bool) -> bool:
    if skip_runtime_checks:
        return False
    code = (
        "from playwright.sync_api import sync_playwright\n"
        "p=sync_playwright().start()\n"
        "b=p.chromium.launch(headless=True)\n"
        "b.close()\n"
        "p.stop()\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def credential_status() -> dict[str, dict[str, Any]]:
    status = {}
    for capability, names in CREDENTIALS.items():
        present = [name for name in names if bool(os.environ.get(name))]
        status[capability] = {
            "requiredEnv": names,
            "presentEnv": present,
            "ready": bool(present) if len(names) == 1 else all(name in present for name in names),
            "valuesStored": False,
        }
    status["business_exports"] = {
        "requiredEvidence": ["business CSV/JSON/text export with orders, revenue, clicks, or leads"],
        "ready": False,
        "valuesStored": False,
    }
    return status


def platform_status(
    scripts: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    credentials: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    browser_ready = bool(tools["playwright"]["available"]) and (
        bool(tools["playwrightChromium"]["available"]) or not tools["playwrightChromium"]["checked"]
    )
    shared_browser_search = scripts_ready(scripts, ["platform_search_browser", "platform_search_capture", "viral_content_library"])
    return {
        "youtube": {
            "viralSearch": status_value(scripts_ready(scripts, ["competitor_collector"]) or (shared_browser_search and browser_ready)),
            "directPublish": "ready" if credentials["youtube_oauth_upload"]["ready"] else "needs_oauth_or_access_token",
            "metricsRecovery": "ready" if credentials["youtube_search_metrics"]["ready"] else "needs_youtube_api_key",
            "ordersRevenue": "business_export_required",
        },
        "github": {
            "viralSearch": status_value(scripts_ready(scripts, ["competitor_collector"])),
            "directPublish": "ready" if credentials["github_write"]["ready"] else "needs_github_token",
            "metricsRecovery": "ready_public_repo_metrics",
            "ordersRevenue": "business_export_required",
        },
        "zhihu": {
            "viralSearch": "browser_visible_ready" if shared_browser_search and browser_ready else "browser_runtime_required",
            "directPublish": "manual_or_browser_assisted_only",
            "metricsRecovery": "manual_export_required",
            "ordersRevenue": "business_export_required",
        },
        "xiaohongshu": {
            "viralSearch": "browser_visible_ready" if shared_browser_search and browser_ready else "browser_runtime_required",
            "directPublish": "manual_or_browser_assisted_only",
            "metricsRecovery": "manual_export_required",
            "ordersRevenue": "business_export_required",
        },
        "douyin": {
            "viralSearch": "browser_visible_ready" if shared_browser_search and browser_ready else "browser_runtime_required",
            "directPublish": "official_app_authorization_required"
            if credentials["douyin_publish"]["ready"]
            else "browser_assisted_until_official_access_verified",
            "metricsRecovery": "manual_or_official_export_required",
            "ordersRevenue": "business_export_required",
        },
        "tiktok": {
            "viralSearch": "browser_visible_ready" if shared_browser_search and browser_ready else "browser_runtime_required",
            "directPublish": "official_app_authorization_required"
            if credentials["tiktok_direct_post"]["ready"]
            else "developer_app_scope_and_creator_auth_required",
            "metricsRecovery": "manual_or_official_export_required",
            "ordersRevenue": "business_export_required",
        },
    }


def requirement_status(
    scripts: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    credentials: dict[str, dict[str, Any]],
    platforms: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    browser_intake_ready = scripts_ready(scripts, ["browser_snapshot", "product_intake", "run_workflow"])
    browser_runtime_ready = bool(tools["playwright"]["available"]) and (
        bool(tools["playwrightChromium"]["available"]) or not tools["playwrightChromium"]["checked"]
    )
    video_scripts_ready = scripts_ready(scripts, ["render_video"])
    video_ready = video_scripts_ready and bool(tools["ffmpeg"]["available"])
    search_ready = scripts_ready(
        scripts,
        [
            "platform_search_browser",
            "platform_search_capture",
            "viral_content_library",
            "creator_leaderboard",
            "creator_follow_up_runner",
            "follow_up_capture_runner",
        ],
    )
    publish_ready = scripts_ready(scripts, ["publish_queue", "publish_executor", "youtube_oauth_publish"])
    metrics_ready = scripts_ready(scripts, ["published_items", "publish_url_capture", "metrics_intake", "metrics_recovery"])
    cycle_ready = scripts_ready(scripts, ["promotion_cycle_runner", "automation_scheduler"])
    full_platform_publish_ready = all(
        platforms[p]["directPublish"] == "ready" for p in ["youtube", "github", "zhihu", "xiaohongshu", "douyin"]
    )
    real_metrics_ready = metrics_ready and (
        credentials["youtube_search_metrics"]["ready"] or credentials["github_write"]["ready"]
    )

    return [
        {
            "id": "product_url_structured_intake",
            "label": "Automatically parse product URLs through Codex/browser structured snapshots",
            "status": "ready" if browser_intake_ready and browser_runtime_ready else "partial_ready",
            "evidence": scripts_present(scripts, ["browser_snapshot", "product_intake", "run_workflow"]),
            "missing": missing_for_scripts(scripts, ["browser_snapshot", "product_intake", "run_workflow"])
            + ([] if browser_runtime_ready else ["Playwright Chromium runtime not verified"]),
        },
        {
            "id": "viral_creator_content_research",
            "label": "Search and capture viral creators/content across YouTube, Zhihu, Xiaohongshu, Douyin, and GitHub",
            "status": "partial_ready" if search_ready else "not_ready",
            "evidence": scripts_present(
                scripts,
                [
                    "platform_search_browser",
                    "platform_search_capture",
                    "viral_content_library",
                    "creator_leaderboard",
                    "creator_follow_up_runner",
                    "follow_up_capture_runner",
                ],
            ),
            "missing": [] if search_ready else ["search/capture/ranking scripts"],
            "limits": [
                "YouTube and GitHub can use official/public connectors.",
                "Zhihu, Xiaohongshu, Douyin, and TikTok require browser-visible evidence or official access; no private endpoint or anti-bot bypass is allowed.",
            ],
        },
        {
            "id": "copy_and_real_video_generation",
            "label": "Generate real copy, scripts, storyboards, and MP4 video files",
            "status": "ready" if video_ready else "partial_ready",
            "evidence": scripts_present(scripts, ["competitor_content_enhancer", "render_video"]),
            "missing": [] if video_ready else ["ffmpeg runtime"] if video_scripts_ready else ["render_video.py"],
        },
        {
            "id": "all_platform_auto_publish",
            "label": "Automatically publish to YouTube, Zhihu, Xiaohongshu, Douyin, and GitHub",
            "status": "ready" if publish_ready and full_platform_publish_ready else "blocked_by_authorization_or_platform_limits",
            "evidence": scripts_present(scripts, ["publish_queue", "publish_executor", "youtube_oauth_publish"]),
            "missing": missing_publish_credentials(credentials),
            "limits": [
                "GitHub and YouTube writes require official credentials plus explicit publish approval.",
                "Zhihu and Xiaohongshu remain manual/browser-assisted unless official creator publishing access is verified.",
                "Douyin/TikTok require approved open-platform apps, scopes, and user authorization.",
            ],
        },
        {
            "id": "real_metrics_orders_revenue_recovery",
            "label": "Recover real views, likes, comments, orders, revenue, and business outcomes",
            "status": "partial_ready" if metrics_ready else "not_ready",
            "evidence": scripts_present(scripts, ["published_items", "publish_url_capture", "metrics_intake", "metrics_recovery"]),
            "missing": [] if real_metrics_ready else ["published URLs, official metrics credentials, or business exports"],
            "limits": [
                "Social metrics require official APIs, public pages, screenshots, or exports.",
                "Orders and revenue require business-system exports; public platform pages cannot prove revenue.",
            ],
        },
        {
            "id": "periodic_codex_operation",
            "label": "Run the whole promotion loop periodically in Codex/local automation",
            "status": "ready" if cycle_ready else "not_ready",
            "evidence": scripts_present(scripts, ["promotion_cycle_runner", "automation_scheduler"]),
            "missing": [] if cycle_ready else ["promotion_cycle_runner.py or automation_scheduler.py"],
        },
        {
            "id": "fully_autonomous_self_evolution",
            "label": "Research, install tools, keep learning, and upgrade the Skill itself",
            "status": "blocked_by_safety_boundary",
            "evidence": ["final_capability_audit.py can audit tools and produce upgrade actions"],
            "missing": ["explicit review/approval for dependency upgrades and self-modifying code"],
            "limits": [
                "The Skill can install explicit allowlisted runtime dependencies when commanded.",
                "It must not silently download unreviewed network code, store secrets, or replace itself without a clear source/risk note.",
            ],
        },
    ]


def scripts_ready(scripts: dict[str, dict[str, Any]], keys: list[str]) -> bool:
    return all(bool(scripts.get(key, {}).get("exists")) for key in keys)


def scripts_present(scripts: dict[str, dict[str, Any]], keys: list[str]) -> list[str]:
    return [str(scripts[key]["file"]) for key in keys if bool(scripts.get(key, {}).get("exists"))]


def missing_for_scripts(scripts: dict[str, dict[str, Any]], keys: list[str]) -> list[str]:
    return [SCRIPT_REQUIREMENTS[key] for key in keys if not bool(scripts.get(key, {}).get("exists"))]


def status_value(value: bool) -> str:
    return "ready" if value else "not_ready"


def missing_publish_credentials(credentials: dict[str, dict[str, Any]]) -> list[str]:
    missing = []
    if not credentials["github_write"]["ready"]:
        missing.append("GITHUB_TOKEN or GH_TOKEN for GitHub writes")
    if not (credentials["youtube_oauth_upload"]["ready"] or credentials["youtube_oauth_flow"]["ready"]):
        missing.append("YouTube OAuth access token or OAuth client credentials")
    if not credentials["douyin_publish"]["ready"]:
        missing.append("Douyin open-platform app credentials and user authorization")
    return missing


def self_evolution_status(tools: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "mode": "controlled_autonomy",
        "canDoNow": [
            "audit local scripts, tools, and credential presence",
            "write capability reports and next-action plans",
            "install Playwright Chromium when explicitly requested through --install-safe-missing-tools",
            "use official docs and public repos as research inputs for reviewed upgrades",
        ],
        "notAllowed": [
            "silent dependency upgrades",
            "self-replacement from unreviewed network code",
            "credential, cookie, or hidden-token extraction",
            "captcha/risk-control bypass",
        ],
        "safeInstallCandidates": [
            {
                "id": "playwright_chromium",
                "status": "ready" if tools["playwrightChromium"]["available"] else "missing_or_unchecked",
                "command": "python scripts/final_capability_audit.py --install-safe-missing-tools --safe-install playwright_chromium",
            }
        ],
    }


def recommended_commands(out_dir: Path) -> list[dict[str, str]]:
    return [
        {
            "purpose": "one_command_cycle",
            "command": (
                f"python scripts/promotion_cycle_runner.py --browser-url \"https://example.com/product\" "
                f"--platforms youtube,zhihu,xiaohongshu,douyin,github --out-dir \"{out_dir}\""
            ),
        },
        {
            "purpose": "install_browser_runtime_when_explicitly_allowed",
            "command": "python scripts/final_capability_audit.py --install-safe-missing-tools --safe-install playwright_chromium",
        },
        {
            "purpose": "run_periodic_jobs",
            "command": "python scripts/automation_scheduler.py run --config ./promotion-automation.json",
        },
    ]


def next_actions(
    requirements: list[dict[str, Any]],
    tools: dict[str, dict[str, Any]],
    credentials: dict[str, dict[str, Any]],
    out_dir: Path,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not tools["playwrightChromium"]["available"]:
        actions.append(
            {
                "priority": 1,
                "area": "product_intake_and_platform_search",
                "action": "Install or verify Playwright Chromium for rendered product and platform search snapshots.",
                "command": "python scripts/final_capability_audit.py --install-safe-missing-tools --safe-install playwright_chromium",
            }
        )
    if not credentials["github_write"]["ready"]:
        actions.append(
            {
                "priority": 2,
                "area": "github_publish",
                "action": "Provide GITHUB_TOKEN or GH_TOKEN only in the environment when approved GitHub publishing is needed.",
            }
        )
    if not (credentials["youtube_oauth_upload"]["ready"] or credentials["youtube_oauth_flow"]["ready"]):
        actions.append(
            {
                "priority": 3,
                "area": "youtube_publish",
                "action": "Provide Google OAuth client credentials or a temporary YouTube OAuth access token for approved uploads.",
            }
        )
    actions.append(
        {
            "priority": 4,
            "area": "full_cycle",
            "action": "Run a real product through the cycle and register real published URLs or exports before claiming performance.",
            "command": (
                f"python scripts/promotion_cycle_runner.py --browser-url \"https://example.com/product\" "
                f"--platforms youtube,zhihu,xiaohongshu,douyin,github --out-dir \"{out_dir}\""
            ),
        }
    )
    if any(item["status"] == "blocked_by_safety_boundary" for item in requirements):
        actions.append(
            {
                "priority": 5,
                "area": "self_evolution",
                "action": "Keep self-upgrades reviewable: generate a proposal, cite official docs/public repos, then apply reviewed changes.",
            }
        )
    return actions


def final_status(requirements: list[dict[str, Any]]) -> str:
    statuses = {item["status"] for item in requirements}
    if statuses == {"ready"}:
        return "full_ready"
    if "blocked_by_authorization_or_platform_limits" in statuses or "blocked_by_safety_boundary" in statuses:
        return "partial_ready_blocked_by_platform_or_safety_limits"
    if "partial_ready" in statuses:
        return "partial_ready"
    return "not_ready"


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = audit_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "final-capability-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (directory / "final-capability-audit.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Final Capability Audit",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['finalStatus']}`",
        f"- Output: {report['outDir']}",
        "",
        "## Requirements",
    ]
    for item in report["requirements"]:
        lines.append(f"- `{item['id']}`: `{item['status']}` - {item['label']}")
        missing = item.get("missing") or []
        if missing:
            lines.append(f"  Missing: {', '.join(missing)}")
        limits = item.get("limits") or []
        if limits:
            lines.append(f"  Limits: {'; '.join(limits)}")
    lines.extend(["", "## Platforms"])
    for platform, info in report["platforms"].items():
        lines.append(
            f"- {platform}: search=`{info['viralSearch']}`, publish=`{info['directPublish']}`, metrics=`{info['metricsRecovery']}`"
        )
    lines.extend(["", "## Next Actions"])
    for action in report["nextActions"]:
        lines.append(f"- P{action['priority']} {action['area']}: {action['action']}")
        if action.get("command"):
            lines.append(f"  Command: `{action['command']}`")
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def audit_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/capability"


if __name__ == "__main__":
    main()

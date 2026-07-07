#!/usr/bin/env python3
"""Audit official platform access paths for publishing and metrics recovery."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


TODAY = date.today().isoformat()
DEFAULT_PLATFORMS = ["youtube", "zhihu", "xiaohongshu", "douyin", "github", "tiktok"]


PLATFORM_ACCESS: dict[str, dict[str, Any]] = {
    "youtube": {
        "label": "YouTube",
        "publish": {
            "access": "implemented_official_api",
            "mode": "official_api_publish",
            "implementedBy": ["publish_executor.py", "youtube_oauth_publish.py"],
            "requiredEnvAny": ["YOUTUBE_OAUTH_ACCESS_TOKEN"],
            "alternativeEnvAll": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
            "approvalRequired": True,
            "notes": "Uploads use the official YouTube Data API videos.insert endpoint and require channel OAuth authorization.",
            "officialDocs": [
                {
                    "title": "YouTube Data API videos.insert",
                    "url": "https://developers.google.com/youtube/v3/docs/videos/insert",
                }
            ],
        },
        "metrics": {
            "access": "implemented_official_api",
            "mode": "official_api_metrics",
            "implementedBy": ["metrics_intake.py", "metrics_recovery.py"],
            "requiredEnvAny": ["YOUTUBE_API_KEY"],
            "notes": "Video statistics are read from the official videos.list endpoint when an API key is present.",
            "officialDocs": [
                {
                    "title": "YouTube Data API videos.list",
                    "url": "https://developers.google.com/youtube/v3/docs/videos/list",
                }
            ],
        },
    },
    "github": {
        "label": "GitHub",
        "publish": {
            "access": "implemented_official_api",
            "mode": "official_api_publish",
            "implementedBy": ["publish_executor.py"],
            "requiredEnvAny": ["GITHUB_TOKEN", "GH_TOKEN"],
            "approvalRequired": True,
            "notes": "Repository files, issues, and releases use official GitHub REST API paths with write permissions.",
            "officialDocs": [
                {
                    "title": "GitHub REST API repository contents",
                    "url": "https://docs.github.com/en/rest/repos/contents",
                },
                {
                    "title": "GitHub REST API issues",
                    "url": "https://docs.github.com/en/rest/issues/issues",
                },
                {
                    "title": "GitHub REST API releases",
                    "url": "https://docs.github.com/en/rest/releases/releases",
                },
            ],
        },
        "metrics": {
            "access": "implemented_public_api",
            "mode": "public_api_metrics",
            "implementedBy": ["metrics_intake.py", "metrics_recovery.py"],
            "requiredEnvAny": [],
            "notes": "Public repository stars, forks, and watchers can be read without storing credentials.",
            "officialDocs": [
                {
                    "title": "GitHub REST API repositories",
                    "url": "https://docs.github.com/en/rest/repos/repos",
                }
            ],
        },
    },
    "douyin": {
        "label": "Douyin",
        "publish": {
            "access": "official_candidate_not_integrated",
            "mode": "browser_assisted_or_official_app_required",
            "implementedBy": [],
            "requiredEnvAll": ["DOUYIN_CLIENT_KEY", "DOUYIN_CLIENT_SECRET", "DOUYIN_ACCESS_TOKEN", "DOUYIN_OPEN_ID"],
            "approvalRequired": True,
            "notes": "Official publishing requires approved open-platform app permissions, scopes, and user authorization; no direct executor is bundled yet.",
            "officialDocs": [
                {
                    "title": "Douyin Open Platform publishing solution",
                    "url": "https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution",
                }
            ],
        },
        "metrics": {
            "access": "official_or_manual_export_required",
            "mode": "manual_structured_snapshot_or_official_export",
            "implementedBy": ["metrics_intake.py", "metrics_recovery.py"],
            "requiredEnvAll": [],
            "notes": "Use official exports/API access when approved, or browser-visible structured snapshots supplied by the user.",
            "officialDocs": [
                {
                    "title": "Douyin Open Platform docs",
                    "url": "https://open.douyin.com/platform/doc",
                }
            ],
        },
    },
    "tiktok": {
        "label": "TikTok",
        "publish": {
            "access": "official_candidate_not_integrated",
            "mode": "official_app_integration_required",
            "implementedBy": [],
            "requiredEnvAll": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN", "TIKTOK_OPEN_ID"],
            "approvalRequired": True,
            "notes": "Direct Post requires app product setup, creator authorization, and approved video.publish scope; no direct executor is bundled yet.",
            "officialDocs": [
                {
                    "title": "TikTok Content Posting API",
                    "url": "https://developers.tiktok.com/doc/content-posting-api-get-started/",
                }
            ],
        },
        "metrics": {
            "access": "official_or_manual_export_required",
            "mode": "manual_structured_snapshot_or_official_export",
            "implementedBy": ["metrics_intake.py", "metrics_recovery.py"],
            "requiredEnvAll": [],
            "notes": "Recover only from official analytics access, exports, or user-visible structured snapshots.",
            "officialDocs": [
                {
                    "title": "TikTok Research API overview",
                    "url": "https://developers.tiktok.com/doc/research-api-specs-query-videos/",
                }
            ],
        },
    },
    "xiaohongshu": {
        "label": "Xiaohongshu",
        "publish": {
            "access": "no_verified_public_creator_publish_endpoint",
            "mode": "manual_or_browser_assisted_until_verified",
            "implementedBy": [],
            "requiredEnvAll": [],
            "approvalRequired": True,
            "notes": "No stable public creator note publishing endpoint is integrated; publish packs remain manual/browser-assisted until official access is verified.",
            "officialDocs": [
                {
                    "title": "Xiaohongshu Open Platform API index",
                    "url": "https://open.xiaohongshu.com/document/api",
                }
            ],
        },
        "metrics": {
            "access": "manual_export_or_structured_snapshot_required",
            "mode": "manual_structured_snapshot_or_export",
            "implementedBy": ["metrics_intake.py", "metrics_recovery.py"],
            "requiredEnvAll": [],
            "notes": "Use exported analytics, screenshots, or browser-visible structured snapshots; do not use private endpoints.",
            "officialDocs": [
                {
                    "title": "Xiaohongshu Open Platform API index",
                    "url": "https://open.xiaohongshu.com/document/api",
                }
            ],
        },
    },
    "zhihu": {
        "label": "Zhihu",
        "publish": {
            "access": "no_verified_public_creator_publish_endpoint",
            "mode": "manual_or_browser_assisted_until_verified",
            "implementedBy": [],
            "requiredEnvAll": [],
            "approvalRequired": True,
            "notes": "No stable public article publishing API is integrated; publish packs remain manual/browser-assisted until official access is verified.",
            "officialDocs": [],
        },
        "metrics": {
            "access": "manual_export_or_structured_snapshot_required",
            "mode": "manual_structured_snapshot_or_export",
            "implementedBy": ["metrics_intake.py", "metrics_recovery.py"],
            "requiredEnvAll": [],
            "notes": "Use public page evidence, exported analytics, screenshots, or browser-visible structured snapshots.",
            "officialDocs": [],
        },
    },
}


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    platforms = select_platforms(args.platforms)
    records = [platform_record(platform, args.check_live) for platform in platforms]
    report = {
        "generatedAt": TODAY,
        "status": overall_status(records),
        "checkLive": bool(args.check_live),
        "platforms": records,
        "summary": summary(records),
        "implementationGaps": implementation_gaps(records),
        "guardrails": [
            "Use official APIs only for automated writes.",
            "Never store, print, or infer credential values; record environment variable names only.",
            "Stop for user action when login, captcha, account verification, or platform review is required.",
            "Treat platforms without verified public creator-publishing access as manual/browser-assisted.",
            "Recover metrics only from official APIs, public pages, user exports, screenshots, or browser-visible structured snapshots.",
        ],
    }
    write_report(out_dir, report)
    print(f"Platform access audit written to: {(report_dir(out_dir) / 'platform-access-audit.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit official platform publishing and metrics access paths.")
    parser.add_argument("--platforms", default="", help="Comma-separated platform filter. Defaults to all supported platforms.")
    parser.add_argument("--out-dir", default="./promotion-output")
    parser.add_argument(
        "--check-live",
        action="store_true",
        help="Fetch official doc URLs and record reachability status. This never sends credentials.",
    )
    return parser.parse_args()


def select_platforms(value: str) -> list[str]:
    if not value:
        return DEFAULT_PLATFORMS
    selected = [item.strip().lower() for item in value.split(",") if item.strip()]
    unknown = [item for item in selected if item not in PLATFORM_ACCESS]
    if unknown:
        raise SystemExit(f"Unsupported platform(s): {', '.join(unknown)}")
    return selected


def platform_record(platform: str, check_live: bool) -> dict[str, Any]:
    config = PLATFORM_ACCESS[platform]
    publish = capability_record(config["publish"], check_live)
    metrics = capability_record(config["metrics"], check_live)
    return {
        "platform": platform,
        "label": config["label"],
        "publish": publish,
        "metrics": metrics,
        "automationLevel": automation_level(publish, metrics),
        "nextActions": next_actions(platform, publish, metrics),
    }


def capability_record(config: dict[str, Any], check_live: bool) -> dict[str, Any]:
    docs = [dict(item) for item in config.get("officialDocs", [])]
    if check_live:
        for doc in docs:
            doc["liveCheck"] = check_url(str(doc["url"]))
    env = env_status(config)
    return {
        "access": config["access"],
        "mode": config["mode"],
        "implementedBy": config.get("implementedBy", []),
        "credentialStatus": env,
        "approvalRequired": bool(config.get("approvalRequired", False)),
        "officialDocs": docs,
        "notes": config["notes"],
        "readyForAutomation": ready_for_automation(config, env),
    }


def env_status(config: dict[str, Any]) -> dict[str, Any]:
    any_names = list(config.get("requiredEnvAny") or [])
    all_names = list(config.get("requiredEnvAll") or [])
    alternative_all = list(config.get("alternativeEnvAll") or [])
    present_any = [name for name in any_names if os.environ.get(name)]
    present_all = [name for name in all_names if os.environ.get(name)]
    present_alternative = [name for name in alternative_all if os.environ.get(name)]
    if any_names:
        ready = bool(present_any) or (bool(alternative_all) and len(present_alternative) == len(alternative_all))
    elif all_names:
        ready = len(present_all) == len(all_names)
    else:
        ready = True
    return {
        "requiredAny": any_names,
        "requiredAll": all_names,
        "alternativeAll": alternative_all,
        "presentEnv": sorted(set(present_any + present_all + present_alternative)),
        "missingEnv": [name for name in any_names + all_names + alternative_all if not os.environ.get(name)],
        "ready": ready,
        "valuesStored": False,
    }


def ready_for_automation(config: dict[str, Any], env: dict[str, Any]) -> bool:
    return config["access"] in {"implemented_official_api", "implemented_public_api"} and bool(env["ready"])


def automation_level(publish: dict[str, Any], metrics: dict[str, Any]) -> str:
    if publish["readyForAutomation"] and metrics["readyForAutomation"]:
        return "official_publish_and_metrics_ready"
    if publish["access"] == "implemented_official_api":
        return "official_publish_ready_when_credentials_present"
    if publish["access"] == "official_candidate_not_integrated":
        return "official_app_integration_required"
    return "manual_or_browser_assisted_required"


def next_actions(platform: str, publish: dict[str, Any], metrics: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if publish["access"] == "implemented_official_api" and not publish["credentialStatus"]["ready"]:
        actions.append("Set the required publish environment variables only when execution is approved.")
    if publish["access"] == "official_candidate_not_integrated":
        actions.append("Complete official developer-app approval and implement a reviewed executor before direct publishing.")
    if publish["access"] == "no_verified_public_creator_publish_endpoint":
        actions.append("Keep publishing manual/browser-assisted until official creator publishing access is verified.")
    if metrics["access"] in {"manual_export_or_structured_snapshot_required", "official_or_manual_export_required"}:
        actions.append("Recover metrics from official exports, screenshots, public pages, or structured browser snapshots.")
    if platform in {"douyin", "tiktok"}:
        actions.append("Do not treat app credentials alone as publish readiness; user authorization and platform review are still required.")
    return actions


def overall_status(records: list[dict[str, Any]]) -> str:
    levels = {record["automationLevel"] for record in records}
    if levels == {"official_publish_and_metrics_ready"}:
        return "full_official_access_ready"
    if "manual_or_browser_assisted_required" in levels or "official_app_integration_required" in levels:
        return "partial_ready_official_paths_mapped"
    return "partial_ready_credentials_required"


def summary(records: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {"total": len(records)}
    for record in records:
        level = str(record["automationLevel"])
        result[level] = result.get(level, 0) + 1
    return dict(sorted(result.items()))


def implementation_gaps(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    for record in records:
        publish = record["publish"]
        metrics = record["metrics"]
        if publish["access"] == "official_candidate_not_integrated":
            gaps.append({"platform": record["platform"], "area": "publish", "gap": "official_app_executor_not_integrated"})
        if publish["access"] == "no_verified_public_creator_publish_endpoint":
            gaps.append({"platform": record["platform"], "area": "publish", "gap": "verified_official_creator_publish_api_missing"})
        if metrics["access"] in {"manual_export_or_structured_snapshot_required", "official_or_manual_export_required"}:
            gaps.append({"platform": record["platform"], "area": "metrics", "gap": "official_or_user_export_evidence_required"})
    return gaps


def check_url(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "CodexSkillPlatformAccessAudit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return {"status": "reachable", "httpStatus": response.status}
    except urllib.error.HTTPError as exc:
        return {"status": "http_error", "httpStatus": exc.code}
    except urllib.error.URLError as exc:
        return {"status": "unreachable", "reason": str(exc.reason)[:160]}
    except TimeoutError:
        return {"status": "timeout"}


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = report_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "platform-access-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / "platform-access-audit.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Platform Access Audit",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Live doc check: {report['checkLive']}",
        "",
        "## Platforms",
    ]
    for record in report["platforms"]:
        lines.extend(
            [
                "",
                f"### {record['label']}",
                f"- Automation level: `{record['automationLevel']}`",
                f"- Publish access: `{record['publish']['access']}`",
                f"- Publish env present: {', '.join(record['publish']['credentialStatus']['presentEnv']) or 'none'}",
                f"- Metrics access: `{record['metrics']['access']}`",
                f"- Metrics env present: {', '.join(record['metrics']['credentialStatus']['presentEnv']) or 'none'}",
            ]
        )
        for action in record["nextActions"]:
            lines.append(f"- Next action: {action}")
        docs = record["publish"]["officialDocs"] + record["metrics"]["officialDocs"]
        if docs:
            lines.append("- Official docs:")
            seen = set()
            for doc in docs:
                if doc["url"] in seen:
                    continue
                seen.add(doc["url"])
                suffix = ""
                if doc.get("liveCheck"):
                    suffix = f" ({doc['liveCheck']['status']})"
                lines.append(f"  - {doc['title']}: {doc['url']}{suffix}")
    if report["implementationGaps"]:
        lines.extend(["", "## Implementation Gaps"])
        for gap in report["implementationGaps"]:
            lines.append(f"- {gap['platform']} {gap['area']}: `{gap['gap']}`")
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def report_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/platform-access"


if __name__ == "__main__":
    main()

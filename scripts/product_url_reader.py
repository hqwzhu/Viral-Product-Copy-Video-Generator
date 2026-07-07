#!/usr/bin/env python3
"""Read product URLs into structured browser snapshots and product profiles."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
BROWSER_SNAPSHOT = SCRIPTS / "browser_snapshot.py"
PRODUCT_INTAKE = SCRIPTS / "product_intake.py"
TODAY = date.today().isoformat()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    urls = collect_urls(args)
    if not urls:
        raise SystemExit("No URLs were supplied.")
    records = [read_product_url(args, out_dir, url, index) for index, url in enumerate(urls, start=1)]
    report = build_report(args, out_dir, records)
    write_report(out_dir, report)
    print(f"Product URL reader report written to: {(report_dir(out_dir) / 'product-url-reader.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read product URLs with Codex/browser evidence before product intake.")
    parser.add_argument("--url", action="append", default=[], help="Product URL. Can be repeated.")
    parser.add_argument("--urls-file", default="", help="Text file with one product URL per line.")
    parser.add_argument("--out-dir", default="./promotion-output")
    parser.add_argument("--skip-browser", action="store_true", help="Skip browser rendering and use static URL intake only.")
    parser.add_argument("--no-static-fallback", action="store_true", help="Do not fall back to static URL intake when browser capture fails.")
    parser.add_argument("--install-browser-if-missing", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--wait-until", default="networkidle", choices=["load", "domcontentloaded", "networkidle"])
    parser.add_argument("--screenshot", action="store_true", help="Save browser screenshots next to structured snapshots.")
    return parser.parse_args()


def collect_urls(args: argparse.Namespace) -> list[str]:
    urls = [item.strip() for item in args.url if item.strip()]
    if args.urls_file:
        path = Path(args.urls_file)
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    deduped = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            deduped.append(url)
            seen.add(url)
    return deduped


def read_product_url(args: argparse.Namespace, out_dir: Path, url: str, index: int) -> dict[str, Any]:
    item_dir = out_dir / "product-url-reader" / f"{index:03d}-{slug_from_url(url)}"
    item_dir.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []
    snapshot_path = item_dir / "structured-product-page.json"
    intake_dir = item_dir / "intake"

    browser_status: dict[str, Any] = {"status": "skipped", "reason": "--skip-browser was supplied."}
    profile_status: dict[str, Any]
    source_mode = "static_url_fallback"

    if not args.skip_browser:
        browser_command = [
            sys.executable,
            str(BROWSER_SNAPSHOT),
            "--url",
            url,
            "--out-file",
            str(snapshot_path),
            "--out-dir",
            str(item_dir),
            "--timeout-ms",
            str(args.timeout_ms),
            "--wait-until",
            args.wait_until,
        ]
        if args.install_browser_if_missing:
            browser_command.append("--install-browser-if-missing")
        if args.screenshot:
            browser_command.append("--screenshot")
        browser_step = run_command("browser_snapshot", browser_command)
        steps.append(browser_step)
        browser_status = {
            "status": "ready" if browser_step["exitCode"] == 0 and snapshot_path.exists() else "error",
            "snapshot": str(snapshot_path) if snapshot_path.exists() else "",
            "exitCode": browser_step["exitCode"],
        }

    if browser_status["status"] == "ready":
        intake_command = [
            sys.executable,
            str(PRODUCT_INTAKE),
            "--structured-json",
            str(snapshot_path),
            "--out-dir",
            str(intake_dir),
        ]
        source_mode = "browser_structured_snapshot"
    elif args.no_static_fallback:
        intake_command = []
    else:
        intake_command = [
            sys.executable,
            str(PRODUCT_INTAKE),
            "--url",
            url,
            "--out-dir",
            str(intake_dir),
        ]

    if intake_command:
        intake_step = run_command("product_intake", intake_command)
        steps.append(intake_step)
        profile_path = intake_dir / "product-profile.json"
        profile_status = {
            "status": "ready" if intake_step["exitCode"] == 0 and profile_path.exists() else "error",
            "profile": str(profile_path) if profile_path.exists() else "",
            "markdown": str(intake_dir / "product-profile.md") if (intake_dir / "product-profile.md").exists() else "",
            "exitCode": intake_step["exitCode"],
        }
    else:
        profile_status = {
            "status": "blocked",
            "profile": "",
            "markdown": "",
            "reason": "Browser capture failed and static fallback was disabled.",
        }

    profile = read_json(Path(profile_status.get("profile", ""))) if profile_status.get("profile") else {}
    return {
        "id": f"product-url-{index:03d}",
        "url": url,
        "status": record_status(browser_status, profile_status),
        "sourceMode": source_mode if profile_status.get("status") == "ready" else "unavailable",
        "workspace": str(item_dir),
        "browser": browser_status,
        "intake": profile_status,
        "product": summarize_profile(profile),
        "nextWorkflowCommand": next_workflow_command(url, source_mode, snapshot_path, out_dir, profile_status),
        "steps": steps,
    }


def build_report(args: argparse.Namespace, out_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generatedAt": TODAY,
        "outDir": str(out_dir),
        "status": report_status(records),
        "records": records,
        "summary": {
            "requestedUrls": len(records),
            "ready": sum(1 for item in records if item["status"] == "ready"),
            "partialReady": sum(1 for item in records if item["status"] == "partial_ready"),
            "blocked": sum(1 for item in records if item["status"] == "blocked"),
            "browserStructuredProfiles": sum(1 for item in records if item["sourceMode"] == "browser_structured_snapshot"),
            "staticFallbackProfiles": sum(1 for item in records if item["sourceMode"] == "static_url_fallback"),
        },
        "recommendedNextCommand": "Use records[].nextWorkflowCommand for the correct structured or static intake mode.",
        "guardrails": [
            "Read browser-visible product page evidence before product intake whenever Chromium is available.",
            "Static URL intake is only a fallback and may miss dynamic page content.",
            "Do not extract cookies, passwords, hidden tokens, private endpoints, or bypass login/captcha/risk controls.",
            "Treat pricing, testimonials, customer counts, and legal claims as assumptions unless the product page proves them.",
        ],
    }


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = report_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "product-url-reader.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / "product-url-reader.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Product URL Reader",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Requested URLs: {report['summary']['requestedUrls']}",
        f"- Browser structured profiles: {report['summary']['browserStructuredProfiles']}",
        f"- Static fallback profiles: {report['summary']['staticFallbackProfiles']}",
        "",
        "## Records",
    ]
    for record in report["records"]:
        product = record.get("product", {})
        lines.extend(
            [
                "",
                f"### {record['id']}",
                f"- URL: {record['url']}",
                f"- Status: `{record['status']}`",
                f"- Source mode: `{record['sourceMode']}`",
                f"- Product: {product.get('productName', 'unknown')}",
                f"- Profile: {record['intake'].get('profile', '')}",
                f"- Snapshot: {record['browser'].get('snapshot', '')}",
                f"- Next workflow: `{record.get('nextWorkflowCommand', '')}`",
            ]
        )
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def run_command(name: str, command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "name": name,
        "command": display_command(command),
        "exitCode": result.returncode,
        "stdoutTail": tail(result.stdout),
        "stderrTail": tail(result.stderr),
    }


def record_status(browser_status: dict[str, Any], profile_status: dict[str, Any]) -> str:
    if browser_status.get("status") == "ready" and profile_status.get("status") == "ready":
        return "ready"
    if profile_status.get("status") == "ready":
        return "partial_ready"
    return "blocked"


def report_status(records: list[dict[str, Any]]) -> str:
    if all(item["status"] == "ready" for item in records):
        return "ready"
    if any(item["status"] in {"ready", "partial_ready"} for item in records):
        return "partial_ready"
    return "blocked"


def summarize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    if not profile:
        return {}
    return {
        "productName": profile.get("productName", ""),
        "canonicalUrl": profile.get("canonicalUrl", ""),
        "sourceType": profile.get("sourceType", ""),
        "valueProposition": profile.get("valueProposition", ""),
        "pricing": profile.get("pricing", ""),
        "confidence": profile.get("confidence", ""),
        "targetAudienceAssumptions": profile.get("targetAudienceAssumptions", []),
        "painPointAssumptions": profile.get("painPointAssumptions", []),
    }


def next_workflow_command(url: str, source_mode: str, snapshot_path: Path, out_dir: Path, profile_status: dict[str, Any]) -> str:
    if profile_status.get("status") != "ready":
        return ""
    if source_mode == "browser_structured_snapshot" and snapshot_path.exists():
        return (
            f"python scripts/run_promotion_workflow.py --structured-json \"{snapshot_path}\" "
            f"--platforms youtube,zhihu,xiaohongshu,douyin,github --out-dir \"{out_dir}\""
        )
    return (
        f"python scripts/run_promotion_workflow.py --product-url \"{url}\" "
        f"--platforms youtube,zhihu,xiaohongshu,douyin,github --out-dir \"{out_dir}\""
    )


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def slug_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    raw = "-".join(part for part in [parsed.netloc, parsed.path.strip("/")] if part) or url
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    return slug[:80] or "product"


def report_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/intake"


def display_command(command: list[str]) -> list[str]:
    return ["python" if item == sys.executable else item for item in command]


def tail(value: str, limit: int = 1200) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[-limit:]


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Create a publish setup kit from a publish-readiness report."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


TODAY = date.today().isoformat()
APPROVAL_PHRASE = "I_APPROVE_PUBLISH"
OFFICIAL_READINESS = {"missing_credentials", "missing_target", "missing_approval", "dry_run_ready", "ready_to_execute"}
BROWSER_OR_MANUAL_READINESS = {"manual_publish_required", "browser_assisted_or_official_app_required"}


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    readiness_path = resolve_readiness_path(args, out_dir)
    readiness = read_json(readiness_path) if readiness_path else {}
    records = selected_records(readiness, args.platforms)
    setup_records = [build_setup_record(record, readiness) for record in records]
    env_names = collect_env_names(setup_records)
    artifacts = write_artifacts(out_dir, readiness_path, setup_records, env_names)
    report = build_report(args, readiness_path, readiness, setup_records, env_names, artifacts)
    write_report(out_dir, report)
    print(f"Publish setup assistant written to: {(report_dir(out_dir) / 'publish-setup.json').resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate credential, target, and approval setup artifacts for publishing.")
    parser.add_argument("--publish-readiness", default="", help="Path to publish-readiness.json. Defaults to <out-dir>/reports/promotion-manager/publish-readiness/publish-readiness.json.")
    parser.add_argument("--platforms", default="", help="Comma-separated platform filter.")
    parser.add_argument("--out-dir", default="./promotion-output")
    return parser.parse_args()


def resolve_readiness_path(args: argparse.Namespace, out_dir: Path) -> Path | None:
    if args.publish_readiness:
        path = Path(args.publish_readiness)
        return path if path.exists() else None
    candidate = out_dir / "reports/promotion-manager/publish-readiness/publish-readiness.json"
    return candidate if candidate.exists() else None


def selected_records(readiness: dict[str, Any], platforms: str) -> list[dict[str, Any]]:
    records = [item for item in readiness.get("records", []) if isinstance(item, dict)]
    selected = split_csv(platforms)
    if selected:
        records = [item for item in records if str(item.get("platform", "")).lower() in selected]
    return records


def build_setup_record(record: dict[str, Any], readiness_report: dict[str, Any]) -> dict[str, Any]:
    platform = str(record.get("platform", "")).strip()
    readiness = str(record.get("readiness", "")).strip()
    credential = record.get("credentialStatus") if isinstance(record.get("credentialStatus"), dict) else {}
    target = record.get("targetStatus") if isinstance(record.get("targetStatus"), dict) else {}
    approval = record.get("approvalStatus") if isinstance(record.get("approvalStatus"), dict) else {}
    category = setup_category(readiness)
    env_names = ordered_unique(
        list(credential.get("requiredAny") or [])
        + list(credential.get("requiredAll") or [])
        + list(credential.get("alternativeAll") or [])
    )
    missing_env = ordered_unique(list(credential.get("missingEnv") or []))
    commands = setup_commands(platform, readiness, readiness_report)
    return {
        "platform": platform,
        "publishMode": record.get("publishMode", ""),
        "readiness": readiness,
        "setupCategory": category,
        "credentialEnvNames": env_names,
        "missingEnv": missing_env,
        "target": {
            "ready": bool(target.get("ready", True)),
            "field": target.get("field", ""),
            "missing": target.get("missing", ""),
        },
        "approval": {
            "required": bool(approval.get("required", False)),
            "approvalPhrase": APPROVAL_PHRASE if approval.get("required", False) else "",
            "provided": bool(approval.get("approvalProvided", False)),
        },
        "setupSteps": setup_steps(platform, category, missing_env, target, approval, record),
        "commands": commands,
        "sourceNextAction": record.get("nextAction", ""),
        "guardrail": platform_guardrail(platform, readiness),
    }


def setup_category(readiness: str) -> str:
    if readiness == "missing_credentials":
        return "credential_setup_required"
    if readiness == "missing_target":
        return "target_setup_required"
    if readiness == "missing_approval":
        return "approval_required"
    if readiness == "dry_run_ready":
        return "execution_approval_required"
    if readiness == "ready_to_execute":
        return "ready_to_execute"
    if readiness in BROWSER_OR_MANUAL_READINESS:
        return "browser_or_manual_publish"
    if readiness == "already_published":
        return "published_metrics_recovery"
    if readiness == "official_app_integration_required":
        return "platform_app_integration_required"
    return "manual_review_required"


def setup_steps(
    platform: str,
    category: str,
    missing_env: list[str],
    target: dict[str, Any],
    approval: dict[str, Any],
    record: dict[str, Any],
) -> list[str]:
    if category == "credential_setup_required":
        return [
            "Set required environment variables in the shell or OS scheduler; do not write real secret values into repo files.",
            "Rerun publish readiness to verify credentials are present by name.",
            f"Use --execute-publish --approval {APPROVAL_PHRASE} only after reviewing the dry-run output.",
        ]
    if category == "target_setup_required":
        missing = target.get("missing") or "the required platform target"
        return [f"Provide {missing}.", "Rerun publish readiness before attempting official execution."]
    if category == "approval_required":
        return [f"Add the exact approval phrase {APPROVAL_PHRASE} when executing official writes."]
    if category == "execution_approval_required":
        return [
            "Review generated drafts, targets, and dry-run execution reports.",
            f"Execute only with --execute-publish --approval {APPROVAL_PHRASE}.",
        ]
    if category == "ready_to_execute":
        return ["The readiness report says execution gates are satisfied; run the guarded executor and keep the official execution report."]
    if category == "browser_or_manual_publish":
        return [
            "Use the browser-assisted payload or manual draft in a user-visible creator/editor page.",
            "Do not auto-login, bypass challenges, or click final publish by script.",
            "After publishing, register the real published URL and evidence for metrics recovery.",
        ]
    if category == "published_metrics_recovery":
        return ["Use the registered published URL for public metrics, comments, and business attribution recovery."]
    if category == "platform_app_integration_required":
        return [f"Complete official {platform} app approval and add a reviewed executor before claiming direct publishing."]
    next_action = str(record.get("nextAction") or "Review platform readiness manually.")
    return [next_action]


def setup_commands(platform: str, readiness: str, readiness_report: dict[str, Any]) -> dict[str, str]:
    inputs = readiness_report.get("inputs") if isinstance(readiness_report.get("inputs"), dict) else {}
    queue = str(inputs.get("publishQueue") or "").strip()
    manifest = str(inputs.get("workflowManifest") or "").strip()
    out_dir = infer_out_dir(queue, manifest)
    readiness_base = ["python", "scripts/publish_readiness_runner.py"]
    if queue:
        readiness_base.extend(["--publish-queue", queue])
    elif manifest:
        readiness_base.extend(["--workflow-manifest", manifest, "--build-queue"])
    readiness_base.extend(["--platforms", platform])
    append_input(readiness_base, "--github-repo", inputs.get("githubRepo", ""))
    append_input(readiness_base, "--youtube-video-file", inputs.get("youtubeVideoFile", ""))
    append_input(readiness_base, "--douyin-video-file", inputs.get("douyinVideoFile", ""))
    if out_dir:
        readiness_base.extend(["--out-dir", out_dir])

    execute = list(readiness_base)
    execute.extend(["--execute-publish", "--approval", APPROVAL_PHRASE])
    commands = {"rerunReadiness": display_command(readiness_base)}
    if readiness in OFFICIAL_READINESS:
        commands["executeWhenReady"] = display_command(execute)
    if readiness in BROWSER_OR_MANUAL_READINESS and queue:
        browser = [
            "python",
            "scripts/browser_publish_assistant.py",
            "--publish-queue",
            queue,
            "--platforms",
            platform,
        ]
        if out_dir:
            browser.extend(["--out-dir", out_dir])
        commands["prepareBrowserPublish"] = display_command(browser)
    commands["registerPublishedUrl"] = (
        f"python scripts/published_items.py --platform {platform} --published-url \"https://...\" "
        f"--title \"Published {platform} content\" --evidence \"./screenshots/{platform}-published.png\""
        + (f" --out-dir \"{out_dir}\"" if out_dir else "")
    )
    return commands


def infer_out_dir(queue: str, manifest: str) -> str:
    for value in [queue, manifest]:
        if not value:
            continue
        path = Path(value)
        parts = path.parts
        if len(parts) >= 4 and parts[-4:-1] == ("reports", "promotion-manager", "publish-queue"):
            return str(path.parents[3])
        if len(parts) >= 4 and parts[-4:-1] == ("reports", "promotion-manager", "agent-run"):
            return str(path.parents[3])
    return ""


def platform_guardrail(platform: str, readiness: str) -> str:
    if readiness in BROWSER_OR_MANUAL_READINESS:
        return f"{platform} remains browser-assisted/manual until verified official publishing access exists."
    if readiness in OFFICIAL_READINESS:
        return "Official writes still require credentials, target readiness, and exact approval; no credential values are stored."
    return "Use only official APIs, public/browser-visible evidence, or user-provided exports."


def collect_env_names(records: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for record in records:
        names.extend(record.get("credentialEnvNames") or [])
    return ordered_unique(names)


def write_artifacts(out_dir: Path, readiness_path: Path | None, records: list[dict[str, Any]], env_names: list[str]) -> dict[str, str]:
    directory = report_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    env_file = directory / "publish-credentials.example.env"
    checklist_file = directory / "publish-setup-checklist.md"
    env_file.write_text(render_env_template(env_names), encoding="utf-8")
    checklist_file.write_text(render_checklist(readiness_path, records) + "\n", encoding="utf-8")
    return {
        "envTemplate": str(env_file),
        "checklist": str(checklist_file),
    }


def build_report(
    args: argparse.Namespace,
    readiness_path: Path | None,
    readiness: dict[str, Any],
    records: list[dict[str, Any]],
    env_names: list[str],
    artifacts: dict[str, str],
) -> dict[str, Any]:
    return {
        "generatedAt": TODAY,
        "status": "ready" if records else "blocked_missing_readiness",
        "input": {
            "publishReadiness": str(readiness_path) if readiness_path else "",
            "platforms": args.platforms,
            "sourceStatus": readiness.get("status", ""),
        },
        "summary": summarize(records, env_names),
        "records": records,
        "artifacts": artifacts,
        "guardrails": [
            "This setup kit writes environment variable names only, never credential values.",
            "The .env file is an example template; do not commit real secrets.",
            "Official writes require reviewed dry-runs, target information, environment credentials, and exact approval.",
            "Browser-assisted/manual platforms must stop for login, captcha, account verification, and final publish actions.",
            "Published URLs, metrics, orders, and revenue require real evidence before retrospective or optimization.",
        ],
    }


def summarize(records: list[dict[str, Any]], env_names: list[str]) -> dict[str, int]:
    summary: dict[str, int] = {
        "total": len(records),
        "credentialEnvNames": len(env_names),
    }
    for record in records:
        category = str(record.get("setupCategory") or "unknown")
        summary[category] = summary.get(category, 0) + 1
    return dict(sorted(summary.items()))


def write_report(out_dir: Path, report: dict[str, Any]) -> None:
    directory = report_dir(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "publish-setup.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / "publish-setup.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Publish Setup Assistant",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Readiness source: {report['input'].get('publishReadiness', '')}",
        f"- Env template: {report['artifacts'].get('envTemplate', '')}",
        f"- Checklist: {report['artifacts'].get('checklist', '')}",
        "",
        "## Platforms",
    ]
    for record in report["records"]:
        lines.extend(
            [
                "",
                f"### {record['platform']}",
                f"- Setup category: `{record['setupCategory']}`",
                f"- Readiness: `{record['readiness']}`",
                f"- Missing env: {', '.join(record.get('missingEnv') or []) or 'none'}",
                f"- Target missing: {record.get('target', {}).get('missing') or 'none'}",
                f"- Approval required: {record.get('approval', {}).get('required', False)}",
                "- Steps:",
            ]
        )
        lines.extend(f"  - {step}" for step in record.get("setupSteps", []))
        if record.get("commands"):
            lines.append("- Commands:")
            for name, command in record["commands"].items():
                lines.append(f"  - {name}: `{command}`")
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def render_env_template(env_names: list[str]) -> str:
    lines = [
        "# Publish credential template generated by publish_setup_assistant.py",
        "# Do not commit real secrets. Set real values in your shell, OS scheduler, or secret manager.",
    ]
    if not env_names:
        lines.append("# No official publishing credential variables were required by the selected readiness records.")
    for name in env_names:
        lines.append(f"{name}=")
    return "\n".join(lines) + "\n"


def render_checklist(readiness_path: Path | None, records: list[dict[str, Any]]) -> str:
    lines = [
        "# Publish Setup Checklist",
        "",
        f"- Source readiness report: {readiness_path or ''}",
        "- Review dry-run outputs before execution.",
        "- Keep all real credentials outside the repository.",
        "- Register real published URLs before metrics recovery.",
        "",
    ]
    for record in records:
        lines.append(f"## {record['platform']}")
        for step in record.get("setupSteps", []):
            lines.append(f"- [ ] {step}")
        lines.append("")
    return "\n".join(lines)


def read_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def split_csv(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def ordered_unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def append_input(command: list[str], flag: str, value: Any) -> None:
    text = "" if value is None else str(value).strip()
    if text:
        command.extend([flag, text])


def display_command(command: list[str]) -> str:
    return " ".join(quote_arg(item) for item in command)


def quote_arg(value: str) -> str:
    if not value or any(ch.isspace() for ch in value) or any(ch in value for ch in ['"', "'"]):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def report_dir(out_dir: Path) -> Path:
    return out_dir / "reports/promotion-manager/publish-setup"


if __name__ == "__main__":
    main()

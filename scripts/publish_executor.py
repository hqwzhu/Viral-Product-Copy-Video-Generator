#!/usr/bin/env python3
"""Execute approved official publishing actions for supported platforms."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date
from pathlib import Path
from typing import Any


TODAY = date.today().isoformat()
APPROVAL_PHRASE = "I_APPROVE_PUBLISH"
GITHUB_API_VERSION = "2026-03-10"


def main() -> None:
    args = parse_args()
    execution = build_execution(args)
    if args.platform == "github":
        result = execute_github(args, execution)
    elif args.platform == "youtube":
        result = execute_youtube(args, execution)
    else:
        raise SystemExit(f"Unsupported platform: {args.platform}")
    write_result(args.out_dir, result)
    print(f"Publish execution report written to: {Path(args.out_dir).resolve() / 'reports/promotion-manager/publish-results/publish-execution.json'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run approved official publishing actions.")
    parser.add_argument("--platform", required=True, choices=["github", "youtube"])
    parser.add_argument("--execute", action="store_true", help="Perform the write action. Default is dry run.")
    parser.add_argument("--approval", default="", help=f"Must equal {APPROVAL_PHRASE} when --execute is used.")
    parser.add_argument("--out-dir", default="./promotion-output")

    github = parser.add_argument_group("GitHub")
    github.add_argument("--github-action", choices=["file", "issue", "release"], default="file")
    github.add_argument("--github-repo", help="owner/repo")
    github.add_argument("--branch", default="")
    github.add_argument("--path", help="Repository path for --github-action file.")
    github.add_argument("--commit-message", default="Publish promotion content")
    github.add_argument("--title", default="")
    github.add_argument("--body", default="")
    github.add_argument("--body-file")
    github.add_argument("--content", default="")
    github.add_argument("--content-file")
    github.add_argument("--tag-name", default="")
    github.add_argument("--draft", action="store_true")
    github.add_argument("--prerelease", action="store_true")

    youtube = parser.add_argument_group("YouTube")
    youtube.add_argument("--video-file")
    youtube.add_argument("--description", default="")
    youtube.add_argument("--description-file")
    youtube.add_argument("--tags", default="", help="Comma-separated YouTube tags.")
    youtube.add_argument("--category-id", default="22")
    youtube.add_argument("--privacy-status", default="private", choices=["private", "public", "unlisted"])
    return parser.parse_args()


def build_execution(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "generatedAt": TODAY,
        "platform": args.platform,
        "mode": "execute" if args.execute else "dry_run",
        "approvalRequired": True,
        "approvalPhrase": APPROVAL_PHRASE,
        "approvalProvided": args.approval == APPROVAL_PHRASE,
        "guardrails": [
            "Default mode is dry-run.",
            "Writes require --execute and the exact approval phrase.",
            "Credentials are read from environment variables only and are never written to reports.",
            "Do not bypass captcha, login, risk controls, or platform review.",
        ],
    }


def execute_github(args: argparse.Namespace, execution: dict[str, Any]) -> dict[str, Any]:
    if not args.github_repo:
        return blocked(execution, "missing_github_repo", "Provide --github-repo owner/repo.")
    token_status = "present" if github_token() else "missing"
    plan = {
        **execution,
        "officialApi": "GitHub REST API",
        "action": args.github_action,
        "repository": args.github_repo,
        "credentialStatus": token_status,
        "request": github_request_preview(args),
    }
    validation = validate_write_gate(args, token_status, "GITHUB_TOKEN or GH_TOKEN")
    if validation:
        return {**plan, **validation}
    if args.github_action == "file":
        return {**plan, **github_put_file(args)}
    if args.github_action == "issue":
        return {**plan, **github_create_issue(args)}
    return {**plan, **github_create_release(args)}


def github_request_preview(args: argparse.Namespace) -> dict[str, Any]:
    if args.github_action == "file":
        return {
            "method": "PUT",
            "endpoint": f"/repos/{args.github_repo}/contents/{args.path or ''}",
            "branch": args.branch,
            "message": args.commit_message,
        }
    if args.github_action == "issue":
        return {"method": "POST", "endpoint": f"/repos/{args.github_repo}/issues", "title": args.title}
    return {
        "method": "POST",
        "endpoint": f"/repos/{args.github_repo}/releases",
        "tag_name": args.tag_name,
        "draft": args.draft,
        "prerelease": args.prerelease,
    }


def github_put_file(args: argparse.Namespace) -> dict[str, Any]:
    if not args.path:
        return {"status": "blocked", "reason": "Provide --path for GitHub file publishing."}
    content = read_text_argument(args.content, args.content_file, "--content or --content-file")
    repo_path = urllib.parse.quote(args.path.strip("/"), safe="/")
    get_result = github_api("GET", f"/repos/{args.github_repo}/contents/{repo_path}", query={"ref": args.branch} if args.branch else None)
    sha = ""
    if get_result["status"] == "ready":
        sha = get_result["data"].get("sha", "")
    elif get_result.get("httpStatus") not in (404, None):
        return get_result
    body: dict[str, Any] = {
        "message": args.commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha
    if args.branch:
        body["branch"] = args.branch
    result = github_api("PUT", f"/repos/{args.github_repo}/contents/{repo_path}", body=body)
    if result["status"] != "ready":
        return result
    data = result["data"]
    return {
        "status": "published",
        "publishedUrl": data.get("content", {}).get("html_url", ""),
        "commitSha": data.get("commit", {}).get("sha", ""),
        "evidence": [data.get("content", {}).get("html_url", "")],
    }


def github_create_issue(args: argparse.Namespace) -> dict[str, Any]:
    title = args.title or "Promotion content"
    body = read_text_argument(args.body, args.body_file, "--body or --body-file")
    result = github_api("POST", f"/repos/{args.github_repo}/issues", body={"title": title, "body": body})
    if result["status"] != "ready":
        return result
    data = result["data"]
    return {"status": "published", "publishedUrl": data.get("html_url", ""), "contentId": str(data.get("number", "")), "evidence": [data.get("html_url", "")]}


def github_create_release(args: argparse.Namespace) -> dict[str, Any]:
    if not args.tag_name:
        return {"status": "blocked", "reason": "Provide --tag-name for GitHub release publishing."}
    body = read_text_argument(args.body, args.body_file, "--body or --body-file")
    payload = {
        "tag_name": args.tag_name,
        "name": args.title or args.tag_name,
        "body": body,
        "draft": args.draft,
        "prerelease": args.prerelease,
    }
    result = github_api("POST", f"/repos/{args.github_repo}/releases", body=payload)
    if result["status"] != "ready":
        return result
    data = result["data"]
    return {"status": "published", "publishedUrl": data.get("html_url", ""), "contentId": str(data.get("id", "")), "evidence": [data.get("html_url", "")]}


def github_api(method: str, path: str, body: dict[str, Any] | None = None, query: dict[str, str] | None = None) -> dict[str, Any]:
    url = "https://api.github.com" + path
    if query:
        clean_query = {key: value for key, value in query.items() if value}
        if clean_query:
            url += "?" + urllib.parse.urlencode(clean_query)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "ViralProductPromotionSkill/1.0",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer " + github_token(),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {"status": "ready", "httpStatus": response.status, "data": payload}
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        return {"status": "error", "httpStatus": exc.code, "reason": message[:500]}
    except Exception as exc:  # noqa: BLE001 - CLI reports connector errors compactly.
        return {"status": "error", "reason": str(exc)}


def execute_youtube(args: argparse.Namespace, execution: dict[str, Any]) -> dict[str, Any]:
    token_status = "present" if youtube_token() else "missing"
    plan = {
        **execution,
        "officialApi": "YouTube Data API videos.insert",
        "action": "video_upload",
        "credentialStatus": token_status,
        "request": {
            "method": "POST",
            "endpoint": "/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status",
            "videoFile": args.video_file or "",
            "privacyStatus": args.privacy_status,
            "title": args.title,
        },
    }
    if not args.video_file:
        return blocked(plan, "missing_video_file", "Provide --video-file for YouTube upload.")
    if not args.title:
        return blocked(plan, "missing_title", "Provide --title for YouTube upload.")
    validation = validate_write_gate(args, token_status, "YOUTUBE_OAUTH_ACCESS_TOKEN")
    if validation:
        return {**plan, **validation}
    return {**plan, **youtube_upload(args)}


def youtube_upload(args: argparse.Namespace) -> dict[str, Any]:
    video_path = Path(args.video_file)
    if not video_path.exists():
        return {"status": "blocked", "reason": f"Video file not found: {video_path}"}
    description = read_optional_text_argument(args.description, args.description_file)
    metadata = {
        "snippet": {
            "title": args.title,
            "description": description,
            "tags": split_csv(args.tags),
            "categoryId": args.category_id,
        },
        "status": {"privacyStatus": args.privacy_status},
    }
    boundary = "===============%s==" % uuid.uuid4().hex
    media_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"
    body = build_multipart_body(boundary, metadata, video_path, media_type)
    request = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status",
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + youtube_token(),
            "Content-Type": f"multipart/related; boundary={boundary}",
            "Content-Length": str(len(body)),
            "User-Agent": "ViralProductPromotionSkill/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        return {"status": "error", "httpStatus": exc.code, "reason": message[:500]}
    except Exception as exc:  # noqa: BLE001 - CLI reports connector errors compactly.
        return {"status": "error", "reason": str(exc)}
    video_id = data.get("id", "")
    return {
        "status": "published",
        "publishedUrl": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        "contentId": video_id,
        "evidence": [f"https://www.youtube.com/watch?v={video_id}" if video_id else ""],
    }


def build_multipart_body(boundary: str, metadata: dict[str, Any], video_path: Path, media_type: str) -> bytes:
    metadata_part = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata, ensure_ascii=False)}\r\n"
    ).encode("utf-8")
    media_header = (
        f"--{boundary}\r\n"
        f"Content-Type: {media_type}\r\n\r\n"
    ).encode("utf-8")
    closing = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return metadata_part + media_header + video_path.read_bytes() + closing


def validate_write_gate(args: argparse.Namespace, token_status: str, credential_name: str) -> dict[str, Any] | None:
    if not args.execute:
        return {
            "status": "dry_run",
            "reason": "No write performed. Add --execute with explicit approval after reviewing the request.",
        }
    if args.approval != APPROVAL_PHRASE:
        return {
            "status": "blocked",
            "reason": f"Execution requires --approval {APPROVAL_PHRASE}.",
        }
    if token_status != "present":
        return {
            "status": "blocked",
            "reason": f"Execution requires {credential_name} in the environment.",
        }
    return None


def blocked(execution: dict[str, Any], code: str, reason: str) -> dict[str, Any]:
    return {**execution, "status": "blocked", "code": code, "reason": reason}


def read_text_argument(value: str, file_value: str | None, label: str) -> str:
    text = read_optional_text_argument(value, file_value)
    if not text:
        raise SystemExit(f"Provide {label}.")
    return text


def read_optional_text_argument(value: str, file_value: str | None) -> str:
    if file_value:
        return Path(file_value).read_text(encoding="utf-8")
    return value or ""


def write_result(out_dir: str, result: dict[str, Any]) -> None:
    report_dir = Path(out_dir) / "reports/promotion-manager/publish-results"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "publish-execution.json").write_text(json.dumps(sanitize_result(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (report_dir / "publish-execution.md").write_text(render_markdown(result) + "\n", encoding="utf-8")


def sanitize_result(result: dict[str, Any]) -> dict[str, Any]:
    if "data" in result:
        result = {key: value for key, value in result.items() if key != "data"}
    return result


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Publish Execution",
        "",
        f"- Platform: {result.get('platform')}",
        f"- Status: `{result.get('status')}`",
        f"- Mode: `{result.get('mode')}`",
        f"- Official API: {result.get('officialApi', 'n/a')}",
        f"- Credential status: {result.get('credentialStatus', 'n/a')}",
        f"- Published URL: {result.get('publishedUrl', '') or 'not published'}",
        "",
        "## Request",
    ]
    for key, value in (result.get("request") or {}).items():
        lines.append(f"- {key}: {value}")
    if result.get("reason"):
        lines.extend(["", "## Reason", "", result["reason"]])
    lines.extend(["", "## Guardrails"])
    lines.extend([f"- {item}" for item in result.get("guardrails", [])])
    return "\n".join(lines)


def github_token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def youtube_token() -> str:
    return os.environ.get("YOUTUBE_OAUTH_ACCESS_TOKEN") or ""


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    main()

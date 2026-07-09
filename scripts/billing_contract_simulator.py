#!/usr/bin/env python3
"""Local reference simulator for the browser extension billing contract.

This is not a production payment backend. It is a deterministic local harness
that proves the extension contract can support license validation, usage
reservation, usage commit, and subscription webhook state changes without
storing payment secrets or plaintext license keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "browser-extension" / "billing-contract.json"
REPORT_SUBDIR = Path("reports/promotion-manager/billing-simulator")
STATE_FILENAME = "billing-simulator-state.json"
REPORT_FILENAME = "billing-simulator.json"
MARKDOWN_FILENAME = "billing-simulator.md"
LICENSE_HASH_PREFIX = "enhe-promotion-manager-license:"
ACTIVE_STATUSES = {"active", "trialing"}


def main() -> None:
    args = parse_args()
    response = run_command(args)
    print(json.dumps(response, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate ENHE Promotion Manager billing contract behavior locally.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--contract", default=str(DEFAULT_CONTRACT), help="Path to browser-extension/billing-contract.json.")
    parent.add_argument("--out-dir", default="./promotion-output", help="Output directory for reports.")
    parent.add_argument("--state-file", default="", help="Optional explicit simulator state file.")

    subparsers.add_parser("validate-contract", parents=[parent], help="Validate required billing contract fields.")

    demo = subparsers.add_parser("demo", parents=[parent], help="Run a complete local license, usage, and webhook flow.")
    demo.add_argument("--license-key", default="", help="Optional demo license key. The key is hashed before storage.")
    demo.add_argument("--plan", default="starter", choices=["free", "starter", "growth", "scale"])
    demo.add_argument("--workflow-type", default="research_run")
    demo.add_argument("--idempotency-key", default="demo-idempotency-key")
    demo.add_argument("--input-tokens", type=int, default=180000)
    demo.add_argument("--output-tokens", type=int, default=65000)
    demo.add_argument("--reset-state", action="store_true", help="Start the demo with an empty local state file.")

    issue = subparsers.add_parser("issue-license", parents=[parent], help="Issue or refresh one local license record.")
    issue.add_argument("--license-key", required=True)
    issue.add_argument("--plan", default="starter", choices=["free", "starter", "growth", "scale"])
    issue.add_argument("--email", default="demo@example.com")

    validate = subparsers.add_parser("validate-license", parents=[parent], help="Validate a local license record.")
    validate.add_argument("--license-key", required=True)

    authorize = subparsers.add_parser("authorize-usage", parents=[parent], help="Reserve credits before a hosted run.")
    authorize.add_argument("--license-key", required=True)
    authorize.add_argument("--workflow-type", default="research_run")
    authorize.add_argument("--estimated-credits", type=int)
    authorize.add_argument("--idempotency-key", required=True)

    commit = subparsers.add_parser("commit-usage", parents=[parent], help="Commit actual usage after a hosted run.")
    commit.add_argument("--usage-id", required=True)
    commit.add_argument("--credits-used", type=int)
    commit.add_argument("--input-tokens", type=int, default=0)
    commit.add_argument("--output-tokens", type=int, default=0)
    commit.add_argument("--video-seconds-rendered", type=int, default=0)
    commit.add_argument("--status", default="succeeded", choices=["succeeded", "failed"])

    webhook = subparsers.add_parser("webhook", parents=[parent], help="Apply a simulated payment-provider webhook event.")
    webhook.add_argument("--event", required=True)
    webhook.add_argument("--license-key", default="")
    webhook.add_argument("--plan", default="starter", choices=["free", "starter", "growth", "scale"])
    webhook.add_argument("--email", default="demo@example.com")

    return parser.parse_args()


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    state_path = resolve_state_path(args, out_dir)
    contract_path = Path(args.contract)
    contract = read_json(contract_path)
    contract_validation = validate_contract(contract)

    if args.command == "validate-contract":
        response = {"status": contract_validation["status"], "contract": contract_validation}
        write_report(out_dir, state_path, contract_validation, response)
        return response

    if contract_validation["status"] != "ready":
        response = {"status": "contract_invalid", "contract": contract_validation}
        write_report(out_dir, state_path, contract_validation, response)
        return response

    if getattr(args, "reset_state", False) and state_path.exists():
        state_path.unlink()
    state = load_state(state_path)

    if args.command == "demo":
        response = demo_flow(args, contract, state)
    elif args.command == "issue-license":
        response = {
            "status": "ready",
            "license": issue_license(state, contract, args.license_key, args.plan, args.email),
        }
    elif args.command == "validate-license":
        response = {
            "status": "ready",
            "license": validate_license(state, args.license_key),
        }
    elif args.command == "authorize-usage":
        response = {
            "status": "ready",
            "usage": authorize_usage(
                state,
                contract,
                args.license_key,
                args.workflow_type,
                args.idempotency_key,
                args.estimated_credits,
            ),
        }
    elif args.command == "commit-usage":
        response = {
            "status": "ready",
            "usage": commit_usage(
                state,
                args.usage_id,
                args.credits_used,
                args.input_tokens,
                args.output_tokens,
                args.video_seconds_rendered,
                args.status,
            ),
        }
    elif args.command == "webhook":
        response = {
            "status": "ready",
            "webhook": apply_webhook(state, contract, args.event, args.license_key, args.plan, args.email),
        }
    else:
        raise SystemExit(f"Unsupported command: {args.command}")

    save_state(state_path, state)
    write_report(out_dir, state_path, contract_validation, response, state)
    return response


def demo_flow(args: argparse.Namespace, contract: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    license_key = args.license_key or f"pm_demo_{uuid.uuid4().hex}"
    issued = issue_license(state, contract, license_key, args.plan, "demo@example.com")
    license_before_usage = validate_license(state, license_key)
    authorization = authorize_usage(
        state,
        contract,
        license_key,
        args.workflow_type,
        args.idempotency_key,
        None,
    )
    usage_id = authorization.get("usageId", "")
    committed = commit_usage(
        state,
        usage_id,
        authorization.get("creditsReserved"),
        args.input_tokens,
        args.output_tokens,
        0,
        "succeeded",
    )
    license_after_usage = validate_license(state, license_key)
    webhook = apply_webhook(state, contract, "invoice.payment_succeeded", license_key, args.plan, "demo@example.com")
    license_after_webhook = validate_license(state, license_key)
    return {
        "status": "ready",
        "secretStored": False,
        "license": issued,
        "licenseBeforeUsage": license_before_usage,
        "usageAuthorization": authorization,
        "usageCommit": committed,
        "licenseAfterUsage": license_after_usage,
        "webhook": webhook,
        "licenseAfterWebhook": license_after_webhook,
    }


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for key in [
        "checkoutUrl",
        "customerPortalUrl",
        "licenseEndpoint",
        "usageAuthorizeEndpoint",
        "usageCommitEndpoint",
        "webhookEndpoint",
        "plans",
        "creditCosts",
        "requiredWebhookEvents",
        "securityRules",
    ]:
        if not contract.get(key):
            missing.append(key)
    plans = contract.get("plans") if isinstance(contract.get("plans"), dict) else {}
    for plan in ["free", "starter", "growth", "scale"]:
        if plan not in plans:
            missing.append(f"plans.{plan}")
        elif "includedCredits" not in plans[plan]:
            missing.append(f"plans.{plan}.includedCredits")
    credit_costs = contract.get("creditCosts") if isinstance(contract.get("creditCosts"), dict) else {}
    for workflow in ["command_only", "standard_run", "research_run", "deep_strategy_review", "hosted_mp4_render"]:
        if workflow not in credit_costs:
            missing.append(f"creditCosts.{workflow}")
    events = contract.get("requiredWebhookEvents") if isinstance(contract.get("requiredWebhookEvents"), list) else []
    for event in [
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.payment_succeeded",
        "invoice.payment_failed",
        "entitlements.active_entitlement_summary.updated",
    ]:
        if event not in events:
            missing.append(f"requiredWebhookEvents.{event}")
    return {
        "status": "ready" if not missing else "invalid",
        "missing": missing,
        "version": contract.get("version", ""),
        "provider": contract.get("provider", ""),
    }


def issue_license(
    state: dict[str, Any],
    contract: dict[str, Any],
    license_key: str,
    plan: str,
    email: str,
    status: str = "active",
) -> dict[str, Any]:
    license_hash = hash_license_key(license_key)
    license_id = license_id_from_hash(license_hash)
    quota = included_credits(contract, plan)
    record = {
        "id": license_id,
        "accountEmail": email,
        "licenseKeyHash": license_hash,
        "status": status,
        "plan": plan,
        "creditsRemaining": quota,
        "renewsAt": (date.today() + timedelta(days=30)).isoformat(),
        "updatedAt": utc_now(),
    }
    state["licenses"][license_id] = record
    return license_public_view(record)


def validate_license(state: dict[str, Any], license_key: str) -> dict[str, Any]:
    record = find_license(state, license_key)
    if not record:
        return {
            "active": False,
            "reason": "license_not_found",
            "plan": "",
            "creditsRemaining": 0,
            "renewsAt": "",
        }
    active = record.get("status") in ACTIVE_STATUSES
    return {
        "active": active,
        "reason": "ok" if active else "inactive_license",
        "licenseId": record["id"],
        "plan": title_plan(record.get("plan", "")),
        "creditsRemaining": int(record.get("creditsRemaining", 0)),
        "renewsAt": record.get("renewsAt", ""),
    }


def authorize_usage(
    state: dict[str, Any],
    contract: dict[str, Any],
    license_key: str,
    workflow_type: str,
    idempotency_key: str,
    estimated_credits: int | None,
) -> dict[str, Any]:
    record = find_license(state, license_key)
    if not record:
        return denied_authorization("license_not_found")
    for usage in state["usageLedger"].values():
        if usage.get("licenseId") == record["id"] and usage.get("idempotencyKey") == idempotency_key:
            return usage_authorization_public_view(usage, record, idempotent=True)
    if record.get("status") not in ACTIVE_STATUSES:
        return denied_authorization("inactive_license", record)
    credits = workflow_credits(contract, workflow_type, estimated_credits)
    if int(record.get("creditsRemaining", 0)) < credits:
        return denied_authorization("quota_exceeded", record, credits)
    record["creditsRemaining"] = int(record.get("creditsRemaining", 0)) - credits
    usage_id = f"usage_{uuid.uuid4().hex[:16]}"
    usage = {
        "id": usage_id,
        "licenseId": record["id"],
        "licenseKeyHash": record["licenseKeyHash"],
        "workflowType": workflow_type,
        "creditsReserved": credits,
        "creditsUsed": None,
        "inputTokens": 0,
        "outputTokens": 0,
        "videoSecondsRendered": 0,
        "status": "reserved",
        "idempotencyKey": idempotency_key,
        "createdAt": utc_now(),
        "committedAt": "",
    }
    state["usageLedger"][usage_id] = usage
    return usage_authorization_public_view(usage, record)


def denied_authorization(reason: str, record: dict[str, Any] | None = None, credits: int = 0) -> dict[str, Any]:
    return {
        "allowed": False,
        "usageId": "",
        "creditsReserved": 0,
        "creditsRemainingAfterReservation": int(record.get("creditsRemaining", 0)) if record else 0,
        "reason": reason,
        "requestedCredits": credits,
    }


def commit_usage(
    state: dict[str, Any],
    usage_id: str,
    credits_used: int | None,
    input_tokens: int,
    output_tokens: int,
    video_seconds_rendered: int,
    status: str,
) -> dict[str, Any]:
    usage = state["usageLedger"].get(usage_id)
    if not usage:
        return {"status": "not_found", "usageId": usage_id}
    if usage.get("status") in {"succeeded", "failed"}:
        return usage_commit_public_view(usage, "idempotent")
    record = state["licenses"].get(usage["licenseId"])
    reserved = int(usage.get("creditsReserved", 0))
    requested_used = reserved if credits_used is None else max(0, int(credits_used))
    actual_used = min(requested_used, reserved) if status == "succeeded" else 0
    refund = reserved - actual_used
    if record and refund > 0:
        record["creditsRemaining"] = int(record.get("creditsRemaining", 0)) + refund
        record["updatedAt"] = utc_now()
    usage["creditsUsed"] = actual_used
    usage["inputTokens"] = max(0, int(input_tokens))
    usage["outputTokens"] = max(0, int(output_tokens))
    usage["videoSecondsRendered"] = max(0, int(video_seconds_rendered))
    usage["status"] = status
    usage["committedAt"] = utc_now()
    return usage_commit_public_view(usage, "committed", refund)


def apply_webhook(
    state: dict[str, Any],
    contract: dict[str, Any],
    event: str,
    license_key: str,
    plan: str,
    email: str,
) -> dict[str, Any]:
    required_events = contract.get("requiredWebhookEvents") if isinstance(contract.get("requiredWebhookEvents"), list) else []
    if event not in required_events:
        return {"status": "unsupported_event", "event": event}
    record = find_license(state, license_key) if license_key else None
    if not record and license_key and event in {
        "checkout.session.completed",
        "customer.subscription.created",
        "invoice.payment_succeeded",
    }:
        issued = issue_license(state, contract, license_key, plan, email)
        record = state["licenses"][issued["licenseId"]]
    if not record:
        return {"status": "license_required", "event": event}

    if event in {"checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"}:
        record["status"] = "active"
        record["plan"] = plan
    elif event == "invoice.payment_succeeded":
        record["status"] = "active"
        record["plan"] = plan
        record["creditsRemaining"] = included_credits(contract, plan)
        record["renewsAt"] = (date.today() + timedelta(days=30)).isoformat()
    elif event == "invoice.payment_failed":
        record["status"] = "past_due"
    elif event == "customer.subscription.deleted":
        record["status"] = "canceled"
        record["creditsRemaining"] = 0
    elif event == "entitlements.active_entitlement_summary.updated":
        record["status"] = "active" if record.get("status") in ACTIVE_STATUSES else record.get("status", "inactive")
    record["updatedAt"] = utc_now()

    event_record = {
        "id": f"evt_{uuid.uuid4().hex[:16]}",
        "event": event,
        "licenseId": record["id"],
        "plan": record.get("plan", ""),
        "statusAfterEvent": record.get("status", ""),
        "handledAt": utc_now(),
    }
    state["events"].append(event_record)
    return {"status": "handled", **event_record, "license": license_public_view(record)}


def workflow_credits(contract: dict[str, Any], workflow_type: str, estimated_credits: int | None) -> int:
    if estimated_credits is not None:
        return max(0, int(estimated_credits))
    credit_costs = contract.get("creditCosts") if isinstance(contract.get("creditCosts"), dict) else {}
    if workflow_type not in credit_costs:
        raise SystemExit(f"Unknown workflow type in billing contract: {workflow_type}")
    return max(0, int(credit_costs[workflow_type]))


def included_credits(contract: dict[str, Any], plan: str) -> int:
    plans = contract.get("plans") if isinstance(contract.get("plans"), dict) else {}
    plan_record = plans.get(plan)
    if not isinstance(plan_record, dict):
        raise SystemExit(f"Unknown plan in billing contract: {plan}")
    return max(0, int(plan_record.get("includedCredits", 0)))


def license_public_view(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "licenseId": record["id"],
        "licenseKeyHash": short_hash(record["licenseKeyHash"]),
        "status": record.get("status", ""),
        "plan": title_plan(record.get("plan", "")),
        "creditsRemaining": int(record.get("creditsRemaining", 0)),
        "renewsAt": record.get("renewsAt", ""),
        "active": record.get("status") in ACTIVE_STATUSES,
    }


def usage_authorization_public_view(
    usage: dict[str, Any],
    record: dict[str, Any],
    idempotent: bool = False,
) -> dict[str, Any]:
    return {
        "allowed": True,
        "usageId": usage["id"],
        "creditsReserved": int(usage.get("creditsReserved", 0)),
        "creditsRemainingAfterReservation": int(record.get("creditsRemaining", 0)),
        "reason": "ok",
        "idempotent": idempotent,
    }


def usage_commit_public_view(usage: dict[str, Any], result: str, credits_refunded: int = 0) -> dict[str, Any]:
    return {
        "result": result,
        "usageId": usage["id"],
        "status": usage.get("status", ""),
        "creditsReserved": int(usage.get("creditsReserved", 0)),
        "creditsUsed": int(usage.get("creditsUsed") or 0),
        "creditsRefunded": credits_refunded,
        "inputTokens": int(usage.get("inputTokens", 0)),
        "outputTokens": int(usage.get("outputTokens", 0)),
        "videoSecondsRendered": int(usage.get("videoSecondsRendered", 0)),
    }


def find_license(state: dict[str, Any], license_key: str) -> dict[str, Any] | None:
    license_hash = hash_license_key(license_key)
    license_id = license_id_from_hash(license_hash)
    record = state["licenses"].get(license_id)
    if record and record.get("licenseKeyHash") == license_hash:
        return record
    return None


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return empty_state()
    if not isinstance(state, dict):
        return empty_state()
    state.setdefault("version", "0.1.0")
    state.setdefault("licenses", {})
    state.setdefault("usageLedger", {})
    state.setdefault("events", [])
    return state


def empty_state() -> dict[str, Any]:
    return {"version": "0.1.0", "licenses": {}, "usageLedger": {}, "events": []}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(
    out_dir: Path,
    state_path: Path,
    contract_validation: dict[str, Any],
    response: dict[str, Any],
    state: dict[str, Any] | None = None,
) -> None:
    directory = out_dir / REPORT_SUBDIR
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": utc_now(),
        "status": response.get("status", "unknown"),
        "contract": contract_validation,
        "stateFile": str(state_path),
        "secretStored": False,
        "summary": state_summary(state or load_state(state_path)),
        "response": response,
        "guardrails": [
            "No payment provider secrets are accepted or stored by this simulator.",
            "Plaintext license keys are never written to state or reports.",
            "Production backends must add authentication, database transactions, salted hashing, and webhook signature verification.",
        ],
    }
    (directory / REPORT_FILENAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / MARKDOWN_FILENAME).write_text(render_markdown(payload) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Billing Contract Simulator",
        "",
        f"- Generated: {report['generatedAt']}",
        f"- Status: `{report['status']}`",
        f"- Contract: `{report['contract']['status']}`",
        f"- State file: {report['stateFile']}",
        f"- Plaintext license stored: {report['secretStored']}",
        "",
        "## Summary",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Guardrails"])
    lines.extend(f"- {item}" for item in report["guardrails"])
    return "\n".join(lines)


def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    licenses = state.get("licenses") if isinstance(state.get("licenses"), dict) else {}
    ledger = state.get("usageLedger") if isinstance(state.get("usageLedger"), dict) else {}
    events = state.get("events") if isinstance(state.get("events"), list) else []
    return {
        "licenses": len(licenses),
        "activeLicenses": sum(1 for record in licenses.values() if record.get("status") in ACTIVE_STATUSES),
        "usageRecords": len(ledger),
        "committedUsageRecords": sum(1 for record in ledger.values() if record.get("status") in {"succeeded", "failed"}),
        "webhookEvents": len(events),
    }


def resolve_state_path(args: argparse.Namespace, out_dir: Path) -> Path:
    if args.state_file:
        return Path(args.state_file)
    return out_dir / REPORT_SUBDIR / STATE_FILENAME


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def hash_license_key(license_key: str) -> str:
    return hashlib.sha256(f"{LICENSE_HASH_PREFIX}{license_key}".encode("utf-8")).hexdigest()


def license_id_from_hash(license_hash: str) -> str:
    return f"lic_{license_hash[:16]}"


def short_hash(license_hash: str) -> str:
    return f"{license_hash[:10]}...{license_hash[-6:]}"


def title_plan(plan: str) -> str:
    return str(plan or "").strip().title()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Public distribution identity, file boundaries, and safety checks."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


VERSION = "0.5.3"
PUBLISHED_STORE_VERSION = "0.5.2"
STORE_ITEM_ID = "dloklkbnmoigemnfigbkibogmgbieppl"
PUBLIC_REPOSITORY = "hqwzhu/enhe-promotion-manager"
PRODUCT_EN = "ENHE Product Promo Maker"
PRODUCT_ZH = "ENHE 产品推广素材生成器"
PRODUCT_PROMISE_EN = "Turn product pages into promotional copy, video scripts, and publishing assets."
PRODUCT_PROMISE_ZH = "把产品网页变成推广文案、视频脚本和发布素材。"

NON_PAYMENT_COMMANDS = (
    "automation_scheduler.py",
    "browser_publish_session.py",
    "final_capability_readiness.py",
    "launch_unlock_pack.py",
    "performance_monitor.py",
    "promotion_manager.py",
    "real_evidence_inbox.py",
    "real_evidence_inbox_setup.py",
    "skill_entry.py",
    "viral_evidence_inbox.py",
    "viral_evidence_inbox_setup.py",
)

_SKILL_STANDALONES = ("SKILL.md", "LICENSE", "requirements-youtube.txt")
_DISTRIBUTION_ONLY_SCRIPTS = {
    "build_public_distribution.py",
    "distribution_contract.py",
    "test_public_distribution.py",
}
_SKILL_FORBIDDEN_PARTS = {
    ".venv",
    "backend",
    "browser-extension",
    "dependencies",
    "deploy",
    "node_modules",
    "promotion-output",
}
_MAX_TEXT_FILE_SIZE = 2_000_000
_SECRET_PATTERNS = (
    (
        "github_token",
        re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{36,})\b"),
    ),
    ("firecrawl_key", re.compile(r"\bfc-[A-Za-z0-9_-]{20,}\b")),
    (
        "private_key",
        re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    ),
    ("live_license", re.compile(r"\bpm_live_[A-Za-z0-9]{20,}\b")),
)


def extension_command_refs(text: str) -> list[str]:
    """Return unique Python script names referenced by extension commands."""
    return sorted(set(re.findall(r"python scripts\\+([A-Za-z0-9_]+\.py)", text)))


def _is_env_part(part: str) -> bool:
    lowered = part.lower()
    return lowered == ".env" or lowered.startswith(".env.")


def _skill_path_allowed(relative: Path) -> bool:
    lowered_parts = {part.lower() for part in relative.parts}
    return not (
        lowered_parts.intersection(_SKILL_FORBIDDEN_PARTS)
        or any(_is_env_part(part) for part in relative.parts)
    )


def skill_files(root: Path) -> list[Path]:
    """List source files allowed in the public Skill package."""
    files = [Path(name) for name in _SKILL_STANDALONES if (root / name).is_file()]

    for path in (root / "references").rglob("*.md"):
        relative = path.relative_to(root)
        if path.is_file() and _skill_path_allowed(relative):
            files.append(relative)

    for path in (root / "scripts").rglob("*.py"):
        relative = path.relative_to(root)
        if (
            path.is_file()
            and path.name not in _DISTRIBUTION_ONLY_SCRIPTS
            and _skill_path_allowed(relative)
        ):
            files.append(relative)

    fixture_directory = root / "scripts" / "fixtures" / "mediacrawler"
    for path in fixture_directory.glob("*.jsonl"):
        relative = path.relative_to(root)
        if path.is_file() and _skill_path_allowed(relative):
            files.append(relative)

    return sorted(set(files), key=lambda item: item.as_posix())


def extension_files(root: Path) -> list[Path]:
    """List visible browser extension files relative to its source directory."""
    extension = root / "browser-extension"
    return sorted(
        (
            path.relative_to(extension)
            for path in extension.rglob("*")
            if path.is_file()
            and not any(part.startswith(".") for part in path.relative_to(extension).parts)
        ),
        key=lambda item: item.as_posix(),
    )


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(root: Path) -> str:
    """Return a deterministic digest of relative file paths and bytes."""
    digest = hashlib.sha256()
    paths = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _is_forbidden_path_part(part: str) -> bool:
    lowered = part.lower()
    if _is_env_part(lowered):
        return True
    if lowered in {
        ".venv",
        "node_modules",
        "promotion-output",
        "cookies.json",
        "__pycache__",
    }:
        return True

    normalized = lowered.strip(".").replace("_", "-").replace(" ", "-")
    return (
        normalized.startswith("chrome-profile")
        or normalized.startswith("chrome-user-data")
        or normalized in {"user-data", "user-data-dir"}
        or ("mediacrawler" in normalized and "backup" in normalized)
    )


def scan_forbidden(root: Path) -> list[dict[str, str]]:
    """Find private paths and secret patterns without returning secret values."""
    violations: list[dict[str, str]] = []
    paths = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
    for path in paths:
        relative = path.relative_to(root)
        if any(_is_forbidden_path_part(part) for part in relative.parts):
            violations.append({"path": relative.as_posix(), "rule": "forbidden_path"})
            continue
        if not path.is_file():
            continue
        try:
            if path.stat().st_size > _MAX_TEXT_FILE_SIZE:
                continue
            content = path.read_bytes()
        except OSError:
            continue
        if b"\0" in content:
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for rule, pattern in _SECRET_PATTERNS:
            if pattern.search(text):
                violations.append({"path": relative.as_posix(), "rule": rule})
    return violations

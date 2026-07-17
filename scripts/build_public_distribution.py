#!/usr/bin/env python3
"""Assemble the reviewed source into the standalone public repository."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import distribution_contract as contract


VERSION = contract.VERSION
SKILL_TARGET = Path("skill/viral-product-copy-video-generator")
EXTENSION_TARGET = Path("extension/chrome")
_GENERATED_TEMPLATE_PARTS = {"__pycache__", ".pytest_cache", "dist", "tmp-release-download"}


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(flag and attributes & flag)


def copy_file(source: Path, target: Path) -> None:
    """Copy bytes and metadata, creating only the requested destination path."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _copy_templates(source: Path, target: Path) -> None:
    template_root = source / "distribution"
    if not template_root.exists():
        return
    for path in contract._strict_files(source, template_root):
        relative = path.relative_to(template_root)
        if any(part in _GENERATED_TEMPLATE_PARTS or part.endswith(".pyc") for part in relative.parts):
            continue
        copy_file(path, target / relative)


def _copy_allowlisted_files(source: Path, target: Path) -> None:
    skill_files = contract.skill_files(source)
    extension_files = contract.extension_files(source)
    if Path("LICENSE") not in skill_files:
        raise RuntimeError("required public source is missing: LICENSE")
    distribution_contract = source / "scripts" / "distribution_contract.py"
    if not distribution_contract.is_file():
        raise RuntimeError("required public source is missing: scripts/distribution_contract.py")
    copy_file(source / "LICENSE", target / "LICENSE")
    copy_file(
        distribution_contract,
        target / "scripts" / "distribution_contract.py",
    )
    skill_target = target / SKILL_TARGET
    for relative in skill_files:
        copy_file(source / relative, skill_target / relative)
    extension_target = target / EXTENSION_TARGET
    for relative in extension_files:
        copy_file(source / "browser-extension" / relative, extension_target / relative)


def _write_manifests(target: Path, source_commit: str) -> None:
    commands = list(contract.NON_PAYMENT_COMMANDS)
    write_json(
        target / SKILL_TARGET / "component-manifest.json",
        {
            "name": "viral-product-copy-video-generator",
            "version": VERSION,
            "sourceCommit": source_commit,
            "runtime": "Python 3.11 and Codex",
            "entryPoints": ["SKILL.md", "scripts/skill_entry.py"],
            "capabilityIds": commands,
        },
    )
    write_json(
        target / EXTENSION_TARGET / "component-manifest.json",
        {
            "name": contract.PRODUCT_EN,
            "version": VERSION,
            "sourceCommit": source_commit,
            "runtime": "Chrome Manifest V3",
            "entryPoints": ["manifest.json", "popup.html", "popup.js"],
            "nonPaymentCapabilityIds": commands,
            "billingParityIncluded": False,
        },
    )
    write_json(
        target / "release-manifest.json",
        {
            "version": VERSION,
            "sourceRepository": "https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator",
            "sourceCommit": source_commit,
            "publicRepository": f"https://github.com/{contract.PUBLIC_REPOSITORY}",
            "treeDigest": "pending-final-build",
            "skillArchive": f"enhe-product-promo-maker-skill-{VERSION}.zip",
            "extensionArchive": f"enhe-promotion-manager-extension-{VERSION}.zip",
            "chromeWebStore": {
                "itemId": contract.STORE_ITEM_ID,
                "publishedVersion": contract.PUBLISHED_STORE_VERSION,
                "submittedVersion": None,
                "status": "not_submitted",
            },
            "syncAudit": {
                "scope": "non-payment extension commands to shipped Skill scripts",
                "excluded": [
                    "payment",
                    "subscription",
                    "license purchase",
                    "credits",
                    "billing backend",
                ],
                "commands": commands,
                "status": "ready",
            },
            "artifacts": {},
            "verification": {
                "status": "pending",
                "commands": [
                    "python scripts/build_release.py --validated-extension-zip dist/validated/enhe-promotion-manager-0.5.3.zip",
                    "python scripts/verify_distribution.py",
                    "python -m unittest discover -s tests -v",
                ],
            },
        },
    )


def build_repository(source: Path, target: Path, source_commit: str) -> None:
    """Build a new public tree without overwriting unknown destination content."""
    source = Path(source).absolute()
    target = Path(target).absolute()
    if target.exists():
        if _is_link_or_reparse(target):
            raise RuntimeError(f"target directory is an unsafe link or reparse point: {target}")
        if not target.is_dir():
            raise RuntimeError(f"target path is not a directory: {target}")
        if any(target.iterdir()):
            raise RuntimeError(f"target directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)

    _copy_templates(source, target)
    _copy_allowlisted_files(source, target)
    popup_path = source / "browser-extension" / "popup.js"
    popup = popup_path.read_text(encoding="utf-8")
    commands = contract.extension_command_refs(popup)
    shipped = target / SKILL_TARGET / "scripts"
    missing = [name for name in contract.NON_PAYMENT_COMMANDS if not (shipped / name).is_file()]
    if tuple(commands) != contract.NON_PAYMENT_COMMANDS or missing:
        raise RuntimeError(f"non-payment command drift: commands={commands}, missing={missing}")

    _write_manifests(target, source_commit)
    violations = contract.scan_forbidden(target)
    if violations:
        raise RuntimeError(f"forbidden public content: {violations}")


def clean_source_commit(source: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=source,
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        raise RuntimeError("source repository must be clean before public distribution build")
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--validated-extension-zip", required=True)
    args = parser.parse_args()

    source_commit = clean_source_commit(ROOT)
    validated_zip = Path(args.validated_extension_zip).resolve()
    if not validated_zip.is_file():
        raise RuntimeError(f"validated extension zip is missing: {validated_zip}")
    target = Path(args.output_dir).absolute()
    build_repository(ROOT, target, source_commit)
    copy_file(validated_zip, target / "dist" / "validated" / f"enhe-promotion-manager-{VERSION}.zip")
    print(f"Public repository assembled at: {target}")


if __name__ == "__main__":
    main()

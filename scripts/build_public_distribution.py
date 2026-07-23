#!/usr/bin/env python3
"""Assemble the reviewed source into the standalone public repository."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import distribution_contract as contract


VERSION = contract.VERSION
SKILL_TARGET = Path("skill/viral-product-copy-video-generator")
EXTENSION_TARGET = Path("extension/chrome")
_GENERATED_TEMPLATE_PARTS = {"__pycache__", ".pytest_cache", "dist", "tmp-release-download"}
_GENERATED_COMPONENT_PARTS = _GENERATED_TEMPLATE_PARTS


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(flag and attributes & flag)


def _validate_target_ancestors(target: Path) -> None:
    current = target
    while True:
        try:
            current.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise RuntimeError(f"unreadable target ancestor: {current}") from exc
        else:
            if _is_link_or_reparse(current):
                raise RuntimeError(f"unsafe link or reparse target ancestor: {current}")
        if current.parent == current:
            return
        current = current.parent


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


def _reject_generated_component_paths(target: Path) -> None:
    for component in (target / SKILL_TARGET, target / EXTENSION_TARGET):
        for path in contract._strict_files(target, component):
            relative = path.relative_to(component)
            if (
                any(part in _GENERATED_COMPONENT_PARTS for part in relative.parts)
                or path.suffix == ".pyc"
            ):
                raise RuntimeError(
                    f"generated or cache path is forbidden in public component: {relative.as_posix()}"
                )


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
                "status": "published",
                "listingUrl": contract.STORE_LISTING_URL,
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
                    f"python scripts/build_release.py --validated-extension-zip dist/validated/enhe-promotion-manager-{VERSION}.zip",
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
    _validate_target_ancestors(target)
    if target.exists():
        if not target.is_dir():
            raise RuntimeError(f"target path is not a directory: {target}")
        if any(target.iterdir()):
            raise RuntimeError(f"target directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    _validate_target_ancestors(target)

    _copy_templates(source, target)
    _copy_allowlisted_files(source, target)
    _reject_generated_component_paths(target)
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


def snapshot_committed_source(source: Path, snapshot: Path, source_commit: str) -> None:
    """Extract only bytes tracked by the selected commit into a new directory."""
    source = Path(source).absolute()
    snapshot = Path(snapshot).absolute()
    if snapshot.exists() and any(snapshot.iterdir()):
        raise RuntimeError(f"snapshot directory is not empty: {snapshot}")
    snapshot.mkdir(parents=True, exist_ok=True)
    snapshot_root = snapshot.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="public-source-archive-") as temp:
        archive_path = Path(temp) / "source.zip"
        subprocess.run(
            [
                "git",
                "archive",
                "--format=zip",
                f"--output={archive_path}",
                source_commit,
            ],
            cwd=source,
            check=True,
            capture_output=True,
        )
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                relative = PurePosixPath(info.filename)
                if (
                    relative.is_absolute()
                    or "\\" in info.filename
                    or any(part in {"", ".", ".."} for part in relative.parts)
                ):
                    raise RuntimeError("git archive contains an unsafe member path")
                mode = info.external_attr >> 16
                if stat.S_IFMT(mode) == stat.S_IFLNK:
                    raise RuntimeError("git archive contains a symbolic link")
                destination = snapshot.joinpath(*relative.parts)
                if not destination.resolve(strict=False).is_relative_to(snapshot_root):
                    raise RuntimeError("git archive member escapes the snapshot root")
                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source_handle, destination.open("xb") as target_handle:
                    shutil.copyfileobj(source_handle, target_handle)


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
    with tempfile.TemporaryDirectory(prefix="public-source-snapshot-") as temp:
        snapshot = Path(temp) / "source"
        snapshot_committed_source(ROOT, snapshot, source_commit)
        build_repository(snapshot, target, source_commit)
    copy_file(validated_zip, target / "dist" / "validated" / f"enhe-promotion-manager-{VERSION}.zip")
    if clean_source_commit(ROOT) != source_commit:
        raise RuntimeError("source repository changed during public distribution build")
    print(f"Public repository assembled at: {target}")


if __name__ == "__main__":
    main()

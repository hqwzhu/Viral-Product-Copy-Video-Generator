#!/usr/bin/env python3
"""Build deterministic public release artifacts from the assembled repository."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

import distribution_contract as contract
import generate_checksums
import verify_distribution


ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build_skill_zip(output: Path) -> None:
    source = ROOT / "skill" / "viral-product-copy-video-generator"
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(
        contract._strict_files(ROOT, source),
        key=lambda path: path.relative_to(source).as_posix(),
    )
    with zipfile.ZipFile(output, "w") as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            add_bytes(
                archive,
                f"viral-product-copy-video-generator/{relative}",
                path.read_bytes(),
            )


def _extension_source_files() -> dict[str, Path]:
    source = ROOT / "extension" / "chrome"
    return {
        path.relative_to(source).as_posix(): path
        for path in contract._strict_files(ROOT, source)
        if path.name != "component-manifest.json"
    }


def copy_validated_extension(source_zip: Path, output: Path) -> None:
    expected = _extension_source_files()
    with zipfile.ZipFile(source_zip) as archive:
        try:
            names = verify_distribution._safe_zip_members(archive)
        except ValueError as exc:
            raise RuntimeError("validated extension ZIP contains an unsafe member path") from exc
        if (
            len(names) != len(set(names))
            or set(names) != set(expected)
            or "manifest.json" not in names
            or "component-manifest.json" in names
        ):
            raise RuntimeError("validated extension ZIP member list differs from public source")
        for name, path in expected.items():
            if archive.read(name) != path.read_bytes():
                raise RuntimeError(f"validated extension ZIP differs from public source: {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_zip, output)


def canonical_tree_digest(release: dict) -> str:
    return verify_distribution.canonical_tree_digest(ROOT, release)


def build_release(validated_extension_zip: Path) -> Path:
    if not validated_extension_zip.is_file():
        raise FileNotFoundError(
            f"validated extension ZIP is missing: {validated_extension_zip}"
        )
    release_path = ROOT / "release-manifest.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if release.get("version") != contract.VERSION:
        raise RuntimeError("release version differs from distribution contract")
    if release.get("skillArchive") != verify_distribution.EXPECTED_SKILL_ARCHIVE:
        raise RuntimeError("release Skill archive name differs from the distribution contract")
    if release.get("extensionArchive") != verify_distribution.EXPECTED_EXTENSION_ARCHIVE:
        raise RuntimeError("release extension archive name differs from the distribution contract")
    component_errors = verify_distribution.verify_component_paths(ROOT)
    if component_errors:
        raise RuntimeError("public component contains generated or unsafe paths")

    dist = ROOT / "dist" / f"v{contract.VERSION}"
    dist.mkdir(parents=True, exist_ok=True)
    skill_zip = dist / release["skillArchive"]
    extension_zip = dist / release["extensionArchive"]
    build_skill_zip(skill_zip)
    copy_validated_extension(validated_extension_zip, extension_zip)

    release["artifacts"] = {
        path.name: {
            "bytes": path.stat().st_size,
            "sha256": contract.sha256_file(path).upper(),
        }
        for path in (skill_zip, extension_zip)
    }
    release["treeDigest"] = canonical_tree_digest(release)
    release["verification"]["status"] = "built"
    write_json(release_path, release)

    errors = verify_distribution.validate(ROOT, check_checksums=False)
    if errors:
        raise RuntimeError("pre-checksum verification failed: " + "; ".join(errors))

    release["verification"]["status"] = "ready"
    write_json(release_path, release)
    generate_checksums.write_checksums(
        ROOT,
        [
            skill_zip.relative_to(ROOT).as_posix(),
            extension_zip.relative_to(ROOT).as_posix(),
            "release-manifest.json",
        ],
        ROOT / "SHA256SUMS",
    )
    errors = verify_distribution.validate(ROOT)
    if errors:
        raise RuntimeError("final distribution verification failed: " + "; ".join(errors))
    return dist


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validated-extension-zip", required=True)
    args = parser.parse_args()
    dist = build_release(Path(args.validated_extension_zip).resolve())
    print(f"Release assets ready: {dist}")


if __name__ == "__main__":
    main()

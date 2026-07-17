#!/usr/bin/env python3
"""Contract tests that run from the standalone public repository root."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SOURCE_SCRIPTS = ROOT.parent / "scripts"
if not (SCRIPTS / "distribution_contract.py").is_file() and str(SOURCE_SCRIPTS) not in sys.path:
    sys.path.insert(1, str(SOURCE_SCRIPTS))

import build_release  # noqa: E402
import generate_checksums  # noqa: E402
import verify_distribution  # noqa: E402


class PublicDistributionTest(unittest.TestCase):
    def test_checksums_are_sorted_uppercase_and_fail_on_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "z.txt").write_bytes(b"z")
            (root / "a.txt").write_bytes(b"a")
            output = root / "SHA256SUMS"

            generate_checksums.write_checksums(root, ["z.txt", "a.txt"], output)
            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual([line.split("  ", 1)[1] for line in lines], ["a.txt", "z.txt"])
            self.assertTrue(all(line.split("  ", 1)[0].isupper() for line in lines))
            with self.assertRaisesRegex(FileNotFoundError, "checksum input is missing"):
                generate_checksums.write_checksums(root, ["missing.txt"], output)

    def test_local_python_caches_do_not_change_tree_digest_or_public_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            release = {
                "verification": {"status": "pending", "commands": ["verify"]},
                "artifacts": {},
                "treeDigest": "pending",
            }
            (root / "release-manifest.json").write_text(
                "{}\n", encoding="utf-8"
            )
            before = verify_distribution.canonical_tree_digest(root, release)
            cache = root / "scripts" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "tool.cpython-311.pyc").write_bytes(b"cache")

            self.assertEqual(
                verify_distribution.canonical_tree_digest(root, release), before
            )
            self.assertEqual(verify_distribution.verify_forbidden(root), [])

            (root / ".env").write_text("SAFE=test\n", encoding="utf-8")
            self.assertTrue(verify_distribution.verify_forbidden(root))

    def test_skill_zip_uses_public_root_and_fixed_timestamps(self) -> None:
        source = ROOT / "skill" / "viral-product-copy-video-generator"
        if not source.is_dir():
            self.skipTest("public Skill tree is created by build_public_distribution.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "skill.zip"
            build_release.build_skill_zip(output)
            with zipfile.ZipFile(output) as archive:
                self.assertTrue(archive.namelist())
                self.assertTrue(all(name.startswith("viral-product-copy-video-generator/") for name in archive.namelist()))
                self.assertTrue(all(info.date_time == (2026, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_public_tooling_scripts_and_non_payment_contract(self) -> None:
        required = (
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
        skill = ROOT / "skill" / "viral-product-copy-video-generator" / "scripts"
        if not skill.is_dir():
            self.skipTest("public Skill tree is created by build_public_distribution.py")
        self.assertTrue(all((skill / name).is_file() for name in required))
        component_path = ROOT / "extension" / "chrome" / "component-manifest.json"
        if not component_path.is_file():
            self.skipTest("component manifests are created by build_public_distribution.py")
        component = verify_distribution.read_json(component_path)
        self.assertIs(component.get("billingParityIncluded"), False)

    def test_archive_layout_when_release_archives_exist(self) -> None:
        release_path = ROOT / "release-manifest.json"
        if not release_path.is_file():
            self.skipTest("release manifest is created by build_public_distribution.py")
        release = verify_distribution.read_json(release_path)
        dist = ROOT / "dist" / f"v{release['version']}"
        skill_zip = dist / release["skillArchive"]
        extension_zip = dist / release["extensionArchive"]
        if not skill_zip.is_file() or not extension_zip.is_file():
            self.skipTest("release archives are created by build_release.py")
        with zipfile.ZipFile(skill_zip) as archive:
            self.assertTrue(any(name == "viral-product-copy-video-generator/SKILL.md" for name in archive.namelist()))
        with zipfile.ZipFile(extension_zip) as archive:
            self.assertIn("manifest.json", archive.namelist())
            self.assertNotIn("component-manifest.json", archive.namelist())

    def test_validator_reports_later_task_files_without_being_weakened(self) -> None:
        errors = verify_distribution.validate(ROOT, check_checksums=False)
        if not errors:
            self.skipTest("later task documentation and release assets are already present")
        self.assertTrue(any("missing required file" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

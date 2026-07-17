#!/usr/bin/env python3
"""Tests for the public distribution boundary."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import distribution_contract as contract


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_NAMES = {
    "douyin-comments.jsonl",
    "douyin-contents.jsonl",
    "xiaohongshu-comments.jsonl",
    "xiaohongshu-contents.jsonl",
    "zhihu-comments.jsonl",
    "zhihu-contents.jsonl",
}
EXPECTED_COMMANDS = (
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


def write_text(root: Path, relative: str, text: str = "test\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class DistributionContractTest(unittest.TestCase):
    def test_public_identity_constants_are_exact(self) -> None:
        self.assertEqual(contract.VERSION, "0.5.3")
        self.assertEqual(contract.PUBLISHED_STORE_VERSION, "0.5.2")
        self.assertEqual(contract.STORE_ITEM_ID, "dloklkbnmoigemnfigbkibogmgbieppl")
        self.assertEqual(contract.PUBLIC_REPOSITORY, "hqwzhu/enhe-promotion-manager")
        self.assertEqual(contract.PRODUCT_EN, "ENHE Product Promo Maker")
        self.assertEqual(contract.PRODUCT_ZH, "ENHE 产品推广素材生成器")
        self.assertEqual(
            contract.PRODUCT_PROMISE_EN,
            "Turn product pages into promotional copy, video scripts, and publishing assets.",
        )
        self.assertEqual(contract.PRODUCT_PROMISE_ZH, "把产品网页变成推广文案、视频脚本和发布素材。")
        self.assertEqual(contract.NON_PAYMENT_COMMANDS, EXPECTED_COMMANDS)
        self.assertEqual(tuple(sorted(contract.NON_PAYMENT_COMMANDS)), contract.NON_PAYMENT_COMMANDS)

    def test_extension_commands_match_the_approved_non_payment_contract(self) -> None:
        popup = (ROOT / "browser-extension" / "popup.js").read_text(encoding="utf-8")
        self.assertEqual(contract.extension_command_refs(popup), list(EXPECTED_COMMANDS))
        for script_name in contract.NON_PAYMENT_COMMANDS:
            self.assertTrue((ROOT / "scripts" / script_name).is_file(), script_name)

    def test_skill_allowlist_contains_runtime_docs_and_only_sanitized_fixtures(self) -> None:
        names = {path.as_posix() for path in contract.skill_files(ROOT)}
        required = {
            "SKILL.md",
            "LICENSE",
            "requirements-youtube.txt",
            "references/workflow.md",
            "scripts/skill_entry.py",
        }
        self.assertLessEqual(required, names)
        fixture_prefix = "scripts/fixtures/mediacrawler/"
        actual_fixtures = {
            name.removeprefix(fixture_prefix)
            for name in names
            if name.startswith(fixture_prefix) and name.endswith(".jsonl")
        }
        self.assertEqual(actual_fixtures, FIXTURE_NAMES)
        self.assertFalse(any(name.startswith("browser-extension/") for name in names))
        self.assertFalse(any(name.startswith("backend/") for name in names))
        self.assertFalse(any(name.startswith("deploy/") for name in names))
        self.assertFalse(any("promotion-output" in name for name in names))
        for distribution_script in (
            "scripts/build_public_distribution.py",
            "scripts/distribution_contract.py",
            "scripts/test_public_distribution.py",
        ):
            self.assertNotIn(distribution_script, names)

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            for standalone in ("SKILL.md", "LICENSE", "requirements-youtube.txt"):
                write_text(source, standalone)
            write_text(source, "references/guide.md")
            write_text(source, "references/nested/deep.md")
            write_text(source, "scripts/runtime.py")
            write_text(source, "scripts/nested/runtime.py")
            write_text(source, "scripts/build_public_distribution.py")
            write_text(source, "scripts/distribution_contract.py")
            write_text(source, "scripts/test_public_distribution.py")
            write_text(source, "scripts/unrelated.jsonl")
            write_text(source, "scripts/nested/private.jsonl")
            write_text(source, "scripts/fixtures/mediacrawler/safe.jsonl")
            write_text(source, "scripts/fixtures/mediacrawler/nested/private.jsonl")
            write_text(source, "scripts/.venv/private.py")
            write_text(source, "scripts/dependencies/private.py")
            write_text(source, "scripts/promotion-output/private.py")
            write_text(source, "backend/private.py")
            write_text(source, "deploy/private.py")
            write_text(source, "browser-extension/private.py")

            self.assertEqual(
                [path.as_posix() for path in contract.skill_files(source)],
                [
                    "LICENSE",
                    "SKILL.md",
                    "references/guide.md",
                    "references/nested/deep.md",
                    "requirements-youtube.txt",
                    "scripts/fixtures/mediacrawler/safe.jsonl",
                    "scripts/nested/runtime.py",
                    "scripts/runtime.py",
                ],
            )

    def test_forbidden_scan_rejects_paths_and_secrets_without_returning_values(self) -> None:
        secret_values = (
            "github_pat_abcdefghijklmnopqrstuvwxyz123456",
            "fc-abcdefghijklmnopqrstuvwxyz123456",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
            "pm_live_abcdefghijklmnopqrstuvwxyz123456",
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_text(root, ".env", "SAFE=test\n")
            write_text(root, ".env.local", "SAFE=test\n")
            write_text(root, "cookies.json", "{}\n")
            for directory in (
                ".venv",
                "node_modules",
                "promotion-output",
                "chrome-profile",
                "user-data-dir",
                "MediaCrawler-backup-2026",
                "__pycache__",
            ):
                (root / directory).mkdir()
            for index, secret in enumerate(secret_values):
                write_text(root, f"notes/secret-{index}.txt", secret + "\n")
            write_text(root, "safe.txt", "no credentials here\n")
            (root / "binary.dat").write_bytes(b"\x00" + secret_values[0].encode("ascii"))
            (root / "huge.txt").write_bytes(secret_values[1].encode("ascii") + b"x" * 2_000_000)

            violations = contract.scan_forbidden(root)
            rules = {item["rule"] for item in violations}
            paths = {item["path"] for item in violations}
            self.assertLessEqual(
                {"forbidden_path", "github_token", "firecrawl_key", "private_key", "live_license"},
                rules,
            )
            self.assertLessEqual(
                {
                    ".env",
                    ".env.local",
                    "cookies.json",
                    ".venv",
                    "node_modules",
                    "promotion-output",
                    "chrome-profile",
                    "user-data-dir",
                    "MediaCrawler-backup-2026",
                    "__pycache__",
                },
                paths,
            )
            serialized = json.dumps(violations, sort_keys=True)
            for secret in secret_values:
                self.assertNotIn(secret, serialized)
            self.assertNotIn("binary.dat", paths)
            self.assertNotIn("huge.txt", paths)

    def test_sha256_and_tree_digest_are_deterministic_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a_path = write_text(root, "a.txt", "abc")
            write_text(root, "nested/b.txt", "two\n")
            self.assertEqual(
                contract.sha256_file(a_path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            first = contract.tree_digest(root)
            second = contract.tree_digest(root)
            self.assertEqual(first, second)
            self.assertRegex(first, r"^[0-9a-f]{64}$")

            a_path.write_text("changed", encoding="utf-8")
            changed = contract.tree_digest(root)
            self.assertNotEqual(first, changed)
            self.assertRegex(changed, r"^[0-9a-f]{64}$")

    def test_extension_file_listing_contains_locales_and_excludes_hidden_paths(self) -> None:
        names = {path.as_posix() for path in contract.extension_files(ROOT)}
        self.assertLessEqual(
            {"manifest.json", "_locales/en/messages.json", "_locales/zh_CN/messages.json"},
            names,
        )
        self.assertFalse(any(part.startswith(".") for name in names for part in Path(name).parts))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_text(root, "browser-extension/manifest.json", "{}\n")
            write_text(root, "browser-extension/.hidden.json", "{}\n")
            write_text(root, "browser-extension/.private/secret.txt")
            self.assertEqual(
                [path.as_posix() for path in contract.extension_files(root)],
                ["manifest.json"],
            )


if __name__ == "__main__":
    unittest.main()

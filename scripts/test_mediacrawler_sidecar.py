#!/usr/bin/env python3
"""Offline tests for the guarded MediaCrawler local sidecar integration."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
FIXTURES = SCRIPTS / "fixtures" / "mediacrawler"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mediacrawler_contract as contract


class ContractTests(unittest.TestCase):
    salt = b"fixture-only-local-salt"

    def load_fixture(self, name: str) -> list[dict[str, object]]:
        return [json.loads(line) for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_normalizes_three_platform_content_without_sensitive_fields(self) -> None:
        expected = {
            "xiaohongshu": ("xhs-note-001", "note", 128, 36),
            "douyin": ("dy-aweme-001", "short_video", 260, 48),
            "zhihu": ("zh-content-001", "answer", 88, None),
        }
        for platform, (content_id, content_type, likes, favorites) in expected.items():
            with self.subTest(platform=platform):
                raw = self.load_fixture(f"{platform}-contents.jsonl")[0]
                record = contract.normalize_content(platform, raw, "contents.jsonl#L1", self.salt)
                self.assertEqual(record["schemaVersion"], 1)
                self.assertEqual(record["provider"], "mediacrawler")
                self.assertEqual(record["platform"], platform)
                self.assertEqual(record["contentId"], content_id)
                self.assertEqual(record["contentType"], content_type)
                self.assertEqual(record["metrics"]["likes"], likes)
                self.assertEqual(record["metrics"]["favorites"], favorites)
                self.assertRegex(record["publishedAt"], r"^2024-")
                self.assertEqual(record["evidencePath"], "contents.jsonl#L1")
                self.assertTrue(record["authorHash"])
                serialized = json.dumps(record, ensure_ascii=False).lower()
                for secret in ("xhs-secret-token", "dy-secret-token", "zh-secret-signature", "xsec_token", "mstoken", "signature"):
                    self.assertNotIn(secret, serialized)

    def test_normalizes_parent_child_comments_and_deduplicates(self) -> None:
        rows = self.load_fixture("xiaohongshu-comments.jsonl")
        records = contract.normalize_comments("xiaohongshu", rows + [rows[0]], "comments.jsonl", self.salt)
        self.assertEqual(len(records), 2)
        self.assertIsNone(records[0]["parentCommentId"])
        self.assertEqual(records[1]["parentCommentId"], records[0]["commentId"])
        self.assertEqual(records[0]["replyCount"], 1)
        self.assertEqual(records[0]["likes"], 9)
        self.assertEqual(records[0]["contentId"], "xhs-note-001")

    def test_normalizes_all_comment_platforms(self) -> None:
        for platform in ("xiaohongshu", "douyin", "zhihu"):
            with self.subTest(platform=platform):
                rows = self.load_fixture(f"{platform}-comments.jsonl")
                records = contract.normalize_comments(platform, rows, f"{platform}-comments.jsonl", self.salt)
                self.assertEqual(len(records), 2)
                self.assertEqual(records[0]["platform"], platform)
                self.assertTrue(records[0]["commentId"])
                self.assertTrue(records[0]["text"])
                self.assertTrue(records[0]["authorHash"])
                self.assertRegex(records[0]["createdAt"], r"^2024-")

    def test_sanitizer_removes_tokens_signatures_cookies_and_raw_ids_recursively(self) -> None:
        value = {
            "url": "https://www.xiaohongshu.com/explore/xhs-note-001?xsec_token=secret&xsec_source=pc_search&keep=ok",
            "Authorization": "Bearer secret",
            "nested": {
                "cookie": "a=b",
                "signature": "signed",
                "user_id": "raw-user-001",
                "safe": "retained",
            },
        }
        sanitized = contract.sanitize_mapping(value)
        text = json.dumps(sanitized, ensure_ascii=False).lower()
        for secret in ("secret", "bearer", "a=b", "signed", "raw-user-001", "xsec_token"):
            self.assertNotIn(secret, text)
        self.assertIn("retained", text)
        self.assertIn("keep=ok", text)

    def test_author_hash_is_stable_per_install_salt(self) -> None:
        first = contract.local_author_hash("upstream-creator", self.salt)
        second = contract.local_author_hash("upstream-creator", self.salt)
        other = contract.local_author_hash("upstream-creator", b"different-salt")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertEqual(len(first), 24)

    def test_unknown_platform_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported MediaCrawler platform"):
            contract.normalize_content("weibo", {}, "fixture", self.salt)


if __name__ == "__main__":
    unittest.main()

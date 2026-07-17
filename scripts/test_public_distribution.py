#!/usr/bin/env python3
"""Tests for the public distribution boundary."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import build_public_distribution as builder
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
    def test_distribution_templates_have_matching_bilingual_documents(self) -> None:
        distribution = ROOT / "distribution"
        zh_docs = distribution / "docs" / "zh-CN"
        en_docs = distribution / "docs" / "en"
        expected_names = {
            "data-and-privacy.md",
            "extension-guide.md",
            "features.md",
            "installation.md",
            "platform-research.md",
            "publishing-and-review.md",
            "quick-start.md",
            "skill-guide.md",
            "troubleshooting.md",
            "version-sync.md",
        }

        zh_names = {path.name for path in zh_docs.glob("*.md")}
        en_names = {path.name for path in en_docs.glob("*.md")}
        self.assertEqual(zh_names, expected_names)
        self.assertEqual(en_names, expected_names)
        self.assertEqual(zh_names, en_names)
        self.assertEqual(len(zh_names), 10)

        zh_readme = (distribution / "README.md").read_text(encoding="utf-8")
        en_readme = (distribution / "README.en.md").read_text(encoding="utf-8")
        zh_opening = "\n\n".join(
            (
                "# ENHE 产品推广素材生成器",
                contract.PRODUCT_PROMISE_ZH,
                "[English](README.en.md) | [官方网站](https://www.enhe-tech.com.cn/) | [产品页面](https://www.enhe-tech.com.cn/promotion-manager) | [Chrome 商店](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)",
            )
        )
        en_opening = "\n\n".join(
            (
                "# ENHE Product Promo Maker",
                contract.PRODUCT_PROMISE_EN,
                "[中文](README.md) | [Official website](https://www.enhe-tech.com.cn/) | [Product page](https://www.enhe-tech.com.cn/promotion-manager) | [Chrome Web Store](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)",
            )
        )
        self.assertTrue(zh_readme.startswith(zh_opening + "\n\n"))
        self.assertTrue(en_readme.startswith(en_opening + "\n\n"))

        def h2_names(text: str) -> list[str]:
            return [line.removeprefix("## ") for line in text.splitlines() if line.startswith("## ")]

        self.assertEqual(
            h2_names(zh_readme),
            [
                "你提供一个产品网页，我们交付什么",
                "它解决的不是“写一篇文案”，而是整套推广准备",
                "Skill 与 Chrome 插件如何配合",
                "核心功能与用户收益",
                "五分钟开始使用",
                "支持的平台和当前边界",
                "本地优先、安全可审计",
                "当前版本与下载",
                "创作者与联系信息",
                "开源许可与第三方组件",
            ],
        )
        self.assertEqual(
            h2_names(en_readme),
            [
                "What you provide and what the product delivers",
                "More than one piece of copy: a complete promotion-preparation workflow",
                "How the Skill and Chrome extension work together",
                "Capabilities and customer benefits",
                "Start in five minutes",
                "Supported platforms and current boundaries",
                "Local-first and auditable by design",
                "Current version and downloads",
                "Creator and contact",
                "License and third-party components",
            ],
        )

        def feature_rows(path: Path, expected_columns: list[str]) -> list[list[str]]:
            table_lines = [
                line
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.startswith("|")
            ]
            columns = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
            self.assertEqual(columns, expected_columns)
            rows = [
                [cell.strip() for cell in line.strip("|").split("|")]
                for line in table_lines[2:]
            ]
            self.assertEqual(len(rows), 16)
            self.assertTrue(all(len(row) == 5 for row in rows))
            self.assertTrue(all(all(cell for cell in row) for row in rows))
            return rows

        zh_feature_rows = feature_rows(
            zh_docs / "features.md",
            ["功能", "它做什么", "解决什么问题", "给用户带来的收益", "典型场景"],
        )
        en_feature_rows = feature_rows(
            en_docs / "features.md",
            [
                "Capability",
                "What it does",
                "Problem it solves",
                "User benefit",
                "Typical use case",
            ],
        )
        expected_capability_pairs = [
            ("产品网页读取", "Product webpage reading"),
            ("多链接与网站产品发现", "Multi-link and website product discovery"),
            ("竞品与爆款内容研究", "Competitor and high-performing content research"),
            ("本机登录态 Sidecar 研究", "Local-login Sidecar research"),
            ("事实、证据与风险控制", "Fact, evidence, and risk controls"),
            ("平台原生文案生成", "Platform-native copy generation"),
            ("视频口播稿与分镜", "Spoken video scripts and storyboards"),
            ("MP4 视频草稿", "MP4 video drafts"),
            ("封面图与详情图", "Cover and detail images"),
            ("完整发布包", "Complete publishing packs"),
            ("受控发布辅助", "Controlled publishing assistance"),
            ("发布后真实证据导入", "Post-publication real-evidence import"),
            ("复盘与下一轮优化", "Retrospectives and next-iteration optimization"),
            ("Chrome 当前页面转任务", "Turn the current Chrome page into a task"),
            ("中英文界面", "Chinese and English UI"),
            ("本地优先隐私", "Local-first privacy"),
        ]
        self.assertEqual(
            [row[0] for row in zh_feature_rows],
            [pair[0] for pair in expected_capability_pairs],
        )
        self.assertEqual(
            [row[0] for row in en_feature_rows],
            [pair[1] for pair in expected_capability_pairs],
        )
        self.assertEqual(
            list(zip([row[0] for row in zh_feature_rows], [row[0] for row in en_feature_rows])),
            expected_capability_pairs,
        )

        selected_feature_markers = {
            0: {
                "zh": ("浏览器快照", "把猜测当事实", "来源、状态和风险提示", "SaaS 产品页"),
                "en": ("browser snapshot", "assumptions as facts", "sources, status, and risk notes", "SaaS product page"),
            },
            3: {
                "zh": ("MediaCrawler Sidecar", "纯匿名读取", "用户控制的本机环境", "小红书关键词"),
                "en": ("MediaCrawler Sidecar", "anonymous reads", "user-controlled local environment", "Xiaohongshu keyword"),
            },
            10: {
                "zh": ("最终提交前停止", "凭据和账号权限", "完整载荷、截图和缺失项", "YouTube 官方 API dry-run"),
                "en": ("stops before final submission", "credential and account-permission", "full payload, screenshots, and missing items", "YouTube official API dry-run"),
            },
            11: {
                "zh": ("真实 URL", "平台后台", "可追溯", "published-urls.csv"),
                "en": ("real URLs", "platform dashboards", "traceable", "published-urls.csv"),
            },
            15: {
                "zh": ("Cookies", "客户数据", "数据外传面", "客户电脑"),
                "en": ("Cookies", "client data", "surface for data transfer", "client's computer"),
            },
        }
        for row_index, language_markers in selected_feature_markers.items():
            for cell, marker in zip(zh_feature_rows[row_index][1:], language_markers["zh"]):
                self.assertIn(marker, cell)
            for cell, marker in zip(en_feature_rows[row_index][1:], language_markers["en"]):
                self.assertIn(marker, cell)

        def assert_markers(path: Path, markers: tuple[str, ...]) -> None:
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                with self.subTest(path=path.relative_to(distribution), marker=marker):
                    self.assertIn(marker, text)

        per_document_markers = {
            "installation.md": {
                "zh": (
                    "本文面向 Windows PowerShell",
                    "python --version",
                    "python -m pip install playwright pillow",
                    "python -m playwright install chromium",
                    'python scripts\\self_evolution_audit.py --skip-runtime-checks --out-dir ".\\promotion-output\\install-audit"',
                    "SHA256SUMS",
                    "新的空暂存目录",
                    '$ErrorActionPreference = "Stop"',
                    "ReparsePoint",
                    "$installed.backup.$(Get-Date -Format 'yyyyMMddHHmmss')",
                    "Move-Item -LiteralPath $installed -Destination $backup",
                    "Move-Item -LiteralPath $backup -Destination $installed",
                    "完全退出并重新打开 Codex",
                    "刷新 Skill 发现",
                    "本机登录态研究",
                    "最终发布需要用户审核和操作",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    "This guide is written for Windows PowerShell first",
                    "python --version",
                    "python -m pip install playwright pillow",
                    "python -m playwright install chromium",
                    'python scripts\\self_evolution_audit.py --skip-runtime-checks --out-dir ".\\promotion-output\\install-audit"',
                    "SHA256SUMS",
                    "new empty staging directory",
                    '$ErrorActionPreference = "Stop"',
                    "ReparsePoint",
                    "$installed.backup.$(Get-Date -Format 'yyyyMMddHHmmss')",
                    "Move-Item -LiteralPath $installed -Destination $backup",
                    "Move-Item -LiteralPath $backup -Destination $installed",
                    "fully exit and reopen Codex",
                    "refresh Skill discovery",
                    "Local-login research",
                    "Final publishing requires user review and action",
                    "existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "quick-start.md": {
                "zh": (
                    "python scripts\\skill_entry.py",
                    "--link-mode site",
                    "product-batch-runs\\<run>",
                    "generated-content",
                    "videos",
                    "media-assets",
                    "publish-queue",
                    "publish-packs",
                    "retrospectives",
                    "real-evidence-inbox-setup",
                    "real-evidence-inbox",
                    "最终发布需要用户审核和操作",
                    "只使用真实 URL、指标、评论、订单和收入",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    "python scripts\\skill_entry.py",
                    "--link-mode site",
                    "product-batch-runs\\<run>",
                    "generated-content",
                    "videos",
                    "media-assets",
                    "publish-queue",
                    "publish-packs",
                    "retrospectives",
                    "real-evidence-inbox-setup",
                    "real-evidence-inbox",
                    "Final publishing requires user review and action",
                    "Only real URLs, metrics, comments, orders, and revenue are used as real evidence",
                    "existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "skill-guide.md": {
                "zh": (
                    "普通用户应使用 `skill_entry.py`",
                    "`promotion_manager.py` 是",
                    "不是单链接入口",
                    "product-batch-runs\\<run>",
                    "generated-content",
                    "publish-packs",
                    "publish-queue",
                    "retrospectives",
                    "MediaCrawler Sidecar 单独安装在本机",
                    "最终发布需要用户审核和操作",
                    "只导入真实 URL、指标、评论、订单和收入",
                    "扩展 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    "Regular users should use `skill_entry.py`",
                    "`promotion_manager.py` is a lower-level report generator",
                    "it is not the single-link entry point",
                    "product-batch-runs\\<run>",
                    "generated-content",
                    "publish-packs",
                    "publish-queue",
                    "retrospectives",
                    "MediaCrawler Sidecar is installed separately on the local computer",
                    "Final publishing requires user review and action",
                    "Import only real URLs, metrics, comments, orders, and revenue",
                    "extension's billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "extension-guide.md": {
                "zh": (
                    contract.STORE_ITEM_ID,
                    "`0.5.2`",
                    "`0.5.3`",
                    "捕获必须由用户发起",
                    "Chrome 登录配置",
                    "11 项脚本",
                    "最终发布需要用户审核和操作",
                    "真实 URL、指标、评论、订单和收入才是复盘证据",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    contract.STORE_ITEM_ID,
                    "`0.5.2`",
                    "`0.5.3`",
                    "Capture must be initiated by the user",
                    "Chrome login profiles",
                    "11 scripts",
                    "Final publishing requires user review and action",
                    "Only real URLs, metrics, comments, orders, and revenue are retrospective evidence",
                    "extension's existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "platform-research.md": {
                "zh": (
                    "MediaCrawler Sidecar 本机登录态",
                    "python scripts\\platform_data_manager.py setup --check",
                    "python scripts\\platform_data_manager.py setup --install",
                    "`--keep-raw`",
                    "manual_verification_required",
                    "blocked_by_platform",
                    "最终发布需要用户审核和操作",
                    "只使用真实 URL、指标、评论、订单和收入",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    "MediaCrawler Sidecar with local login state",
                    "python scripts\\platform_data_manager.py setup --check",
                    "python scripts\\platform_data_manager.py setup --install",
                    "`--keep-raw`",
                    "manual_verification_required",
                    "blocked_by_platform",
                    "Final publishing requires user review and action",
                    "Only real URLs, metrics, comments, orders, and revenue are used as real evidence",
                    "extension's existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "publishing-and-review.md": {
                "zh": (
                    "product-batch-runs\\<run>",
                    "python scripts\\publish_readiness_runner.py",
                    "python scripts\\browser_publish_session.py",
                    "--execute-publish --approval I_APPROVE_PUBLISH",
                    "最终发布需要用户审核和操作",
                    "只登记真实发布 URL、真实指标、真实评论、真实订单和真实收入",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    "product-batch-runs\\<run>",
                    "python scripts\\publish_readiness_runner.py",
                    "python scripts\\browser_publish_session.py",
                    "--execute-publish --approval I_APPROVE_PUBLISH",
                    "Final publishing requires user review and action",
                    "Record only real published URLs, real metrics, real comments, real orders, and real revenue",
                    "extension's existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "data-and-privacy.md": {
                "zh": (
                    "https://www.enhe-tech.com.cn/promotion-manager/privacy",
                    "## 数据保留",
                    "`--keep-raw`",
                    "huqingwei5942@gmail.com",
                    "Cookies 与 Chrome 登录配置只留在本机",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker：关闭",
                ),
                "en": (
                    "https://www.enhe-tech.com.cn/promotion-manager/privacy",
                    "## Data retention",
                    "`--keep-raw`",
                    "huqingwei5942@gmail.com",
                    "Cookies and Chrome login profiles stay on the local computer",
                    "extension's existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker: disabled",
                ),
            },
            "troubleshooting.md": {
                "zh": (
                    "--install-browser-if-missing",
                    "partial_ready",
                    "provider_unavailable",
                    "waiting_login",
                    "manual_verification_required",
                    "blocked_by_platform",
                    "$env:PYTHONUTF8 = \"1\"",
                    "--sync-installed-skill",
                    "--execute-publish --approval I_APPROVE_PUBLISH",
                    "waiting_real_data",
                    "huqingwei5942@gmail.com",
                    "扩展原有 billing UI 和 `billing-contract.json` 保留",
                    "Hosted Worker 保持关闭",
                ),
                "en": (
                    "--install-browser-if-missing",
                    "partial_ready",
                    "provider_unavailable",
                    "waiting_login",
                    "manual_verification_required",
                    "blocked_by_platform",
                    "$env:PYTHONUTF8 = \"1\"",
                    "--sync-installed-skill",
                    "--execute-publish --approval I_APPROVE_PUBLISH",
                    "waiting_real_data",
                    "huqingwei5942@gmail.com",
                    "extension's existing billing UI and `billing-contract.json` remain included",
                    "Hosted Worker remains disabled",
                ),
            },
            "version-sync.md": {
                "zh": (
                    "公开仓库/Skill/扩展源码版本：0.5.3",
                    "Chrome 商店当前公开版本（发布前）：0.5.2",
                    "非支付命令引用：11/11 已在随包 Skill 中存在",
                    "支付与订阅：不纳入功能同步结论，但扩展原有 UI 和 billing-contract.json 保留",
                    "Hosted Worker：关闭",
                    contract.STORE_ITEM_ID,
                    "--sync-installed-skill",
                ),
                "en": (
                    "Public repository / Skill / extension source version: 0.5.3",
                    "Current public Chrome Web Store version (before update): 0.5.2",
                    "Non-payment command references: 11/11 exist in the bundled Skill",
                    "Payment and subscriptions: excluded from the feature parity conclusion; the existing extension UI and billing-contract.json remain included",
                    "Hosted Worker: disabled",
                    contract.STORE_ITEM_ID,
                    "--sync-installed-skill",
                ),
            },
        }
        for name, language_markers in per_document_markers.items():
            assert_markers(zh_docs / name, language_markers["zh"])
            assert_markers(en_docs / name, language_markers["en"])

        def assert_before(text: str, earlier: str, later: str) -> None:
            self.assertGreaterEqual(text.find(earlier), 0, earlier)
            self.assertGreater(text.find(later), text.find(earlier), later)

        for installation_path in (
            zh_docs / "installation.md",
            en_docs / "installation.md",
        ):
            installation = installation_path.read_text(encoding="utf-8")
            with self.subTest(path=installation_path.relative_to(distribution)):
                assert_before(
                    installation,
                    "if (($stagingItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)",
                    "$stagingRoot = (Resolve-Path -LiteralPath $staging).Path",
                )
                assert_before(
                    installation,
                    "if (($candidateItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)",
                    "$candidate = (Resolve-Path -LiteralPath $candidatePath).Path",
                )
                assert_before(
                    installation,
                    "if (($installedItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)",
                    "$resolvedInstalled = (Resolve-Path -LiteralPath $installed).Path",
                )
                assert_before(
                    installation,
                    "$resolvedInstalled = (Resolve-Path -LiteralPath $installed).Path",
                    "Move-Item -LiteralPath $installed -Destination $backup",
                )
                assert_before(
                    installation,
                    "if (($backupItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)",
                    "$resolvedBackup = (Resolve-Path -LiteralPath $backup).Path",
                )
                assert_before(
                    installation,
                    "$resolvedBackup = (Resolve-Path -LiteralPath $backup).Path",
                    "Move-Item -LiteralPath $backup -Destination $installed",
                )

        zh_version = (zh_docs / "version-sync.md").read_text(encoding="utf-8")
        en_version = (en_docs / "version-sync.md").read_text(encoding="utf-8")
        for command_name in EXPECTED_COMMANDS:
            self.assertIn(f"`{command_name}`", zh_version)
            self.assertIn(f"`{command_name}`", en_version)

        zh_corpus = zh_readme + "\n" + "\n".join(
            (zh_docs / name).read_text(encoding="utf-8") for name in sorted(zh_names)
        )
        en_corpus = en_readme + "\n" + "\n".join(
            (en_docs / name).read_text(encoding="utf-8") for name in sorted(en_names)
        )
        for fact in (
            "公开仓库/Skill/扩展源码版本：0.5.3",
            "Chrome 商店当前公开版本（发布前）：0.5.2",
            "非支付命令引用：11/11 已在随包 Skill 中存在",
            "Hosted Worker：关闭",
        ):
            self.assertIn(fact, zh_corpus)
        for fact in (
            "Public repository / Skill / extension source version: 0.5.3",
            "Current public Chrome Web Store version (before update): 0.5.2",
            "Non-payment command references: 11/11 exist in the bundled Skill",
            "Hosted Worker: disabled",
        ):
            self.assertIn(fact, en_corpus)

        shared_identity = (
            "ENHE AI",
            "深圳市龙岗区恩禾网络科技工作室",
            "https://www.enhe-tech.com.cn/",
            "https://www.enhe-tech.com.cn/promotion-manager",
            "huqingwei5942@gmail.com",
            "https://github.com/hqwzhu",
            contract.STORE_ITEM_ID,
        )
        for value in shared_identity:
            self.assertIn(value, zh_readme)
            self.assertIn(value, en_readme)

        for readme, license_markers in (
            (
                zh_readme,
                (
                    "`Copyright (c) 2026 HU`",
                    "`HU` 是该许可文件显示的代码版权标识/权利人",
                    "`ENHE AI` 是产品品牌与创作者身份",
                    "`深圳市龙岗区恩禾网络科技工作室` 是公开运营与支持主体",
                ),
            ),
            (
                en_readme,
                (
                    "`Copyright (c) 2026 HU`",
                    "`HU` is the code copyright identifier/rightsholder shown in the MIT license",
                    "`ENHE AI` is the product brand and creator identity",
                    "Shenzhen Longgang District Enhe Network Technology Studio (深圳市龙岗区恩禾网络科技工作室) is the public operating and support entity",
                ),
            ),
        ):
            for marker in license_markers:
                self.assertIn(marker, readme)

        markdown_files = [
            distribution / "README.md",
            distribution / "README.en.md",
            *(zh_docs / name for name in sorted(zh_names)),
            *(en_docs / name for name in sorted(en_names)),
        ]
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        distribution_root = distribution.resolve()
        for source in markdown_files:
            text = source.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(text):
                target = raw_target.strip().strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative_target = target.split("#", 1)[0]
                if not relative_target:
                    continue
                resolved_target = (source.parent / relative_target).resolve()
                with self.subTest(source=source.relative_to(distribution), target=target):
                    try:
                        resolved_target.relative_to(distribution_root)
                    except ValueError:
                        self.fail(f"relative link escapes distribution tree: {target}")
                    self.assertTrue(resolved_target.exists(), f"missing relative link: {target}")

        banned_claims = (
            "guaranteed viral",
            "bypass captcha",
            "automatic final publish",
            "automatically click final publish",
            "保证爆款",
            "承诺爆款",
            "绕过验证码",
            "自动点击最终发布",
        )
        for path in markdown_files:
            lowered = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path.relative_to(distribution)):
                self.assertIsNone(re.search(r"\b(?:todo|tbd|placeholder)\b", lowered))
                for banned_claim in banned_claims:
                    self.assertNotIn(banned_claim, lowered)

    def test_committed_snapshot_excludes_ignored_allowlisted_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            snapshot = base / "snapshot"
            source.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=source, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=source,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Distribution Test"],
                cwd=source,
                check=True,
            )
            write_text(source, ".gitignore", "scripts/ignored.py\n")
            write_text(source, "scripts/tracked.py", "print('tracked')\n")
            subprocess.run(["git", "add", "."], cwd=source, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=source, check=True)
            write_text(source, "scripts/ignored.py", "print('ignored')\n")
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            builder.snapshot_committed_source(source, snapshot, commit)

            self.assertTrue((snapshot / "scripts" / "tracked.py").is_file())
            self.assertFalse((snapshot / "scripts" / "ignored.py").exists())

    def test_builder_rejects_mocked_reparse_target_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ancestor = Path(temp) / "ancestor"
            ancestor.mkdir()
            target = ancestor / "nested" / "public"

            with mock.patch.object(
                builder,
                "_is_link_or_reparse",
                side_effect=lambda path: path == ancestor,
            ):
                with self.assertRaisesRegex(RuntimeError, "ancestor|reparse|unsafe"):
                    builder.build_repository(ROOT, target, source_commit="test")

    def test_builder_rejects_real_symlink_target_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            outside = base / "outside"
            outside.mkdir()
            link = base / "linked"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"OS denied symlink creation: {exc}")

            with self.assertRaisesRegex(RuntimeError, "link|reparse|unsafe"):
                builder.build_repository(ROOT, link / "public", source_commit="test")

    def test_builder_creates_component_manifests_without_private_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "public"
            builder.build_repository(ROOT, target, source_commit="test-source-commit")

            skill = target / "skill" / "viral-product-copy-video-generator"
            extension = target / "extension" / "chrome"
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "requirements-youtube.txt").is_file())
            self.assertTrue((extension / "manifest.json").is_file())
            self.assertFalse((target / "backend").exists())
            self.assertFalse((target / "deploy").exists())
            self.assertEqual(contract.scan_forbidden(target), [])

            skill_component = json.loads(
                (skill / "component-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(skill_component["version"], contract.VERSION)
            self.assertEqual(skill_component["sourceCommit"], "test-source-commit")
            self.assertEqual(skill_component["runtime"], "Python 3.11 and Codex")
            self.assertEqual(
                skill_component["entryPoints"], ["SKILL.md", "scripts/skill_entry.py"]
            )
            self.assertEqual(
                skill_component["capabilityIds"], list(contract.NON_PAYMENT_COMMANDS)
            )
            extension_component = json.loads(
                (extension / "component-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(extension_component["version"], contract.VERSION)
            self.assertEqual(extension_component["sourceCommit"], "test-source-commit")
            self.assertEqual(extension_component["runtime"], "Chrome Manifest V3")
            self.assertEqual(
                extension_component["entryPoints"],
                ["manifest.json", "popup.html", "popup.js"],
            )
            self.assertEqual(
                extension_component["nonPaymentCapabilityIds"],
                list(contract.NON_PAYMENT_COMMANDS),
            )
            self.assertIs(extension_component["billingParityIncluded"], False)

            release = json.loads(
                (target / "release-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(release["version"], "0.5.3")
            self.assertEqual(release["sourceCommit"], "test-source-commit")
            self.assertEqual(release["syncAudit"]["status"], "ready")
            self.assertEqual(
                release["syncAudit"]["commands"],
                list(contract.NON_PAYMENT_COMMANDS),
            )

    def test_builder_refuses_non_empty_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "public"
            target.mkdir()
            (target / "keep.txt").write_text("keep\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "target directory is not empty"):
                builder.build_repository(ROOT, target, source_commit="test")

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

    def test_extension_command_discovery_handles_variants_and_rejects_bypasses(self) -> None:
        commands = "\n".join(
            (
                "python scripts/automation_scheduler.py",
                r"python.exe scripts\browser_publish_session.py",
                "python3 scripts/final_capability_readiness.py",
                r"python3.exe scripts\launch_unlock_pack.py",
                "python3.11 scripts/performance_monitor.py",
                r"python3.11.exe scripts\promotion_manager.py",
                "py scripts/skill_entry.py",
                r"py.exe scripts\unapproved-tool.py",
            )
        )
        self.assertEqual(
            contract.extension_command_refs(commands),
            [
                "automation_scheduler.py",
                "browser_publish_session.py",
                "final_capability_readiness.py",
                "launch_unlock_pack.py",
                "performance_monitor.py",
                "promotion_manager.py",
                "skill_entry.py",
                "unapproved-tool.py",
            ],
        )

        unsupported = (
            "node scripts/unapproved.py",
            "node scripts/unapproved-tool.py",
            "python2 scripts/unapproved.py",
            r"pythonw scripts\unapproved.py",
            "not-python scripts/unapproved.py",
            "scripts/unapproved.py",
            "python scripts/skill_entry.py && node scripts/unapproved.py",
        )
        for command in unsupported:
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "unsupported interpreter"):
                    contract.extension_command_refs(command)

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
            (root / "invalid.dat").write_bytes(b"\xff" + secret_values[1].encode("ascii"))
            (root / "huge.txt").write_bytes(secret_values[1].encode("ascii") + b"x" * 2_000_000)

            violations = contract.scan_forbidden(root)
            rules = {item["rule"] for item in violations}
            paths = {item["path"] for item in violations}
            findings = {(item["path"], item["rule"]) for item in violations}
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
            self.assertIn(("binary.dat", "github_token"), findings)
            self.assertIn(("invalid.dat", "firecrawl_key"), findings)
            self.assertNotIn("huge.txt", paths)

    def test_forbidden_scan_reports_unreadable_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unreadable = write_text(root, "unreadable.txt")
            real_read_bytes = Path.read_bytes

            def read_bytes_with_denial(path: Path) -> bytes:
                if path == unreadable:
                    raise PermissionError("test-only read denial")
                return real_read_bytes(path)

            with mock.patch.object(Path, "read_bytes", new=read_bytes_with_denial):
                violations = contract.scan_forbidden(root)

            self.assertIn(
                {"path": "unreadable.txt", "rule": "unreadable_file"},
                violations,
            )
            self.assertNotIn("test-only read denial", json.dumps(violations, sort_keys=True))

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

    def test_public_file_walkers_reject_real_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            secret = "github_pat_abcdefghijklmnopqrstuvwxyz123456"
            outside = write_text(base, "outside.txt", secret)

            def symlink(link: Path) -> None:
                link.parent.mkdir(parents=True, exist_ok=True)
                try:
                    link.symlink_to(outside)
                except OSError as exc:
                    self.skipTest(f"OS denied symlink creation: {exc}")

            skill_root = base / "skill"
            symlink(skill_root / "scripts" / "escape.py")
            with self.assertRaisesRegex(ValueError, "link|reparse|outside"):
                contract.skill_files(skill_root)

            extension_root = base / "extension-source"
            symlink(extension_root / "browser-extension" / "escape.js")
            with self.assertRaisesRegex(ValueError, "link|reparse|outside"):
                contract.extension_files(extension_root)

            digest_root = base / "digest"
            symlink(digest_root / "escape.txt")
            with self.assertRaisesRegex(ValueError, "link|reparse|outside"):
                contract.tree_digest(digest_root)

            violations = contract.scan_forbidden(digest_root)
            self.assertIn({"path": "escape.txt", "rule": "unsafe_link"}, violations)
            self.assertNotIn(secret, json.dumps(violations, sort_keys=True))

    def test_public_file_walkers_reject_resolved_paths_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            outside = write_text(base, "outside.txt", "private\n").resolve()
            skill_root = base / "skill"
            extension_root = base / "extension-source"
            digest_root = base / "digest"
            write_text(skill_root, "scripts/escape.py")
            write_text(extension_root, "browser-extension/escape.js")
            write_text(digest_root, "escape.txt")

            real_resolve = Path.resolve

            def resolve_with_escape(path: Path, *args: object, **kwargs: object) -> Path:
                if path.name.startswith("escape"):
                    return outside
                return real_resolve(path, *args, **kwargs)

            with mock.patch.object(Path, "resolve", new=resolve_with_escape):
                with self.assertRaisesRegex(ValueError, "outside"):
                    contract.skill_files(skill_root)
                with self.assertRaisesRegex(ValueError, "outside"):
                    contract.extension_files(extension_root)
                with self.assertRaisesRegex(ValueError, "outside"):
                    contract.tree_digest(digest_root)
                self.assertIn(
                    {"path": "escape.txt", "rule": "unsafe_link"},
                    contract.scan_forbidden(digest_root),
                )


if __name__ == "__main__":
    unittest.main()

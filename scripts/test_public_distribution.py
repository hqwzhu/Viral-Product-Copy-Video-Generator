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
        feature_fields = ("what", "problem", "benefit", "use_case")
        feature_contracts = [
            (
                ("产品网页读取", "Product webpage reading"),
                (
                    (r"公开产品页.*浏览器快照", r"public product page.*browser snapshot"),
                    (r"信息散落.*猜测当事实", r"scattered.*assumptions as facts"),
                    (r"来源.*状态.*风险提示", r"sources.*status.*risk notes"),
                    (r"SaaS 产品页.*定位.*目标用户", r"SaaS product page.*positioning.*target users"),
                ),
            ),
            (
                ("多链接与网站产品发现", "Multi-link and website product discovery"),
                (
                    (r"多个产品链接.*站点地图.*候选产品页", r"multiple product links.*sitemap.*candidate product pages"),
                    (r"产品线多.*逐页复制.*耗时", r"product line.*one by one.*time-consuming"),
                    (r"一次运行.*候选清单.*评分", r"candidate list.*one run.*scores"),
                    (r"几十个工具页面.*批量", r"dozens of tool pages.*batches"),
                ),
            ),
            (
                ("竞品与爆款内容研究", "Competitor and high-performing content research"),
                (
                    (r"竞品.*创作者.*钩子.*可见指标", r"competitors.*creators.*hooks.*visible metrics"),
                    (r"只凭感觉.*参考内容来自哪里", r"intuition.*reference material came from"),
                    (r"可复核的证据库.*内容模式.*补采", r"reviewable evidence library.*content patterns.*follow-up collection"),
                    (r"AI 工具.*YouTube.*小红书.*抖音", r"AI tool.*YouTube.*Xiaohongshu.*Douyin"),
                ),
            ),
            (
                ("本机登录态 Sidecar 研究", "Local-login Sidecar research"),
                (
                    (r"MediaCrawler Sidecar.*本机 Chrome 登录态", r"MediaCrawler Sidecar.*local Chrome login state"),
                    (r"匿名读取.*浏览器可见内容", r"anonymous reads.*visible in a user's browser"),
                    (r"用户控制的本机环境.*保留状态", r"user-controlled local environment.*preserving collection status"),
                    (r"本机完成登录.*小红书关键词", r"signing in locally.*Xiaohongshu keyword"),
                ),
            ),
            (
                ("事实、证据与风险控制", "Fact, evidence, and risk controls"),
                (
                    (r"事实.*来源.*权限.*合成演示.*缺失", r"facts.*sources.*permissions.*synthetic demonstration.*missing"),
                    (r"无法核查.*数字.*链接.*假设", r"numbers.*links.*assumptions.*cannot be checked"),
                    (r"审核者.*可以用.*补证据", r"reviewers.*usable.*needs evidence"),
                    (r"引用.*风险提示.*waiting_real_data", r"citations.*risk notes.*waiting_real_data"),
                ),
            ),
            (
                ("平台原生文案生成", "Platform-native copy generation"),
                (
                    (r"YouTube.*知乎.*小红书.*抖音.*GitHub.*标题.*标签", r"YouTube.*Zhihu.*Xiaohongshu.*Douyin.*GitHub.*titles.*tags"),
                    (r"通用文案.*不同平台.*语气", r"generic.*does not fit.*different platforms"),
                    (r"减少重复改写.*多平台草稿", r"reduces repetitive rewriting.*platform-specific drafts"),
                    (r"视频简介.*知乎回答.*小红书笔记", r"video description.*Zhihu answer.*Xiaohongshu post"),
                ),
            ),
            (
                ("视频口播稿与分镜", "Spoken video scripts and storyboards"),
                (
                    (r"产品事实.*口播稿.*镜头顺序.*字幕", r"product facts.*spoken scripts.*shot order.*subtitle"),
                    (r"文案.*拍摄.*剪辑.*共同结构", r"copywriting.*shooting.*editing.*shared production structure"),
                    (r"可拍.*可审.*可交接", r"filmed.*reviewed.*handed off"),
                    (r"30–60 秒.*页面录屏", r"30–60 second.*screen captures"),
                ),
            ),
            (
                ("MP4 视频草稿", "MP4 video drafts"),
                (
                    (r"FFmpeg.*音频素材.*MP4", r"FFmpeg.*audio assets.*MP4"),
                    (r"只有文字.*节奏.*画面缺口", r"text alone.*pacing.*missing visuals"),
                    (r"时长.*画幅.*素材占位", r"duration.*aspect ratio.*provisional asset"),
                    (r"可播放的 MP4.*首轮审稿", r"playable MP4.*first review"),
                ),
            ),
            (
                ("封面图与详情图", "Cover and detail images"),
                (
                    (r"Pillow.*PNG.*尺寸.*路径", r"Pillow.*PNG.*dimensions.*paths"),
                    (r"每个平台.*重新整理图片.*漏传", r"every platform.*reorganized.*omit"),
                    (r"图片.*标题.*视频.*发布字段", r"images.*title.*video.*publishing fields"),
                    (r"小红书.*抖音.*封面.*产品细节图", r"Xiaohongshu.*Douyin.*cover.*product-detail"),
                ),
            ),
            (
                ("完整发布包", "Complete publishing packs"),
                (
                    (r"标题.*标签.*媒体路径.*跟踪链接.*人工步骤", r"titles.*tags.*media paths.*tracking links.*manual steps"),
                    (r"内容.*素材.*发布说明.*分散", r"content.*assets.*publishing instructions.*scattered"),
                    (r"一份清单.*留下记录", r"one checklist.*audit record"),
                    (r"已审核任务.*创作者.*客户", r"approved task.*creator.*client"),
                ),
            ),
            (
                ("受控发布辅助", "Controlled publishing assistance"),
                (
                    (r"dry-run.*字段填充.*发布队列.*最终提交前停止", r"dry-run.*field filling.*publishing queues.*stops before final submission"),
                    (r"误操作.*凭据.*账号权限", r"mistakes.*credential.*account-permission"),
                    (r"完整载荷.*截图.*缺失项", r"full payload.*screenshots.*missing items"),
                    (r"YouTube 官方 API dry-run.*小红书", r"YouTube official API dry-run.*Xiaohongshu"),
                ),
            ),
            (
                ("发布后真实证据导入", "Post-publication real-evidence import"),
                (
                    (r"真实 URL.*截图.*订单.*收入", r"real URLs.*screenshots.*orders.*revenue"),
                    (r"平台后台.*统一入口", r"platform dashboards.*consistent retrospective entry point"),
                    (r"可追溯.*示例数字", r"traceable.*sample numbers"),
                    (r"published-urls.csv.*metrics.csv.*评论文件", r"published-urls.csv.*metrics.csv.*comment files"),
                ),
            ),
            (
                ("复盘与下一轮优化", "Retrospectives and next-iteration optimization"),
                (
                    (r"真实证据.*表现摘要.*受众需求.*下一轮.*钩子", r"real evidence.*performance summaries.*audience needs.*next topic.*hook"),
                    (r"结构化反馈.*下一轮靠猜", r"structured feedback.*next iteration.*guesswork"),
                    (r"真实数据.*内容方向.*优先级", r"real data.*content direction.*priority"),
                    (r"不同标题.*真实指标.*下一轮素材", r"different titles.*real metrics.*next asset set"),
                ),
            ),
            (
                ("Chrome 当前页面转任务", "Turn the current Chrome page into a task"),
                (
                    (r"用户主动点击.*当前标签页 URL.*可复制", r"explicit user click.*current tab URL.*copyable"),
                    (r"浏览器.*终端.*手工抄链接.*易出错", r"manually copying.*browser.*terminal.*error-prone"),
                    (r"几秒内.*本地任务.*审阅命令", r"within seconds.*local task.*reviewable"),
                    (r"产品官网.*功能页.*单链接", r"product website.*feature page.*single-link"),
                ),
            ),
            (
                ("中英文界面", "Chinese and English UI"),
                (
                    (r"中文/英文切换.*所选参数", r"Chinese and English.*selected parameters"),
                    (r"团队成员语言不同.*入口不统一", r"different languages.*consistent entry point"),
                    (r"中文运营.*英文协作者", r"Chinese-language operators.*English-language collaborators"),
                    (r"中文运营选择平台.*英文协作者审核", r"Chinese-language operator selects platforms.*English-language collaborator reviews"),
                ),
            ),
            (
                ("本地优先隐私", "Local-first privacy"),
                (
                    (r"输出.*Cookies.*Chrome 登录配置.*本机", r"output.*Cookies.*Chrome login profiles.*local computer"),
                    (r"账号状态.*客户数据.*隐藏令牌", r"account state.*client data.*hidden tokens"),
                    (r"减少数据外传面.*审计.*删除", r"reduces the surface for data transfer.*review.*deletion"),
                    (r"客户电脑.*决定分享", r"client's computer.*decide what to share"),
                ),
            ),
        ]
        self.assertEqual(len(feature_contracts), 16)
        self.assertEqual(len(zh_feature_rows), len(feature_contracts))
        self.assertEqual(len(en_feature_rows), len(feature_contracts))
        for row_index, ((zh_name, en_name), field_contracts) in enumerate(feature_contracts):
            self.assertEqual(len(field_contracts), len(feature_fields))
            self.assertEqual(zh_feature_rows[row_index][0], zh_name)
            self.assertEqual(en_feature_rows[row_index][0], en_name)
            for field_index, (field_name, language_patterns) in enumerate(
                zip(feature_fields, field_contracts),
                start=1,
            ):
                for language, row, pattern in (
                    ("zh", zh_feature_rows[row_index], language_patterns[0]),
                    ("en", en_feature_rows[row_index], language_patterns[1]),
                ):
                    capability = row[0]
                    normalized_cell = row[field_index].casefold()
                    for marker in pattern.split(".*"):
                        message = (
                            f"{language} capability={capability!r} field={field_name!r} "
                            f"lacks semantic marker {marker!r}"
                        )
                        self.assertIn(marker.casefold(), normalized_cell, message)

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

    def test_distribution_runnable_examples_use_official_product_url(self) -> None:
        distribution = ROOT / "distribution"
        official_url = "https://www.enhe-tech.com.cn/promotion-manager"
        obsolete_url = "https://example.com/product"
        required_product_guides = {
            distribution / "README.md",
            distribution / "README.en.md",
            distribution / "docs" / "zh-CN" / "quick-start.md",
            distribution / "docs" / "en" / "quick-start.md",
            distribution / "docs" / "zh-CN" / "skill-guide.md",
            distribution / "docs" / "en" / "skill-guide.md",
        }
        markdown_files = [
            distribution / "README.md",
            distribution / "README.en.md",
            *sorted((distribution / "docs" / "zh-CN").glob("*.md")),
            *sorted((distribution / "docs" / "en").glob("*.md")),
        ]
        powershell_block = re.compile(r"```powershell\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
        guides_with_product_commands: set[Path] = set()
        for path in markdown_files:
            for block_index, block in enumerate(
                powershell_block.findall(path.read_text(encoding="utf-8")),
                start=1,
            ):
                with self.subTest(path=path.relative_to(distribution), block=block_index):
                    self.assertNotIn(obsolete_url, block)
                    is_product_run = (
                        "python scripts\\skill_entry.py" in block
                        and "--link " in block
                        and "--link-mode site" not in block
                    )
                    is_evidence_setup = (
                        "python scripts\\real_evidence_inbox_setup.py" in block
                        and "--product-url " in block
                    )
                    if is_product_run or is_evidence_setup:
                        self.assertIn(official_url, block)
                        guides_with_product_commands.add(path)
        self.assertLessEqual(required_product_guides, guides_with_product_commands)

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

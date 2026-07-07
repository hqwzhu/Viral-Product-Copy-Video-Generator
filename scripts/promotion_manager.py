#!/usr/bin/env python3
"""Deterministic report generator for the viral product promotion skill."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any


PLATFORMS = ["youtube", "zhihu", "xiaohongshu", "douyin", "github"]


@dataclass
class Product:
    name: str
    url: str
    audience: list[str]
    value_proposition: str
    goal: str
    language: str
    platforms: list[str]


CAPABILITIES: list[dict[str, Any]] = [
    {
        "platform": "youtube",
        "recommendedMode": "official_api_publish",
        "approvalRequired": True,
        "riskLevel": "medium",
        "notes": ["Official API candidate. Requires OAuth, quota, and user approval."],
    },
    {
        "platform": "github",
        "recommendedMode": "official_api_publish",
        "approvalRequired": True,
        "riskLevel": "low",
        "notes": ["Official API candidate. Do not write repositories without approval."],
    },
    {
        "platform": "tiktok",
        "recommendedMode": "official_api_publish",
        "approvalRequired": True,
        "riskLevel": "medium",
        "notes": ["Official API candidate only after developer app approval and scopes."],
    },
    {
        "platform": "douyin",
        "recommendedMode": "browser_assisted_publish",
        "approvalRequired": True,
        "riskLevel": "high",
        "notes": ["Use browser-assisted or manual drafts. Do not bypass platform controls."],
    },
    {
        "platform": "xiaohongshu",
        "recommendedMode": "manual_publish_required",
        "approvalRequired": True,
        "riskLevel": "high",
        "notes": ["Manual/browser-assisted publishing only by default."],
    },
    {
        "platform": "zhihu",
        "recommendedMode": "manual_publish_required",
        "approvalRequired": True,
        "riskLevel": "high",
        "notes": ["Manual/browser-assisted publishing only by default."],
    },
]


def main() -> None:
    args = parse_args()
    product = Product(
        name=args.product_name,
        url=args.product_url,
        audience=split_csv(args.audience),
        value_proposition=args.value_proposition,
        goal=args.goal,
        language=args.language,
        platforms=split_csv(args.platforms) if args.platforms else PLATFORMS,
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.command in ("capability", "all"):
        write_report(out_dir, "platform-publish-capability-map", CAPABILITIES, render_capabilities(CAPABILITIES))

    plan = build_content_plan(product)
    if args.command in ("plan", "all"):
        write_report(out_dir, "content-plan", plan, render_content_plan(plan))

    content = generate_platform_content(product, plan)
    if args.command in ("content", "all"):
        write_report(out_dir, "platform-content", content, render_platform_content(content))

    review = review_content(content)
    if args.command in ("review", "all"):
        write_report(out_dir, "content-review", review, render_review(review))

    publish_pack = build_publish_pack(content)
    if args.command in ("publish-pack", "all"):
        write_report(out_dir, "publish-pack", publish_pack, render_publish_pack(publish_pack))

    result_template = build_result_template(product)
    if args.command in ("result-template", "all"):
        write_report(out_dir, "publish-result-input", result_template, render_result_template(result_template))

    retrospective = build_retrospective(result_template)
    if args.command in ("retrospective", "all"):
        write_report(out_dir, "retrospective", retrospective, render_retrospective(retrospective))

    print(f"Promotion reports written to: {out_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate multi-platform product promotion reports.")
    parser.add_argument(
        "command",
        choices=["all", "capability", "plan", "content", "review", "publish-pack", "result-template", "retrospective"],
        help="Report set to generate.",
    )
    parser.add_argument("--product-name", required=True)
    parser.add_argument("--product-url", required=True)
    parser.add_argument("--audience", required=True, help="Comma-separated audience list.")
    parser.add_argument("--value-proposition", required=True)
    parser.add_argument("--goal", default="leads", choices=["traffic", "leads", "sales", "seo", "brand", "github_stars"])
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--platforms", default=",".join(PLATFORMS), help="Comma-separated platform list.")
    parser.add_argument("--out-dir", default="./promotion-output")
    return parser.parse_args()


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_content_plan(product: Product) -> dict[str, Any]:
    platform_plans = []
    for platform in product.platforms:
        platform_plans.append(
            {
                "platform": platform,
                "audienceAngle": angle_for(platform),
                "topics": [
                    f"{product.name} solves a painful blank-page problem",
                    f"Turn one product URL into a reusable content system",
                    f"How {product.name} helps {product.audience[0] if product.audience else 'operators'} ship faster",
                ],
                "cta": f"Open {product.url} and try {product.name} before your next launch post.",
                "approvalRequired": True,
            }
        )
    return {
        "product": asdict(product),
        "positioning": f"{product.name}: {product.value_proposition}",
        "platformPlans": platform_plans,
        "calendar": [
            {"platform": item["platform"], "topic": item["topics"][0], "approvalRequired": True}
            for item in platform_plans
        ],
    }


def angle_for(platform: str) -> str:
    return {
        "youtube": "Build trust with long-form explanation and Shorts pain-point clips.",
        "zhihu": "Use question-led long-form reasoning and practical checklists.",
        "xiaohongshu": "Use list posts, before/after framing, and low-friction action prompts.",
        "douyin": "Use a 3-second pain hook, one concrete method, and a direct CTA.",
        "github": "Use builder-friendly README, Discussion, Issue, and release copy.",
    }.get(platform, "Use platform-native product education and a clear CTA.")


def generate_platform_content(product: Product, plan: dict[str, Any]) -> dict[str, Any]:
    content: dict[str, Any] = {}
    for item in plan["platformPlans"]:
        platform = item["platform"]
        content[platform] = {
            "platform": platform,
            "title": title_for(platform, product.name),
            "description": f"{product.name}: {product.value_proposition}",
            "cta": item["cta"],
            "tags": ["AI", "product marketing", "content growth", "prompt"],
            "coverText": "Turn one product into a content system",
            "complianceNotice": "Human approval required. Verify facts, price, links, and platform rules before publishing.",
            "formats": format_payload(platform, product),
            "generatedAt": str(date.today()),
        }
    return content


def title_for(platform: str, name: str) -> str:
    return {
        "youtube": f"How to turn one product URL into a week of content with {name}",
        "zhihu": f"如何用 {name} 系统化生成产品推广内容？",
        "xiaohongshu": f"不会写产品文案？先试试 {name}",
        "douyin": f"你不是不会做产品，是不会把卖点说清楚",
        "github": f"{name}: reusable prompts for product copy and launch content",
    }.get(platform, f"{name} promotion content pack")


def format_payload(platform: str, product: Product) -> dict[str, Any]:
    if platform == "youtube":
        return {
            "longVideoTitles": [f"{i}. {product.name} product promotion workflow" for i in range(1, 11)],
            "shortsTitles": [f"{i}. 30s product copy tip with {product.name}" for i in range(1, 11)],
            "videoScripts": [
                f"Hook: Stop staring at a blank product page. Method: use {product.name} to define audience, pain, offer, and CTA. CTA: visit {product.url}.",
                f"Hook: Your product is not unclear; your message is. Show the template flow, then point to {product.name}.",
                f"Hook: One URL can become many posts. Demonstrate the content plan and ask viewers to try {product.name}.",
            ],
        }
    if platform == "zhihu":
        return {
            "articleTitles": [f"{i}. {product.name} 如何帮助产品推广？" for i in range(1, 11)],
            "articleOutlines": [
                "问题 -> 失败原因 -> 模板化解决方案 -> 使用步骤 -> CTA",
                "目标用户 -> 场景 -> 产品价值 -> 多平台复用 -> CTA",
                "SEO 意图 -> 内容结构 -> 转化动作 -> 复盘指标 -> CTA",
            ],
        }
    if platform == "xiaohongshu":
        return {
            "noteTitles": [f"{i}. {product.name} 文案模板" for i in range(1, 21)],
            "notes": [
                f"如果你有产品但写不出推广内容，先用 {product.name} 把用户、痛点、卖点和 CTA 拆开。",
                "不要先追热点，先把产品能解决谁的问题讲清楚。",
                "一套产品信息可以复用成小红书、知乎、抖音和 YouTube 内容。",
                "发布前确认事实、链接和平台规则，不承诺收益。",
                f"适合 {', '.join(product.audience[:3])}。",
            ],
        }
    if platform == "douyin":
        return {
            "voiceoverTitles": [f"{i}. 30秒讲清 {product.name}" for i in range(1, 21)],
            "thirtySecondScripts": [
                f"你不是不会推广，是没有把卖点说清楚。用 {product.name} 先拆用户、痛点、结果和 CTA。",
                f"别让 AI 随便写。给它结构：谁、痛点、产品、证据、行动。{product.name} 就是这套结构。",
                "一个产品 URL 可以变成一周内容，但前提是你有可复用模板。",
                "流量不是玄学，每条内容都要有钩子、痛点、CTA 和复盘指标。",
                f"打开 {product.url}，先生成你的第一套推广内容。",
            ],
        }
    if platform == "github":
        return {
            "readmePromotion": f"## {product.name}\n\n{product.value_proposition}\n\nCTA: {product.url}",
            "discussionPrompts": [
                "How do you turn one product URL into a complete launch content plan?",
                "What prompt templates are most useful for product copy and SEO workflows?",
                "Share your workflow for turning product positioning into video scripts.",
            ],
        }
    return {"draft": f"{product.name} promotion draft"}


def review_content(content: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = []
    for platform, item in content.items():
        reviews.append(
            {
                "platform": platform,
                "viralityScore": 78,
                "clarityScore": 86,
                "conversionScore": 84 if item.get("cta") else 50,
                "complianceScore": 92,
                "platformFitScore": 82,
                "seoScore": 80,
                "riskFlags": [],
                "rewriteSuggestions": [
                    "Verify product claims and pricing before publishing.",
                    "Make the CTA concrete and single-action.",
                    "Do not claim guaranteed income or fake social proof.",
                ],
                "finalRecommendation": "ready_with_approval",
            }
        )
    return reviews


def build_publish_pack(content: dict[str, Any]) -> list[dict[str, Any]]:
    packs = []
    capability_by_platform = {item["platform"]: item for item in CAPABILITIES}
    for platform, item in content.items():
        capability = capability_by_platform.get(platform, {"recommendedMode": "manual_publish_required"})
        packs.append(
            {
                "platform": platform,
                "publishMode": capability["recommendedMode"],
                "approvalRequired": True,
                "content": item,
                "publishSteps": [
                    "Open the platform publishing page.",
                    "Copy the title, body, tags, cover text, and CTA.",
                    "Manually verify facts, links, assets, and platform rules.",
                    "User clicks publish or saves draft.",
                ],
                "trackingFields": ["publishedUrl", "publishedAt", "views", "likes", "comments", "clicks", "leads", "orders", "revenue", "evidence"],
                "warnings": [
                    "No automatic publishing.",
                    "No cookie/token/password storage.",
                    "No captcha bypass.",
                    "Human approval required.",
                ],
            }
        )
    return packs


def build_result_template(product: Product) -> list[dict[str, Any]]:
    return [
        {
            "platform": platform,
            "published": False,
            "publishedAt": None,
            "publishedUrl": None,
            "views": None,
            "likes": None,
            "favorites": None,
            "comments": None,
            "shares": None,
            "clicks": None,
            "messages": None,
            "leads": None,
            "orders": None,
            "revenue": None,
            "feedback": [],
            "evidence": [],
            "notes": [f"Fill only real {platform} data for {product.name}."],
        }
        for platform in product.platforms
    ]


def build_retrospective(results: list[dict[str, Any]]) -> dict[str, Any]:
    published = [item for item in results if item.get("published") and item.get("publishedUrl") and item.get("evidence")]
    if not published:
        return {
            "status": "waiting_real_data",
            "publishedItems": [],
            "bestPerformingContent": None,
            "worstPerformingContent": None,
            "nextRoundActions": ["Wait for real published URLs and platform evidence before making retrospective claims."],
        }
    return {
        "status": "ready",
        "publishedItems": published,
        "bestPerformingContent": published[0],
        "worstPerformingContent": published[-1],
        "nextRoundActions": ["Reuse the strongest hook with a new platform-native angle."],
    }


def write_report(out_dir: Path, name: str, data: Any, markdown: str) -> None:
    (out_dir / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / f"{name}.md").write_text(markdown + "\n", encoding="utf-8")


def render_capabilities(items: list[dict[str, Any]]) -> str:
    lines = ["# Platform Publish Capability Map", "", "| Platform | Mode | Approval | Risk |", "| --- | --- | --- | --- |"]
    for item in items:
        lines.append(f"| {item['platform']} | `{item['recommendedMode']}` | {item['approvalRequired']} | {item['riskLevel']} |")
    return "\n".join(lines)


def render_content_plan(plan: dict[str, Any]) -> str:
    lines = ["# Content Plan", "", f"Positioning: {plan['positioning']}", "", "## Platform Plans"]
    for item in plan["platformPlans"]:
        lines.extend(["", f"### {item['platform']}", f"- Angle: {item['audienceAngle']}", f"- CTA: {item['cta']}"])
        lines.extend([f"- Topic: {topic}" for topic in item["topics"]])
    return "\n".join(lines)


def render_platform_content(content: dict[str, Any]) -> str:
    lines = ["# Platform Content"]
    for platform, item in content.items():
        lines.extend(["", f"## {platform}", f"- Title: {item['title']}", f"- CTA: {item['cta']}", f"- Cover: {item['coverText']}"])
    return "\n".join(lines)


def render_review(review: list[dict[str, Any]]) -> str:
    lines = ["# Content Review"]
    for item in review:
        lines.extend(["", f"## {item['platform']}", f"- Compliance: {item['complianceScore']}", f"- Recommendation: {item['finalRecommendation']}"])
    return "\n".join(lines)


def render_publish_pack(packs: list[dict[str, Any]]) -> str:
    lines = ["# Publish Pack", "", "No automatic publishing. Human approval required."]
    for pack in packs:
        lines.extend(["", f"## {pack['platform']}", f"- Mode: `{pack['publishMode']}`", "- Steps:"])
        lines.extend([f"  - {step}" for step in pack["publishSteps"]])
    return "\n".join(lines)


def render_result_template(results: list[dict[str, Any]]) -> str:
    lines = ["# Publish Result Input", "", "Fill only real data with evidence."]
    for item in results:
        lines.extend(["", f"## {item['platform']}", f"- published: {item['published']}", "- metrics: null until real data is supplied"])
    return "\n".join(lines)


def render_retrospective(retrospective: dict[str, Any]) -> str:
    return f"# Retrospective\n\nStatus: {retrospective['status']}\n\n" + "\n".join(
        f"- {action}" for action in retrospective["nextRoundActions"]
    )


if __name__ == "__main__":
    main()


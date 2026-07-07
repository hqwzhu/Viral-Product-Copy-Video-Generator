#!/usr/bin/env python3
"""Extract a structured product profile from a public URL or saved HTML file."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[dict[str, str]] = []
        self.json_ld: list[str] = []
        self._script_type: str | None = None
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = attrs_map.get("property") or attrs_map.get("name")
            content = attrs_map.get("content")
            if key and content:
                self.meta[key.lower()] = normalize_space(content)
        elif tag == "link":
            if attrs_map.get("rel") or attrs_map.get("href"):
                self.links.append(attrs_map)
        elif tag == "script":
            self._script_type = attrs_map.get("type", "").lower()
            self._script_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            if self._script_type == "application/ld+json" and self._script_parts:
                self.json_ld.append("".join(self._script_parts).strip())
            self._script_type = None
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self._script_type == "application/ld+json":
            self._script_parts.append(data)


def main() -> None:
    args = parse_args()
    html, source = load_html(args)
    profile = extract_profile(html, source)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "product-profile.json"
    md_path = out_dir / "product-profile.md"
    json_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(profile) + "\n", encoding="utf-8")
    print(f"Product profile written to: {json_path.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract product metadata from a URL or HTML file.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Public product URL to fetch.")
    source.add_argument("--html-file", help="Saved product HTML file to parse.")
    parser.add_argument("--out-dir", default="./promotion-output/intake")
    return parser.parse_args()


def load_html(args: argparse.Namespace) -> tuple[str, str]:
    if args.html_file:
        path = Path(args.html_file)
        return path.read_text(encoding="utf-8"), str(path)
    request = urllib.request.Request(
        args.url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ViralProductPromotionSkill/1.0; +https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace"), args.url


def extract_profile(html: str, source: str) -> dict[str, Any]:
    parser = MetadataParser()
    parser.feed(html)
    title = first_non_empty(
        parser.meta.get("og:title"),
        parser.meta.get("twitter:title"),
        normalize_space(" ".join(parser.title_parts)),
    )
    description = first_non_empty(
        parser.meta.get("og:description"),
        parser.meta.get("description"),
        parser.meta.get("twitter:description"),
    )
    image = first_non_empty(parser.meta.get("og:image"), parser.meta.get("twitter:image"))
    canonical = canonical_url(parser.links)
    jsonld_objects = parse_json_ld(parser.json_ld)
    inferred_name = first_non_empty(
        value_from_json_ld(jsonld_objects, "name"),
        title,
        "Unknown product",
    )
    inferred_offer = first_non_empty(
        value_from_json_ld(jsonld_objects, "offers.price"),
        value_from_json_ld(jsonld_objects, "price"),
        "unknown",
    )
    keywords = infer_keywords(title, description, parser.meta.get("keywords", ""))
    value_proposition = infer_value_proposition(inferred_name, description)
    return {
        "source": source,
        "canonicalUrl": canonical or source,
        "productName": inferred_name,
        "title": title,
        "description": description,
        "valueProposition": value_proposition,
        "pricing": inferred_offer,
        "image": image,
        "keywords": keywords,
        "targetAudienceAssumptions": infer_audience(keywords, description),
        "painPointAssumptions": infer_pain_points(keywords, description),
        "jsonLdTypes": sorted({str(item.get("@type")) for item in jsonld_objects if isinstance(item, dict) and item.get("@type")}),
        "confidence": confidence_score(title, description, jsonld_objects),
        "notes": [
            "Derived from public page metadata. Verify product claims, pricing, audience, and legal terms before publishing.",
            "Dynamic pages may expose less metadata than the rendered browser page.",
        ],
    }


def parse_json_ld(blocks: list[str]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            graph = data.get("@graph")
            if isinstance(graph, list):
                parsed.extend([item for item in graph if isinstance(item, dict)])
            parsed.append(data)
        elif isinstance(data, list):
            parsed.extend([item for item in data if isinstance(item, dict)])
    return parsed


def value_from_json_ld(items: list[dict[str, Any]], dotted_key: str) -> str:
    parts = dotted_key.split(".")
    for item in items:
        value: Any = item
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break
        if value not in (None, ""):
            return str(value)
    return ""


def canonical_url(links: list[dict[str, str]]) -> str:
    for link in links:
        rel = link.get("rel", "").lower()
        if "canonical" in rel and link.get("href"):
            return link["href"]
    return ""


def infer_keywords(*values: str) -> list[str]:
    text = " ".join(values).lower()
    raw = re.split(r"[,，;；|/\s]+", text)
    keywords = []
    for item in raw:
        cleaned = re.sub(r"[^a-z0-9\u4e00-\u9fff-]", "", item).strip("-")
        if len(cleaned) >= 2 and cleaned not in keywords:
            keywords.append(cleaned)
    return keywords[:20]


def infer_value_proposition(name: str, description: str) -> str:
    if description:
        return description
    return f"{name} product page. Value proposition needs manual verification."


def infer_audience(keywords: list[str], description: str) -> list[str]:
    text = " ".join(keywords) + " " + description.lower()
    audiences = []
    if any(term in text for term in ["ai", "prompt", "automation", "workflow"]):
        audiences.append("AI tool users and operators")
    if any(term in text for term in ["seo", "content", "blog", "marketing"]):
        audiences.append("content and growth operators")
    if any(term in text for term in ["developer", "github", "api", "open source"]):
        audiences.append("developers and technical founders")
    if any(term in text for term in ["shop", "ecommerce", "seller", "store"]):
        audiences.append("ecommerce sellers")
    return audiences or ["target audience needs manual verification"]


def infer_pain_points(keywords: list[str], description: str) -> list[str]:
    text = " ".join(keywords) + " " + description.lower()
    points = []
    if any(term in text for term in ["copy", "content", "prompt", "template"]):
        points.append("hard to turn product value into reusable content")
    if any(term in text for term in ["seo", "traffic", "growth"]):
        points.append("needs more qualified traffic")
    if any(term in text for term in ["automation", "workflow", "tool"]):
        points.append("manual workflows are slow")
    return points or ["pain points need manual verification"]


def confidence_score(title: str, description: str, jsonld: list[dict[str, Any]]) -> str:
    score = 0
    if title:
        score += 1
    if description:
        score += 1
    if jsonld:
        score += 1
    return {0: "low", 1: "low", 2: "medium", 3: "high"}[score]


def first_non_empty(*values: str | None) -> str:
    for value in values:
        normalized = normalize_space(value or "")
        if normalized:
            return normalized
    return ""


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def render_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Product Profile",
        "",
        f"- Source: {profile['source']}",
        f"- Canonical URL: {profile['canonicalUrl']}",
        f"- Product name: {profile['productName']}",
        f"- Value proposition: {profile['valueProposition']}",
        f"- Pricing: {profile['pricing']}",
        f"- Confidence: {profile['confidence']}",
        "",
        "## Audience Assumptions",
    ]
    lines.extend([f"- {item}" for item in profile["targetAudienceAssumptions"]])
    lines.extend(["", "## Pain Point Assumptions"])
    lines.extend([f"- {item}" for item in profile["painPointAssumptions"]])
    lines.extend(["", "## Keywords"])
    lines.extend([f"- {item}" for item in profile["keywords"]])
    lines.extend(["", "## Notes"])
    lines.extend([f"- {item}" for item in profile["notes"]])
    return "\n".join(lines)


if __name__ == "__main__":
    main()

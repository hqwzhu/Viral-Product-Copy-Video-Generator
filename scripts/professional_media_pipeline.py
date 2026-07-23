#!/usr/bin/env python3
"""Run one local professional media pipeline job.

This entry point intentionally wires only local providers through
``MediaOrchestrator``.  It never uploads browser state, creates a Hosted
Worker, or publishes to a platform.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:  # direct ``python scripts/professional_media_pipeline.py``
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.media_pipeline.contracts import MediaJob
from scripts.media_pipeline.orchestrator import MediaOrchestrator


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local professional product media from one product page.")
    parser.add_argument("--product-url", required=True)
    parser.add_argument("--product-name", required=True)
    parser.add_argument("--content-json", required=True, help="Generated bilingual content JSON.")
    parser.add_argument("--publish-pack", default="", help="Optional publish-pack JSON to update after a complete run.")
    parser.add_argument("--run-dir", default="", help="Explicit run directory; otherwise the bilingual output root is used.")
    parser.add_argument("--language", default="zh-CN", choices=("zh-CN", "en", "en-US"))
    parser.add_argument("--platforms", default="youtube", help="Comma-separated target platforms.")
    parser.add_argument("--brand-logo", action="append", default=[], help="Local brand logo path; may be repeated.")
    parser.add_argument("--quality-target", default="professional", choices=("draft", "standard", "professional"))
    parser.add_argument("--comfyui-url", default="", help="Reserved local ComfyUI endpoint hint; no remote upload is enabled.")
    parser.add_argument("--presenter", default="none", choices=("none", "musetalk", "heygen"))
    parser.add_argument("--presenter-asset", default="")
    parser.add_argument("--portrait-authorized", action="store_true")
    parser.add_argument("--allow-cloud-media", action="store_true", help="Explicitly request cloud media (disabled by this local-only runner).")
    return parser.parse_args(argv)


def _platforms(value: str) -> tuple[str, ...]:
    return tuple(item.strip().casefold() for item in value.split(",") if item.strip()) or ("youtube",)


def _aspect_ratios(platforms: tuple[str, ...]) -> tuple[str, ...]:
    portrait = {"douyin", "xiaohongshu", "tiktok"}
    if platforms and platforms[0] in portrait:
        return ("9:16",)
    if platforms and platforms[0] == "github":
        return ("1:1",)
    return ("16:9",)


def build_job(args: argparse.Namespace) -> MediaJob:
    content = Path(args.content_json).expanduser().resolve()
    if not content.is_file():
        raise FileNotFoundError(content)
    platforms = _platforms(args.platforms)
    run_id = Path(args.run_dir).expanduser().name if args.run_dir else datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return MediaJob(
        run_id=run_id,
        product_name=args.product_name,
        source_url=args.product_url,
        language=args.language,
        target_platforms=platforms,
        quality_target=args.quality_target,
        aspect_ratios=_aspect_ratios(platforms),
        duration_range=(20, 60),
        providers={"comfyuiUrl": args.comfyui_url} if args.comfyui_url else {},
        allow_cloud_media=args.allow_cloud_media,
        product_data_path=str(content),
        brand_assets=tuple(Path(item).expanduser().resolve() for item in args.brand_logo),
        generated_content_path=str(content),
        capture_plan_path="",
        presenter=args.presenter,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.presenter != "none":
        if not args.presenter_asset or not args.portrait_authorized:
            raise SystemExit("presenter asset requires --presenter-asset and --portrait-authorized")
        raise SystemExit("presenter adapters are not enabled in the local core pipeline")
    job = build_job(args)
    scene_provider = None
    if args.comfyui_url:
        from scripts.media_pipeline.scenes import ComfyUiFluxProvider

        workflow = Path(__file__).resolve().parents[1] / "references" / "comfyui" / "flux1-schnell-api.json"
        scene_provider = ComfyUiFluxProvider(args.comfyui_url, workflow, allow_cloud_media=args.allow_cloud_media)
    orchestrator = MediaOrchestrator(scene_provider=scene_provider)
    result = orchestrator.run(job, run_dir=args.run_dir or None, publish_pack_path=args.publish_pack or None)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"ready", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

import hashlib
import re
import unicodedata
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path


DEFAULT_OUTPUT_ROOT = Path("promotion-output_推广输出")
RUNS_DIR = "runs_运行记录"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if ascii_slug:
        return ascii_slug
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
    return f"product-{digest}"


@dataclass(frozen=True)
class RunPaths:
    root: Path
    source_assets: Path
    captures: Path
    generated_content: Path
    voiceovers: Path
    b_roll: Path
    ai_scenes: Path
    videos: Path
    covers: Path
    detail_images: Path
    publish_packs: Path
    reports: Path

    def create(self) -> "RunPaths":
        for field in fields(self):
            getattr(self, field.name).mkdir(parents=True, exist_ok=True)
        return self


def new_run_paths(
    output_root: Path, product: str, now: str | None = None
) -> RunPaths:
    timestamp = now or datetime.now().strftime("%Y%m%d-%H%M%S")
    base_root = output_root / RUNS_DIR / f"{timestamp}-{slugify(product)}"
    root = base_root
    sequence = 2
    while root.exists():
        root = base_root.with_name(f"{base_root.name}-{sequence:03d}")
        sequence += 1
    return RunPaths(
        root=root,
        source_assets=root / "source-assets_源素材",
        captures=root / "product-captures_产品录屏",
        generated_content=root / "generated-content_生成内容",
        voiceovers=root / "voiceovers_配音",
        b_roll=root / "b-roll_辅助镜头",
        ai_scenes=root / "ai-scenes_AI场景图",
        videos=root / "videos_视频",
        covers=root / "covers_封面",
        detail_images=root / "detail-images_详情图",
        publish_packs=root / "publish-packs_发布包",
        reports=root / "reports_报告",
    )


def find_existing(relative_new: Path, relative_legacy: Path) -> Path:
    if relative_new.exists():
        return relative_new
    if relative_legacy.exists():
        return relative_legacy
    return relative_new

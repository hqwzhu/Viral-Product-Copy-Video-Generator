"""Local commercial visual composition for product promotion assets.

The compositor deliberately treats the supplied product capture as source media:
it only scales the pixels with :func:`PIL.ImageOps.contain` and never redraws a
dashboard or other product UI.  Backgrounds and logos are local files too.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

try:  # Pillow remains an optional dependency for the rest of the pipeline.
    from PIL import Image, ImageDraw, ImageOps
except ImportError:  # pragma: no cover - exercised when Pillow is not installed
    Image = ImageDraw = ImageOps = None  # type: ignore[assignment]

from scripts.media_asset_pack import load_font, wrap_pixels
from scripts.media_pipeline.contracts import Artifact, StageResult


PLATFORM_SIZES: dict[str, tuple[int, int]] = {
    "youtube": (1920, 1080),
    "zhihu": (1200, 628),
    "xiaohongshu": (1080, 1440),
    "douyin": (1080, 1920),
    "github": (1280, 640),
}

_DETAIL_LABELS = ("真实录屏", "有声视频", "商业视觉")
_DETAIL_TINTS = ((16, 32, 64), (22, 78, 99), (56, 32, 72))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_local_image(value: str | Path, name: str) -> tuple[Path, Any]:
    """Resolve and decode a local image, rejecting URLs and unreadable files."""

    if Image is None:
        raise RuntimeError("pillow_unavailable")
    raw = str(value)
    if "://" in raw:
        raise ValueError(f"{name}_must_be_local")
    path = Path(value).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"{name}_not_readable")
    resolved = path.resolve()
    try:
        with Image.open(resolved) as opened:
            opened.load()
            image = opened.copy()
    except Exception as exc:
        raise ValueError(f"{name}_invalid_image") from exc
    return resolved, image


def _atomic_save(image: Any, destination: Path) -> None:
    """Write a PNG through a sibling part file and atomically replace it."""

    part = destination.with_name(destination.name + ".part")
    try:
        part.unlink(missing_ok=True)
        image.save(part, format="PNG")
        part.replace(destination)
    except Exception:
        part.unlink(missing_ok=True)
        raise


def _fit(image: Any, size: tuple[int, int]) -> Any:
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def _contain(image: Any, size: tuple[int, int]) -> tuple[Any, str]:
    """Fit a capture without scaling when the layout box can contain it."""

    rgb = image.convert("RGB")
    if rgb.width <= size[0] and rgb.height <= size[1]:
        return rgb, "native"
    # This call is intentionally the only transformation of product pixels.
    return ImageOps.contain(rgb, size, method=Image.Resampling.LANCZOS), "resized"


def _paste_product(canvas: Any, capture: Any, frame: tuple[int, int, int, int], radius: int) -> str:
    x0, y0, x1, y1 = frame
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x0 + 12, y0 + 16, x1 + 12, y1 + 16),
        radius=radius,
        fill=(0, 0, 0, 100),
    )
    canvas.alpha_composite(shadow)

    frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame_layer)
    frame_draw.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=(248, 250, 252, 255))
    frame_draw.rounded_rectangle(
        (x0, y0, x1, y1), radius=radius, outline=(255, 255, 255, 220), width=max(2, radius // 12)
    )
    canvas.alpha_composite(frame_layer)

    pad = max(10, min(x1 - x0, y1 - y0) // 28)
    target = (max(1, x1 - x0 - 2 * pad), max(1, y1 - y0 - 2 * pad))
    contained, capture_pixel_mode = _contain(capture, target)
    px = x0 + pad + (target[0] - contained.width) // 2
    py = y0 + pad + (target[1] - contained.height) // 2
    mask = Image.new("L", contained.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, contained.width - 1, contained.height - 1), radius=max(1, radius - pad), fill=255
    )
    canvas.paste(contained, (px, py), mask)
    return capture_pixel_mode


def _paste_logo(canvas: Any, logo: Any, x: int, y: int, box: tuple[int, int]) -> None:
    if logo.mode not in ("RGBA", "LA"):
        logo = logo.convert("RGBA")
    else:
        logo = logo.convert("RGBA")
    contained = ImageOps.contain(logo, box, method=Image.Resampling.LANCZOS)
    canvas.alpha_composite(contained, (x, y))


def _overlay_gradient(canvas: Any, tint: tuple[int, int, int]) -> None:
    width, height = canvas.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    gradient_height = max(1, int(height * 0.60))
    for y in range(gradient_height):
        # The upper third remains dark enough for white copy; the lower part
        # fades to a transparent tint so the supplied scene remains visible.
        alpha = int(205 * (1 - y / gradient_height) ** 1.4)
        draw.line((0, y, width, y), fill=(*tint, alpha), width=1)
    canvas.alpha_composite(overlay)


def _draw_copy(canvas: Any, title: str, subtitle: str, margin: int, text_y: int, platform: str) -> None:
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    scale = max(1, min(width, height) // 480)
    title_font = load_font(max(30, int(min(width, height) * (0.047 if platform in {"douyin", "xiaohongshu"} else 0.060))), bold=True)
    subtitle_font = load_font(max(20, int(min(width, height) * 0.030)), bold=False)
    max_width = width - margin * 2
    y = text_y
    for line in wrap_pixels(draw, title.strip(), title_font, max_width)[:3]:
        draw.text((margin, y), line, fill=(255, 255, 255, 255), font=title_font)
        y += draw.textbbox((0, 0), line, font=title_font)[3] + max(8, 10 * scale)
    if subtitle.strip():
        y += max(4, 4 * scale)
        for line in wrap_pixels(draw, subtitle.strip(), subtitle_font, max_width)[:3]:
            draw.text((margin, y), line, fill=(226, 232, 240, 255), font=subtitle_font)
            y += draw.textbbox((0, 0), line, font=subtitle_font)[3] + max(5, 6 * scale)


def _compose_image(
    background: Any,
    capture: Any,
    logo: Any,
    size: tuple[int, int],
    title: str,
    subtitle: str,
    platform: str,
    variation: int,
) -> Any:
    width, height = size
    canvas = _fit(background, size).convert("RGBA")
    _overlay_gradient(canvas, _DETAIL_TINTS[variation % len(_DETAIL_TINTS)])
    margin = max(28, int(min(width, height) * 0.08))
    _paste_logo(canvas, logo, margin, margin, (max(110, int(width * 0.22)), max(44, int(height * 0.11))))

    if variation == 0:
        frame_top, frame_bottom, frame_width = 0.44, 0.90, 0.84
    elif variation == 1:
        frame_top, frame_bottom, frame_width = 0.36, 0.79, 0.74
    else:
        frame_top, frame_bottom, frame_width = 0.49, 0.87, 0.66
    frame_w = int(width * frame_width)
    frame_h = max(120, int(height * (frame_bottom - frame_top)))
    frame_x = (width - frame_w) // 2
    frame_y = int(height * frame_top)
    radius = max(16, int(min(width, height) * 0.025))
    capture_pixel_mode = _paste_product(
        canvas, capture, (frame_x, frame_y, frame_x + frame_w, frame_y + frame_h), radius
    )
    _draw_copy(canvas, title, subtitle, margin, int(height * 0.19), platform)
    if variation > 0:
        label_font = load_font(max(18, int(min(width, height) * 0.026)), bold=True)
        label = _DETAIL_LABELS[variation - 1]
        ImageDraw.Draw(canvas).text(
            (margin, int(height * 0.89)), label, fill=(255, 255, 255, 235), font=label_font
        )
    return canvas.convert("RGB"), capture_pixel_mode


def _safe_margins() -> dict[str, float]:
    return {"top": 0.08, "right": 0.08, "bottom": 0.08, "left": 0.08}


class CommercialVisualCompositor:
    """Compose local, provenance-preserving cover/detail visuals."""

    provider = "local_compositor"

    def render(
        self,
        platform: str,
        title: str,
        subtitle: str,
        background: str | Path,
        product_capture: str | Path,
        logo: str | Path,
        out_dir: str | Path,
        background_source: Mapping[str, Any] | None = None,
    ) -> StageResult:
        generated: list[Path] = []
        target_paths: list[Path] = []
        try:
            if platform not in PLATFORM_SIZES:
                raise ValueError("invalid_platform")
            destination = Path(out_dir).expanduser()
            target_paths = [
                destination / f"{platform}-cover.png",
                *(destination / f"{platform}-detail-{index:02d}.png" for index in range(1, 4)),
                destination / f"{platform}-contact-sheet.png",
            ]
            # Clear only this renderer's deterministic targets.  Old assets
            # must not survive a later failed render and be mistaken as ready.
            for target in target_paths:
                target.unlink(missing_ok=True)
                target.with_name(target.name + ".part").unlink(missing_ok=True)
            if not isinstance(title, str) or not title.strip():
                raise ValueError("invalid_title")
            if not isinstance(subtitle, str):
                raise ValueError("invalid_subtitle")
            if not isinstance(background_source, Mapping):
                raise ValueError("missing_ai_scene_provenance")
            provider_value = background_source.get("provider")
            source_value = background_source.get("source", "local-input")
            license_value = background_source.get("license")
            if not isinstance(provider_value, str) or not isinstance(source_value, str) or not isinstance(license_value, str):
                raise ValueError("invalid_ai_scene_provenance")
            ai_provider = provider_value.strip()
            ai_source = source_value.strip()
            ai_license = license_value.strip()
            if not ai_provider or not ai_source or not ai_license:
                raise ValueError("invalid_ai_scene_provenance")
            background_path, background_image = _read_local_image(background, "background")
            capture_path, capture_image = _read_local_image(product_capture, "product_capture")
            logo_path, logo_image = _read_local_image(logo, "logo")
            capture_hash = _sha256(capture_path)
            background_hash = _sha256(background_path)
            logo_hash = _sha256(logo_path)
            destination.mkdir(parents=True, exist_ok=True)
            width, height = PLATFORM_SIZES[platform]
            safe = _safe_margins()

            paths: list[tuple[str, Path, int]] = [("cover_image", target_paths[0], 0)]
            paths.extend(
                ("detail_image", target_paths[index], index)
                for index in range(1, 4)
            )
            capture_pixel_modes: dict[str, str] = {}
            for artifact_type, path, variation in paths:
                image, pixel_mode = _compose_image(
                    background_image,
                    capture_image,
                    logo_image,
                    (width, height),
                    title,
                    subtitle,
                    platform,
                    variation,
                )
                _atomic_save(image, path)
                generated.append(path)
                capture_pixel_modes[path.name] = pixel_mode

            # Make a small but readable audit sheet from the just-written PNGs.
            sheet_width = 760
            thumb_width = 220
            thumb_height = max(150, int(thumb_width * height / width))
            sheet_height = 90 + len(generated) * (thumb_height + 48)
            sheet = Image.new("RGB", (sheet_width, sheet_height), "#111827")
            sheet_draw = ImageDraw.Draw(sheet)
            sheet_font = load_font(22, bold=True)
            sheet_draw.text((24, 20), f"{platform} · commercial visual contact sheet", fill="white", font=sheet_font)
            for index, path in enumerate(generated):
                thumb = ImageOps.contain(Image.open(path).convert("RGB"), (thumb_width, thumb_height))
                y = 70 + index * (thumb_height + 48)
                sheet.paste(thumb, (24, y))
                label = "cover" if index == 0 else f"detail-{index:02d}"
                sheet_draw.text((270, y + thumb_height // 2), f"{platform} / {label}", fill="#e5e7eb", font=sheet_font)
            contact_path = destination / f"{platform}-contact-sheet.png"
            _atomic_save(sheet, contact_path)
            generated.append(contact_path)

            common = {
                "containsProductCapture": True,
                "productCaptureSha256": capture_hash,
                "hasBrand": True,
                "usesAiScene": True,
                "dimensions": [width, height],
                "safeMargins": safe,
                "backgroundSha256": background_hash,
                "logoSha256": logo_hash,
                "aiSceneProvenance": {
                    "provider": ai_provider,
                    "source": ai_source,
                    "license": ai_license,
                    "sha256": background_hash,
                },
            }
            artifacts: list[Artifact] = []
            for artifact_type, path, _variation in paths:
                artifact = Artifact.from_file(artifact_type, path, self.provider, "local-composite", ai_license)
                artifacts.append(
                    replace(
                        artifact,
                        metadata={
                            **common,
                            "capturePixelMode": capture_pixel_modes[path.name],
                            "sourcePixelsEmbedded": True,
                            "productCaptureProvenance": {
                                "source": "local-input",
                                "sha256": capture_hash,
                            },
                        },
                    )
                )
            contact_artifact = Artifact.from_file(
                "contact_sheet", contact_path, self.provider, "local-composite", ai_license
            )
            artifacts.append(
                replace(
                    contact_artifact,
                    metadata={"count": len(paths), "platforms": [platform], "labels": ["cover", "detail-01", "detail-02", "detail-03"]},
                )
            )
            return StageResult.ready(
                self.provider,
                artifacts,
                diagnostics={"platform": platform, "dimensions": [width, height], "count": len(artifacts)},
            )
        except Exception as exc:
            for path in {*generated, *target_paths}:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
                path.with_name(path.name + ".part").unlink(missing_ok=True)
            error_code = str(exc) if str(exc) in {
                "invalid_platform",
                "invalid_title",
                "invalid_subtitle",
                "missing_ai_scene_provenance",
                "invalid_ai_scene_provenance",
                "pillow_unavailable",
                "background_not_readable",
                "product_capture_not_readable",
                "logo_not_readable",
                "background_invalid_image",
                "product_capture_invalid_image",
                "logo_invalid_image",
                "background_must_be_local",
                "product_capture_must_be_local",
                "logo_must_be_local",
            } else "visual_composition_failed"
            return StageResult(
                status="failed",
                provider=self.provider,
                error_code=error_code,
                warnings=("No commercial visual artifacts were marked ready.",),
                diagnostics={"platform": platform},
            )


__all__ = ["CommercialVisualCompositor", "PLATFORM_SIZES"]

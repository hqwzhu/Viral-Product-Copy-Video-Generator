"""Local HyperFrames + FFmpeg product-demo rendering.

This module deliberately keeps the browser renderer behind a small process
boundary.  The composition is data-driven and only receives assets explicitly
selected by the caller; it never uploads a browser profile, cookies, or tokens.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Mapping

from scripts.media_pipeline.contracts import Artifact, StageResult


MOTION_TYPES = ("zoomPan", "productHighlight", "sceneTransition")
DEFAULT_SIZE = (1920, 1080)
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "references" / "hyperframes-professional"
RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "tools" / "hyperframes-runtime"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _script_json(value: Any) -> str:
    """Serialize data for an inline script without allowing HTML termination."""

    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _safe_asset_path(value: Any) -> Path:
    if isinstance(value, Mapping):
        value = value.get("path") or value.get("file") or value.get("src")
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise ValueError("video asset path is required")
    text = str(value)
    if "://" in text or text.startswith("data:"):
        raise ValueError("video assets must be local files")
    path = Path(text).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _asset_name(path: Path, index: int, suffix: str | None = None) -> str:
    ext = suffix or path.suffix.lower() or ".bin"
    if not ext.startswith("."):
        ext = "." + ext
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:10]
    return f"asset-{index:03d}-{digest}{ext}"


def _materialize_asset(value: Any, assets_dir: Path, index: int) -> str:
    source = _safe_asset_path(value)
    target = assets_dir / _asset_name(source, index)
    shutil.copyfile(source, target)
    return target.relative_to(assets_dir.parent).as_posix()


def sample_composition_data(root: Path | None = None) -> dict[str, Any]:
    """Create deterministic local fixture data used by tests and smoke runs."""

    base = (root or Path(tempfile.mkdtemp(prefix="hyperframes-fixture-"))).resolve()
    source_dir = base / "fixture-assets"
    source_dir.mkdir(parents=True, exist_ok=True)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">'
        '<rect width="1280" height="720" fill="#152849"/>'
        '<rect x="80" y="90" width="1120" height="80" rx="18" fill="#2f72dc"/>'
        '<rect x="120" y="250" width="1040" height="340" rx="24" fill="#f7f9fc"/>'
        '<circle cx="200" cy="130" r="16" fill="#65e7c0"/>'
        '<text x="140" y="145" fill="white" font-size="34" font-family="Arial">REAL PRODUCT CAPTURE</text>'
        '<text x="180" y="360" fill="#14213d" font-size="48" font-family="Arial">ENHE workflow</text>'
        '<text x="180" y="430" fill="#2f72dc" font-size="32" font-family="Arial">Capture · explain · convert</text>'
        '</svg>'
    ).encode("utf-8")
    assets = []
    for index in range(5):
        path = source_dir / f"capture-{index + 1}.svg"
        if not path.exists():
            path.write_bytes(svg.replace(b"#152849", (f"#{18 + index * 7:02x}{40 + index * 6:02x}{73 + index * 8:02x}").encode()))
        assets.append(path)

    voice = source_dir / "voiceover.wav"
    if not voice.exists():
        # A deterministic 440 Hz bed is deliberately used only as a fixture.
        # Real runs pass the Kokoro/user narration artifact instead.
        rate, seconds = 16000, 20
        with wave.open(str(voice), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            frames = bytearray()
            for sample in range(rate * seconds):
                value = int(8500 * ((sample % (rate // 2)) / (rate // 2) * 2 - 1))
                frames.extend(value.to_bytes(2, "little", signed=True))
            handle.writeframes(bytes(frames))

    duration = 20
    shots = []
    for index, path in enumerate(assets):
        shots.append(
            {
                "id": f"shot-{index + 1}",
                "kind": "product" if index % 2 == 0 else "supporting",
                "start": index * 4,
                "duration": 4,
                "src": str(path),
                "title": ("Show the real workflow" if index == 0 else f"Product moment {index + 1}"),
                "subtitle": "Exact product capture with a clear, focused explanation.",
                "eyebrow": "ENHE AI / PRODUCT DEMO",
                "panX": (-12 + index * 6),
                "panY": (index % 3 - 1) * 8,
                "pointerX": 120 + index * 20,
                "pointerY": -20 + index * 8,
                "provenance": {"source": "local_fixture", "aiGenerated": index % 2 == 1},
            }
        )
    return {
        "width": DEFAULT_SIZE[0],
        "height": DEFAULT_SIZE[1],
        "duration": duration,
        "fps": 30,
        "motionTypes": list(MOTION_TYPES),
        "shots": shots,
        "captions": [
            {"start": index * 4 + 0.4, "duration": 2.8, "text": text}
            for index, text in enumerate(
                ("从真实产品开始", "看见关键工作流", "突出每一个动作", "用场景连接价值", "现在开始转化")
            )
        ],
        "voiceover": str(voice),
        "provenance": {"provider": "local_fixture", "cloudUpload": False},
    }


def _normalise_data(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise ValueError("composition data must be a mapping")
    shots = data.get("shots")
    if not isinstance(shots, (list, tuple)) or len(shots) < 5:
        raise ValueError("professional product demo requires at least five shots")
    width = int(data.get("width", DEFAULT_SIZE[0]))
    height = int(data.get("height", DEFAULT_SIZE[1]))
    duration = float(data.get("duration", max(float(s.get("start", 0)) + float(s.get("duration", 1)) for s in shots)))
    if width < 1 or height < 1 or duration <= 0:
        raise ValueError("composition dimensions and duration must be positive")
    clean = _json_safe(dict(data))
    clean.update({"width": width, "height": height, "duration": duration, "fps": int(data.get("fps", 30))})
    clean["motionTypes"] = list(dict.fromkeys(data.get("motionTypes") or MOTION_TYPES))
    clean["captions"] = list(data.get("captions") or [])
    return clean


def materialize_hyperframes_project(data: Mapping[str, Any], project_dir: str | Path) -> Path:
    """Copy templates and explicitly selected assets into a render project."""

    clean = _normalise_data(data)
    project = Path(project_dir).resolve()
    project.mkdir(parents=True, exist_ok=True)
    assets_dir = project / "assets"
    vendor_dir = project / "vendor"
    assets_dir.mkdir(exist_ok=True)
    vendor_dir.mkdir(exist_ok=True)

    for filename in ("index.html", "style.css", "composition.js"):
        shutil.copyfile(TEMPLATE_DIR / filename, project / filename)
    gsap = RUNTIME_ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    if not gsap.is_file():
        raise FileNotFoundError("local GSAP runtime is not installed")
    shutil.copyfile(gsap, vendor_dir / "gsap.min.js")

    copied = 0
    serialised_shots = []
    for shot in clean["shots"]:
        current = dict(shot)
        current["src"] = _materialize_asset(current["src"], assets_dir, copied)
        copied += 1
        serialised_shots.append(current)
    clean["shots"] = serialised_shots
    voice = clean.get("voiceover")
    if voice:
        clean["voiceover"] = _materialize_asset(voice, assets_dir, copied)
        copied += 1

    (project / "composition-data.json").write_text(
        json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    index = (project / "index.html").read_text(encoding="utf-8")
    index = index.replace('width=1920, height=1080', f'width={clean["width"]}, height={clean["height"]}')
    index = index.replace('data-width="1920"', f'data-width="{clean["width"]}"')
    index = index.replace('data-height="1080"', f'data-height="{clean["height"]}"')
    index = index.replace('data-duration="20"', f'data-duration="{clean["duration"]}"')
    payload = _script_json(clean)
    index = index.replace(
        '<script id="composition-data"></script>',
        f'<script id="composition-data" type="application/json">{payload}</script>',
    )
    (project / "index.html").write_text(index, encoding="utf-8")
    style_path = project / "style.css"
    style = style_path.read_text(encoding="utf-8")
    style = style.replace("--width: 1920px", f"--width: {clean['width']}px")
    style = style.replace("--height: 1080px", f"--height: {clean['height']}px")
    style_path.write_text(style, encoding="utf-8")
    return project


def hyperframes_executable() -> Path | None:
    local = RUNTIME_ROOT / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
    if local.is_file():
        return local
    found = shutil.which("hyperframes")
    return Path(found) if found else None


def _tool(name: str) -> str | None:
    return shutil.which(name)


def professional_render_available() -> bool:
    return hyperframes_executable() is not None and _tool("node") is not None and _tool("ffmpeg") is not None and _tool("ffprobe") is not None


def _resolution_preset(width: int, height: int) -> str:
    presets = {
        (1920, 1080): "landscape",
        (1080, 1920): "portrait",
        (3840, 2160): "landscape-4k",
        (2160, 3840): "portrait-4k",
        (1080, 1080): "square",
        (2160, 2160): "square-4k",
    }
    try:
        return presets[(width, height)]
    except KeyError as exc:
        raise ValueError("unsupported_hyperframes_resolution") from exc


def _run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )


def probe_media(path: str | Path) -> dict[str, Any]:
    video = Path(path).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    ffprobe = _tool("ffprobe")
    ffmpeg = _tool("ffmpeg")
    if not ffprobe or not ffmpeg:
        raise RuntimeError("FFmpeg and ffprobe are required for media inspection")
    result = _run([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)])
    payload = json.loads(result.stdout or "{}")
    streams = payload.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
    duration = float(payload.get("format", {}).get("duration", 0) or 0)
    volume = _run([ffmpeg, "-hide_banner", "-i", str(video), "-af", "volumedetect", "-f", "null", "NUL"]).stderr
    mean_volume = None
    max_volume = None
    for line in volume.splitlines():
        if "mean_volume:" in line:
            mean_volume = float(line.split("mean_volume:", 1)[1].split("dB", 1)[0].strip())
        elif "max_volume:" in line:
            max_volume = float(line.split("max_volume:", 1)[1].split("dB", 1)[0].strip())
    width = int(video_stream.get("width", 0) or 0)
    height = int(video_stream.get("height", 0) or 0)
    return {
        "videoCodec": video_stream.get("codec_name", ""),
        "audioCodec": audio_stream.get("codec_name", ""),
        "duration": duration,
        "width": width,
        "height": height,
        "shortEdge": min(width, height),
        "meanVolume": mean_volume,
        "maxVolume": max_volume,
        "nonSilent": mean_volume is not None and mean_volume > -50,
        "videoStreams": sum(item.get("codec_type") == "video" for item in streams),
        "audioStreams": sum(item.get("codec_type") == "audio" for item in streams),
    }


def _encode_final(raw: Path, output: Path, voiceover: Path | None, duration: float) -> None:
    ffmpeg = _tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is required for final encoding")
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_name(output.name + ".part")
    part.unlink(missing_ok=True)
    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw)]
    if voiceover:
        command += ["-i", str(voiceover)]
        command += ["-filter_complex", "[1:a]loudnorm=I=-16:LRA=11:TP=-1.5[a]"]
        command += ["-map", "0:v:0", "-map", "[a]"]
    else:
        command += ["-map", "0:v:0"]
        if probe_media(raw).get("audioStreams"):
            command += ["-map", "0:a:0"]
    command += [
        "-t", f"{duration:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-f", "mp4", str(part),
    ]
    try:
        _run(command)
        if not part.is_file() or part.stat().st_size <= 0:
            raise RuntimeError("final_video_part_missing")
        part.replace(output)
    finally:
        part.unlink(missing_ok=True)


def _quality_errors(clean: Mapping[str, Any], probe: Mapping[str, Any]) -> list[str]:
    """Return hard failures for the professional-video acceptance contract."""

    errors: list[str] = []
    if probe.get("videoCodec") != "h264":
        errors.append("video_codec_not_h264")
    if probe.get("audioCodec") != "aac":
        errors.append("audio_codec_not_aac")
    if probe.get("videoStreams") != 1 or probe.get("audioStreams") != 1:
        errors.append("stream_count_invalid")
    if probe.get("nonSilent") is not True:
        errors.append("audio_silent")
    if int(probe.get("shortEdge", 0) or 0) < 1080:
        errors.append("resolution_below_1080_short_edge")
    duration = float(probe.get("duration", 0) or 0)
    target_duration = float(clean.get("duration", 0) or 0)
    if not math.isfinite(duration) or duration <= 0:
        errors.append("duration_invalid")
    elif not math.isfinite(target_duration) or target_duration <= 0 or duration < target_duration * 0.9 or duration > target_duration + 0.5:
        errors.append("duration_out_of_range")

    shots = clean.get("shots")
    if not isinstance(shots, (list, tuple)):
        errors.append("shots_missing")
        shots = []
    product_count = sum(isinstance(shot, Mapping) and shot.get("kind") == "product" for shot in shots)
    supporting_count = sum(isinstance(shot, Mapping) and shot.get("kind") in {"supporting", "broll", "ai_scene"} for shot in shots)
    if product_count < 3:
        errors.append("product_shots_below_three")
    if supporting_count < 2:
        errors.append("supporting_shots_below_two")
    motion_types = set(clean.get("motionTypes") or ())
    if not set(MOTION_TYPES).issubset(motion_types):
        errors.append("motion_types_incomplete")
    provenance = clean.get("provenance")
    if not isinstance(provenance, Mapping) or provenance.get("cloudUpload") is not False:
        errors.append("cloud_upload_provenance_invalid")
    if not clean.get("voiceover"):
        errors.append("voiceover_missing")
    if not all(isinstance(shot, Mapping) and isinstance(shot.get("provenance"), Mapping) and str(shot["provenance"].get("source") or "").strip() for shot in shots):
        errors.append("shot_provenance_missing")
    captions = clean.get("captions") or []
    for caption in captions:
        try:
            start = float(caption.get("start", 0))
            caption_duration = float(caption.get("duration", 0))
        except (AttributeError, TypeError, ValueError):
            errors.append("caption_timing_invalid")
            break
        if not math.isfinite(start) or not math.isfinite(caption_duration) or start < 0 or caption_duration <= 0 or start + caption_duration > target_duration + 1e-6:
            errors.append("caption_timing_invalid")
            break
    return list(dict.fromkeys(errors))


def render_professional_video(data: Mapping[str, Any], output: str | Path, project_dir: str | Path | None = None) -> StageResult:
    """Render a HyperFrames project, then normalize and inspect its MP4."""

    clean = _normalise_data(data)
    output_path = Path(output).resolve()
    workspace = Path(project_dir).resolve() if project_dir else output_path.parent / f".{output_path.stem}-hyperframes"
    raw = workspace / "raw.mp4"
    staged_output = output_path.with_name(output_path.name + ".quality.part.mp4")
    staged_output.unlink(missing_ok=True)
    try:
        materialize_hyperframes_project(clean, workspace)
        executable = hyperframes_executable()
        node = _tool("node")
        if executable is None or node is None:
            raise RuntimeError("HyperFrames local runtime is unavailable")
        resolution = _resolution_preset(int(clean["width"]), int(clean["height"]))
        command = [node, str(executable), "render", str(workspace), "--output", str(raw), "--quality", "high", "--workers", "1", "--low-memory-mode", "--strict", "--no-best-effort", "--resolution", resolution]
        _run(command, cwd=workspace)
        voice = clean.get("voiceover")
        voice_path = _safe_asset_path(voice) if voice else None
        source_hashes = []
        for shot in clean["shots"]:
            source = _safe_asset_path(shot["src"])
            source_hashes.append(
                {
                    "shotId": str(shot.get("id", "")),
                    "sha256": _file_sha256(source),
                    "provenance": shot.get("provenance", {}),
                }
            )
        voiceover_sha256 = _file_sha256(voice_path) if voice_path else None
        source_asset_count = len(source_hashes) + (1 if voice_path else 0)
        contains_user_data = bool(clean.get("containsUserData", clean.get("contains_user_data", False)))
        _encode_final(raw, staged_output, voice_path, float(clean["duration"]))
        probe = probe_media(staged_output)
        quality_errors = _quality_errors(clean, probe)
        if quality_errors:
            staged_output.unlink(missing_ok=True)
            return StageResult(
                status="failed",
                provider="hyperframes_ffmpeg_local",
                error_code="professional_video_quality_gate_failed",
                warnings=tuple(quality_errors),
                diagnostics={"project": str(workspace), "probe": probe, "qualityErrors": quality_errors},
            )
        staged_output.replace(output_path)
        artifact = Artifact.from_file(
            "professional_product_demo_video",
            output_path,
            "hyperframes_ffmpeg_local",
            "local-composition",
            "Apache-2.0",
        )
        artifact = Artifact(
            type=artifact.type,
            path=artifact.path,
            sha256=artifact.sha256,
            source=artifact.source,
            license=artifact.license,
            provider=artifact.provider,
            contains_user_data=contains_user_data,
            metadata={
                "probe": probe,
                "shotCount": len(clean["shots"]),
                "motionTypes": clean["motionTypes"],
                "captionCount": len(clean.get("captions", [])),
                "shotIds": [str(shot.get("id", "")) for shot in clean["shots"]],
                "productShotCount": sum(shot.get("kind") == "product" for shot in clean["shots"]),
                "supportingSceneCount": sum(shot.get("kind") in {"supporting", "broll", "ai_scene"} for shot in clean["shots"]),
                "shotProvenance": [shot.get("provenance", {}) for shot in clean["shots"]],
                "sourceHashes": source_hashes,
                "sourceAssetCount": source_asset_count,
                "voiceoverSha256": voiceover_sha256,
                "containsUserData": contains_user_data,
                "cloudUpload": False,
            },
        )
        return StageResult.ready(
            "hyperframes_ffmpeg_local",
            [artifact],
            diagnostics={
                "probe": probe,
                "project": str(workspace),
                "motionTypes": clean["motionTypes"],
                "shotCount": len(clean["shots"]),
                "shotIds": [str(shot.get("id", "")) for shot in clean["shots"]],
                "productShotCount": sum(shot.get("kind") == "product" for shot in clean["shots"]),
                "supportingSceneCount": sum(shot.get("kind") in {"supporting", "broll", "ai_scene"} for shot in clean["shots"]),
                "captionCount": len(clean.get("captions", [])),
                "captionTimingValid": all(
                    float(caption.get("start", 0)) >= 0
                    and float(caption.get("start", 0)) + float(caption.get("duration", 0)) <= float(clean["duration"]) + 1e-6
                    for caption in clean.get("captions", [])
                ),
                "shotProvenance": [shot.get("provenance", {}) for shot in clean["shots"]],
                "sourceHashes": source_hashes,
                "sourceAssetCount": source_asset_count,
                "voiceoverSha256": voiceover_sha256,
                "containsUserData": contains_user_data,
                "cloudUpload": False,
            },
        )
    except subprocess.CalledProcessError as exc:
        staged_output.unlink(missing_ok=True)
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return StageResult(status="failed", provider="hyperframes_ffmpeg_local", error_code="professional_video_failed", warnings=(detail[-4000:],), diagnostics={"project": str(workspace), "command": exc.cmd})
    except Exception as exc:
        staged_output.unlink(missing_ok=True)
        return StageResult(status="failed", provider="hyperframes_ffmpeg_local", error_code="professional_video_failed", warnings=(str(exc),), diagnostics={"project": str(workspace)})


def render_fixture_professional_video(out_dir: str | Path) -> StageResult:
    root = Path(out_dir).resolve()
    data = sample_composition_data(root)
    return render_professional_video(data, root / "professional-demo.mp4", root / "hyperframes-project")


__all__ = [
    "MOTION_TYPES",
    "materialize_hyperframes_project",
    "hyperframes_executable",
    "professional_render_available",
    "probe_media",
    "render_professional_video",
    "render_fixture_professional_video",
    "sample_composition_data",
]

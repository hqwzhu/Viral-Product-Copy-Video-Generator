"""Fail-closed media quality evaluation and artifact inspection.

The media providers return :class:`~scripts.media_pipeline.contracts.StageResult`
objects.  A provider saying ``ready`` is not, by itself, evidence that a usable
asset exists: the quality gate re-hashes every file, inspects PNG/MP4 bytes,
checks provenance, and rejects sensitive paths or cloud-upload claims.  The
module is intentionally local-only and writes reports atomically.
"""

from __future__ import annotations

import hashlib
import math
import mimetypes
import re
import struct
import wave
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scripts.media_pipeline.contracts import Artifact, StageResult, atomic_write_json

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is optional for the core module
    Image = None  # type: ignore[assignment]

try:
    # Keep the import surface narrow.  ``probe_media`` itself only invokes
    # ffprobe/ffmpeg when a video is inspected, so importing this module does
    # not start a process or contact a network service.
    from scripts.media_pipeline.video import probe_media
except Exception:  # pragma: no cover - ffmpeg/runtime may not be installed
    probe_media = None  # type: ignore[assignment]


QUALITY_STATUSES = {
    "draft_ready",
    "standard_ready",
    "professional_ready",
    "partial_ready",
}

# Kept as a public constant so callers can show a stable acceptance matrix.
PROFESSIONAL_CHECKS = (
    "non_silent_voice",
    "five_distinct_shots",
    "three_product_captures",
    "two_supporting_scenes",
    "three_motion_types",
    "captions_synced",
    "short_edge_1080",
    "h264_aac",
    "ai_photographic_scene",
    "commercial_cover",
    "commercial_details",
    "contact_sheet",
)

_SENSITIVE_PATH_PARTS = (
    "cookies",
    "cookie",
    "local storage",
    "localstorage",
    "login data",
    "login_data",
    "session storage",
    "session_storage",
    "user data",
    "user_data",
    "profile lock",
    "profile_lock",
    "access token",
    "access_token",
    "refresh token",
    "refresh_token",
    "credentials",
    "credential",
    "secrets",
    ".env",
)
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "cookies",
    "password",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "headers",
    "user_data_dir",
    "profile_path",
}
_VIDEO_TYPES = {
    "product_capture_video",
    "professional_product_demo_video",
    "video",
}
_IMAGE_TYPES = {
    "product_capture_image",
    "ai_scene_image",
    "ai_scene",
    "b_roll_image",
    "pexels_b_roll_image",
    "cover_image",
    "detail_image",
    "contact_sheet",
    "supporting_scene_image",
}
_KNOWN_ARTIFACT_TYPES = _VIDEO_TYPES | _IMAGE_TYPES | {"voiceover_audio", "audio"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Artifact):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _artifact_metadata(value: Mapping[str, Any]) -> dict[str, Any]:
    metadata = value.get("metadata")
    return dict(metadata) if isinstance(metadata, Mapping) else {}


def _contains_sensitive(value: Any, key_path: str = "") -> str | None:
    """Return the first secret-bearing key, or ``None``.

    This is deliberately a rejection scanner, rather than a redaction helper:
    a quality report must never claim a sensitive artifact was safe to publish.
    Values are also checked for common bearer/API-key forms because old reports
    occasionally used non-standard key names.
    """

    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key).casefold().replace("-", "_")
            current = f"{key_path}.{key}" if key_path else str(key)
            if name in _SENSITIVE_KEYS or any(part in name for part in ("token", "secret", "password", "cookie")):
                return current
            found = _contains_sensitive(item, current)
            if found:
                return found
        return None
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            found = _contains_sensitive(item, f"{key_path}[{index}]")
            if found:
                return found
        return None
    if isinstance(value, str):
        lowered = value.casefold()
        userinfo = False
        if "://" in lowered:
            try:
                parsed = urlsplit(lowered)
                userinfo = bool(parsed.username or parsed.password)
            except ValueError:
                userinfo = False
        if (
            "bearer " in lowered
            or re.search(r"(?:^|[?&#\s])(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth(?:orization)?|password|cookie|secret|token)\s*=", lowered)
            or userinfo
            or "leak_" in lowered
            or lowered.startswith(("sk-", "fc-", "ghp_", "xox"))
        ):
            return key_path or "value"
    return None


def _sensitive_path(path: str) -> str | None:
    lowered = str(path).replace("\\", "/").casefold()
    for part in _SENSITIVE_PATH_PARTS:
        if part in lowered:
            return part
    return None


def _check(name: str, passed: bool, *, details: Any = None, blocker: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "passed": bool(passed)}
    if details is not None:
        result["details"] = details
    if blocker and not passed:
        result["blocker"] = blocker
    return result


def _safe_report_value(value: Any) -> Any:
    """Recursively remove bearer tokens and secret-bearing evidence fields."""

    if isinstance(value, Mapping):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key).casefold().replace("-", "_")
            if name in _SENSITIVE_KEYS or any(marker in name for marker in ("token", "secret", "password", "cookie")):
                safe[str(key)] = "redacted_sensitive_value"
            else:
                safe[str(key)] = _safe_report_value(item)
        return safe
    if isinstance(value, (list, tuple, set)):
        return [_safe_report_value(item) for item in value]
    if isinstance(value, str) and _contains_sensitive(value):
        return "redacted_sensitive_value"
    return value


def _distinct_hashes(items: Any, key: str = "sha256") -> set[str]:
    if not isinstance(items, (list, tuple)):
        return set()
    values: set[str] = set()
    for item in items:
        if isinstance(item, Mapping):
            value = item.get(key) or item.get("hash") or item.get("productCaptureSha256")
        else:
            value = getattr(item, key, None)
        if isinstance(value, str) and value:
            values.add(value)
    return values


def _bool_metadata(item: Any, name: str) -> bool:
    if isinstance(item, Mapping):
        return bool(item.get(name))
    return bool(getattr(item, name, False))


def _check_evidence(evidence: Mapping[str, Any], name: str) -> tuple[bool, Any, str]:
    probe = evidence.get("probe") if isinstance(evidence.get("probe"), Mapping) else {}
    captures = evidence.get("productCaptures") or []
    if not captures and evidence.get("productCaptureHashes"):
        captures = [{"sha256": value} for value in evidence.get("productCaptureHashes", [])]
    supporting = evidence.get("supportingScenes") or evidence.get("bRoll") or []
    if not supporting and evidence.get("supportingSceneHashes"):
        supporting = [{"sha256": value} for value in evidence.get("supportingSceneHashes", [])]
    ai_scenes = evidence.get("aiScenes") or []
    covers = evidence.get("covers") or []
    details = evidence.get("detailImages") or []
    contacts = evidence.get("contactSheets") or []
    videos = evidence.get("videos") or evidence.get("video") or []
    if not isinstance(videos, (list, tuple)):
        videos = [videos] if videos else []

    if name == "non_silent_voice":
        voiceover = evidence.get("voiceover") if isinstance(evidence.get("voiceover"), Mapping) else {}
        value = probe.get("nonSilent", voiceover.get("nonSilent", evidence.get("nonSilentVoice")))
        return bool(value), value, "voiceover_non_silent"
    if name == "five_distinct_shots":
        shot_ids = evidence.get("shotIds") or []
        if not shot_ids and videos:
            shot_ids = next((item.get("shotIds", []) for item in videos if isinstance(item, Mapping)), [])
        return len({str(value) for value in shot_ids}) >= 5, len({str(value) for value in shot_ids}), "five_distinct_shots_required"
    if name == "three_product_captures":
        hashes = _distinct_hashes(captures)
        return len(hashes) >= 3, len(hashes), "three_product_captures_required"
    if name == "two_supporting_scenes":
        hashes = _distinct_hashes(supporting)
        if len(hashes) < 2:
            hashes = _distinct_hashes(ai_scenes)
        return len(hashes) >= 2, len(hashes), "two_supporting_scenes_required"
    if name == "three_motion_types":
        motions = {str(value) for value in (evidence.get("motionTypes") or [])}
        return {"zoomPan", "productHighlight", "sceneTransition"}.issubset(motions), sorted(motions), "three_motion_types_required"
    if name == "captions_synced":
        return bool(evidence.get("captionsSynced")), bool(evidence.get("captionsSynced")), "captions_out_of_sync"
    if name == "short_edge_1080":
        value = probe.get("shortEdge", 0)
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 0
        return value >= 1080, value, "video_resolution_too_small"
    if name == "h264_aac":
        return str(probe.get("videoCodec", "")).casefold() == "h264" and str(probe.get("audioCodec", "")).casefold() == "aac", _safe_report_value(dict(probe)), "video_codec_mismatch"
    if name == "ai_photographic_scene":
        return any(_bool_metadata(item, "aiGenerated") for item in ai_scenes), len(ai_scenes), "ai_photographic_scene_missing"
    if name == "commercial_cover":
        return bool(covers) and all(_bool_metadata(item, "containsProductCapture") and _bool_metadata(item, "hasBrand") for item in covers), len(covers), "commercial_cover_missing"
    if name == "commercial_details":
        return bool(details) and all(_bool_metadata(item, "containsProductCapture") for item in details), len(details), "commercial_details_missing"
    if name == "contact_sheet":
        return bool(contacts), len(contacts), "contact_sheet_missing"
    return False, None, "unknown_quality_check"


def evaluate_media_quality(evidence: Mapping[str, Any] | None, target: str = "professional") -> dict[str, Any]:
    """Evaluate a normalized evidence mapping without trusting provider status.

    This function is intentionally pure and cheap; :func:`run_quality_gate`
    first performs file/hash/probe checks and then supplies this function with
    the evidence that survived inspection.
    """

    if target not in {"draft", "standard", "professional"}:
        raise ValueError("target must be draft, standard, or professional")
    data = dict(evidence) if isinstance(evidence, Mapping) else {}
    blockers: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    required_families = {
        "productCaptures": bool(data.get("productCaptures") or data.get("productCaptureHashes")),
        # A probe alone is not a publishable artifact; require an inspected
        # video family so callers cannot claim readiness from diagnostics only.
        "videos": bool(data.get("videos") or data.get("video")),
        "covers": bool(data.get("covers")),
        "detailImages": bool(data.get("detailImages")),
        "contactSheets": bool(data.get("contactSheets")),
    }
    missing_families = [name for name, present in required_families.items() if not present]

    if target == "draft":
        status = "draft_ready" if any(required_families.values()) else "partial_ready"
        if missing_families:
            blockers.extend(f"{name}_missing" for name in missing_families)
        return {"schemaVersion": "1.0", "target": target, "status": status, "achievedLevel": status, "checks": checks, "blockers": blockers, "warnings": warnings, "missingFamilies": missing_families}

    if missing_families:
        blockers.extend(f"{name}_missing" for name in missing_families)

    for name in PROFESSIONAL_CHECKS:
        passed, details, blocker = _check_evidence(data, name)
        checks.append(_check(name, passed, details=details, blocker=blocker))
        if not passed:
            blockers.append(blocker)

    # Preserve order while removing duplicate blockers, which makes reports
    # stable and easier for downstream automation to consume.
    blockers = list(dict.fromkeys(blockers))
    if missing_families:
        status = "partial_ready"
    elif target == "standard":
        status = "standard_ready"
    elif all(item["passed"] for item in checks):
        status = "professional_ready"
    else:
        status = "standard_ready"
        warnings.append("one_or_more_professional_checks_failed")

    return {
        "schemaVersion": "1.0",
        "target": target,
        "status": status,
        "achievedLevel": status,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "missingFamilies": missing_families,
        "probe": _safe_report_value(dict(data.get("probe"))) if isinstance(data.get("probe"), Mapping) else {},
    }


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("png_header_invalid")
        length_raw = handle.read(4)
        chunk = handle.read(4)
        if len(length_raw) != 4 or chunk != b"IHDR":
            raise ValueError("png_ihdr_missing")
        length = struct.unpack(">I", length_raw)[0]
        if length < 8:
            raise ValueError("png_ihdr_invalid")
        data = handle.read(length)
        if len(data) < 8:
            raise ValueError("png_ihdr_truncated")
        width, height = struct.unpack(">II", data[:8])
    if width < 1 or height < 1:
        raise ValueError("png_dimensions_invalid")
    if Image is not None:
        try:
            with Image.open(path) as image:
                image.verify()
                if image.format != "PNG":
                    raise ValueError("png_format_invalid")
                if tuple(image.size) != (width, height):
                    raise ValueError("png_dimensions_mismatch")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("png_decode_failed") from exc
    return width, height


def _wav_diagnostics(path: Path) -> dict[str, Any]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        rate = handle.getframerate()
        frame_count = handle.getnframes()
        payload = handle.readframes(frame_count)
    if channels < 1 or sample_width < 1 or rate < 1 or frame_count < 1:
        raise ValueError("wav_parameters_invalid")
    return {
        "channels": channels,
        "sampleWidth": sample_width,
        "sampleRate": rate,
        "frames": frame_count,
        "duration": frame_count / rate,
        "nonSilent": any(payload),
    }


def _expected_dimensions(metadata: Mapping[str, Any], artifact_type: str) -> tuple[int, int] | None:
    value = metadata.get("dimensions")
    if value is None and artifact_type == "product_capture_image":
        value = metadata.get("viewport")
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            width, height = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
        if width > 0 and height > 0:
            return width, height
    return None


def _inspect_artifact(artifact: Artifact | Mapping[str, Any]) -> dict[str, Any]:
    value = _as_dict(artifact)
    artifact_type = str(value.get("type", ""))
    path_text = value.get("path")
    metadata = _artifact_metadata(value)
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    if not artifact_type or not isinstance(path_text, str) or not path_text.strip():
        failures.append("artifact_descriptor_invalid")
        raw_path = str(path_text or "")
        safe_path = "redacted_sensitive_value" if _sensitive_path(raw_path) or _contains_sensitive(path_text) else raw_path
        return {"type": artifact_type, "path": safe_path, "passed": False, "failures": failures, "checks": checks}
    path = Path(path_text).expanduser()
    try:
        resolved_path_text = str(path.resolve(strict=False))
    except OSError:
        resolved_path_text = str(path)
    sensitive = _sensitive_path(path_text) or _sensitive_path(resolved_path_text)
    checks.append(_check("sensitive_path", sensitive is None, details=sensitive, blocker="sensitive_path_rejected"))
    if sensitive:
        failures.append("sensitive_path_rejected")
    secret_key = _contains_sensitive(metadata)
    checks.append(_check("metadata_secrets", secret_key is None, details=secret_key, blocker="secret_metadata_rejected"))
    if secret_key:
        failures.append("secret_metadata_rejected")
    type_ok = artifact_type in _KNOWN_ARTIFACT_TYPES
    checks.append(_check("artifact_type_supported", type_ok, details=artifact_type, blocker="artifact_type_unsupported"))
    if not type_ok:
        failures.append("artifact_type_unsupported")
    cloud_upload = metadata.get("cloudUpload", False)
    checks.append(_check("cloud_upload_disabled", cloud_upload is False, details=cloud_upload, blocker="cloud_upload_not_allowed"))
    if cloud_upload is not False:
        failures.append("cloud_upload_not_allowed")
    if not path.is_file():
        failures.append("artifact_missing")
        checks.append(_check("file_exists", False, blocker="artifact_missing"))
        return {"type": artifact_type, "path": "<redacted>" if sensitive else str(path), "passed": False, "failures": list(dict.fromkeys(failures)), "checks": checks}
    try:
        actual_hash = _sha256(path)
    except OSError:
        actual_hash = ""
    expected_hash = value.get("sha256")
    hash_ok = isinstance(expected_hash, str) and len(expected_hash) == 64 and actual_hash.casefold() == expected_hash.casefold()
    checks.append(_check("sha256", hash_ok, details=actual_hash, blocker="artifact_hash_mismatch"))
    if not hash_ok:
        failures.append("artifact_hash_mismatch")
    checks.append(_check("file_exists", True))

    diagnostics: dict[str, Any] = {}
    if artifact_type in _VIDEO_TYPES or path.suffix.casefold() in {".mp4", ".webm", ".mov"}:
        try:
            if probe_media is None:
                raise RuntimeError("video_probe_unavailable")
            probe = probe_media(path)
            safe_probe = _safe_report_value(probe)
            diagnostics["probe"] = safe_probe
            codec_ok = str(probe.get("videoCodec", "")).casefold() == "h264" and str(probe.get("audioCodec", "")).casefold() == "aac"
            duration = float(probe.get("duration", 0) or 0)
            duration_ok = math.isfinite(duration) and duration > 0
            short_edge_ok = int(probe.get("shortEdge", 0) or 0) >= 1080
            non_silent_ok = probe.get("nonSilent") is True
            checks.extend([
                _check("video_codec", codec_ok, details={"video": probe.get("videoCodec"), "audio": probe.get("audioCodec")}, blocker="video_codec_mismatch"),
                _check("video_duration", duration_ok, details=duration, blocker="video_duration_invalid"),
                _check("video_resolution", short_edge_ok, details=probe.get("shortEdge"), blocker="video_resolution_too_small"),
                _check("video_non_silent", non_silent_ok, details=probe.get("nonSilent"), blocker="video_silent"),
            ])
            if not codec_ok:
                failures.append("video_codec_mismatch")
            if not duration_ok:
                failures.append("video_duration_invalid")
            if not short_edge_ok:
                failures.append("video_resolution_too_small")
            if not non_silent_ok:
                failures.append("video_silent")
        except Exception as exc:
            safe_error = _safe_report_value(str(exc))
            diagnostics["probeError"] = safe_error
            failures.append("video_probe_failed")
            checks.append(_check("video_probe", False, details=safe_error, blocker="video_probe_failed"))
    elif artifact_type in {"voiceover_audio", "audio"} or path.suffix.casefold() == ".wav":
        try:
            wav = _wav_diagnostics(path)
            diagnostics["wav"] = wav
            checks.append(_check("wav_valid", True, details=wav))
            non_silent = wav["nonSilent"] is True
            checks.append(_check("wav_non_silent", non_silent, details=wav["nonSilent"], blocker="audio_silent"))
            if not non_silent:
                failures.append("audio_silent")
        except Exception as exc:
            safe_error = _safe_report_value(str(exc))
            diagnostics["wavError"] = safe_error
            failures.append("wav_invalid")
            checks.append(_check("wav_valid", False, details=safe_error, blocker="wav_invalid"))
    elif artifact_type in _IMAGE_TYPES or path.suffix.casefold() == ".png":
        try:
            dimensions = _png_dimensions(path)
            diagnostics["dimensions"] = list(dimensions)
            expected = _expected_dimensions(metadata, artifact_type)
            dimensions_ok = expected is None or dimensions == expected
            checks.append(_check("png_header_and_dimensions", dimensions_ok, details={"actual": list(dimensions), "expected": list(expected) if expected else None}, blocker="png_dimensions_mismatch"))
            if not dimensions_ok:
                failures.append("png_dimensions_mismatch")
        except Exception as exc:
            safe_error = _safe_report_value(str(exc))
            diagnostics["pngError"] = safe_error
            failures.append("png_invalid")
            failures.append(str(safe_error))
            checks.append(_check("png_header_and_dimensions", False, details=safe_error, blocker="png_invalid"))

    # Commercial images must carry the exact product/brand/provenance claims;
    # do not infer them from the filename or provider status.
    if artifact_type in {"cover_image", "detail_image"}:
        for key in ("containsProductCapture", "hasBrand", "usesAiScene"):
            present = metadata.get(key) is True
            checks.append(_check(f"metadata_{key}", present, details=metadata.get(key), blocker=f"metadata_{key}_missing"))
            if not present:
                failures.append(f"metadata_{key}_missing")
        provenance = metadata.get("productCaptureProvenance")
        provenance_ok = isinstance(provenance, Mapping) and isinstance(provenance.get("sha256"), str) and len(provenance.get("sha256", "")) == 64
        checks.append(_check("metadata_provenance", provenance_ok, details=provenance, blocker="metadata_provenance_missing"))
        if not provenance_ok:
            failures.append("metadata_provenance_missing")

    provider_value = str(value.get("provider", ""))
    source_value = str(value.get("source", ""))
    provider_secret = _contains_sensitive(provider_value)
    source_secret = _contains_sensitive(source_value)
    provider_ok = bool(provider_value.strip()) and provider_secret is None
    source_ok = bool(source_value.strip()) and source_secret is None
    checks.extend([
        _check("artifact_provider", provider_ok, details=provider_secret, blocker="artifact_provider_missing" if provider_secret is None else "artifact_provider_secret"),
        _check("artifact_source", source_ok, details=source_secret, blocker="artifact_source_missing" if source_secret is None else "artifact_source_secret"),
    ])
    if not provider_ok:
        failures.append("artifact_provider_secret" if provider_secret else "artifact_provider_missing")
    if not source_ok:
        failures.append("artifact_source_secret" if source_secret else "artifact_source_missing")
    return {
        "type": artifact_type,
        "path": "<redacted>" if sensitive else str(path.resolve()),
        "sha256": actual_hash,
        "passed": not failures,
        "failures": list(dict.fromkeys(failures)),
        "checks": checks,
        "diagnostics": diagnostics,
        "cloudUpload": False,
    }


def _family_for_type(artifact_type: str) -> str | None:
    if artifact_type == "product_capture_image":
        return "productCaptures"
    if artifact_type in {"professional_product_demo_video", "product_capture_video", "video"}:
        return "videos"
    if artifact_type == "voiceover_audio":
        return "voiceovers"
    if artifact_type == "ai_scene_image":
        return "aiScenes"
    if artifact_type == "ai_scene":
        return "aiScenes"
    if artifact_type in {"b_roll_image", "pexels_b_roll_image", "supporting_scene_image"}:
        return "supportingScenes"
    if artifact_type == "cover_image":
        return "covers"
    if artifact_type == "detail_image":
        return "detailImages"
    if artifact_type == "contact_sheet":
        return "contactSheets"
    return None


def _artifact_summary(value: Mapping[str, Any], inspection: Mapping[str, Any]) -> dict[str, Any]:
    metadata = _artifact_metadata(value)
    inspected_path = str(inspection.get("path", value.get("path", "")))
    failures = list(inspection.get("failures", []))
    # A failed sensitive artifact must not turn the report into a path-discovery
    # channel.  Ordinary local paths remain useful for human review.
    if "sensitive_path_rejected" in failures:
        inspected_path = "[redacted-sensitive-path]"
    summary = {
        "type": str(value.get("type", "")),
        "path": inspected_path,
        "sha256": str(inspection.get("sha256", value.get("sha256", ""))),
        "provider": "redacted_sensitive_value" if _contains_sensitive(value.get("provider", "")) else str(value.get("provider", "")),
        "source": "redacted_sensitive_value" if _contains_sensitive(value.get("source", "")) else str(value.get("source", "")),
        "passed": bool(inspection.get("passed")),
        "failures": failures,
    }
    for key in ("aiGenerated", "shotId", "shotIds", "motionTypes", "captionCount", "containsProductCapture", "hasBrand", "usesAiScene", "dimensions", "safeMargins", "cloudUpload"):
        if key in metadata:
            summary[key] = _safe_report_value(metadata[key])
    if "probe" in inspection.get("diagnostics", {}):
        summary["probe"] = _safe_report_value(inspection["diagnostics"]["probe"])
    if "dimensions" in inspection.get("diagnostics", {}):
        summary["dimensions"] = inspection["diagnostics"]["dimensions"]
    return summary


def _stage_map(stage_results: Mapping[str, StageResult] | Iterable[StageResult]) -> dict[str, StageResult]:
    if isinstance(stage_results, Mapping):
        return {str(name): result for name, result in stage_results.items() if isinstance(result, StageResult)}
    return {f"stage-{index + 1:02d}": result for index, result in enumerate(stage_results) if isinstance(result, StageResult)}


def build_quality_report(stage_results: Mapping[str, StageResult] | Iterable[StageResult], target: str = "professional") -> dict[str, Any]:
    """Inspect stage artifacts and return a machine-readable quality report."""

    stages = _stage_map(stage_results)
    evidence: dict[str, Any] = {key: [] for key in ("productCaptures", "videos", "voiceovers", "aiScenes", "supportingScenes", "covers", "detailImages", "contactSheets")}
    artifact_checks: list[dict[str, Any]] = []
    stage_records: dict[str, Any] = {}
    degraded_stages: list[str] = []
    failed_stages: list[str] = []
    for name, result in stages.items():
        safe_warnings: list[str] = []
        for warning in result.warnings:
            safe_warnings.append(
                "redacted_sensitive_warning"
                if _contains_sensitive(warning)
                else str(warning)
            )
        safe_name = "redacted_sensitive_stage" if _contains_sensitive(name) else name
        safe_error_code = "redacted_sensitive_error" if _contains_sensitive(result.error_code) else str(result.error_code)
        stage_records[safe_name] = {
            "status": result.status,
            "provider": "redacted_sensitive_value" if _contains_sensitive(result.provider) else str(result.provider),
            "errorCode": safe_error_code,
            "warnings": safe_warnings,
        }
        if result.status == "degraded":
            degraded_stages.append(safe_name)
        if result.status in {"failed", "skipped"}:
            failed_stages.append(safe_name)
        for artifact in result.artifacts:
            descriptor = artifact.to_dict()
            inspection = _inspect_artifact(artifact)
            artifact_checks.append(_artifact_summary(descriptor, inspection))
            family = _family_for_type(artifact.type)
            if family and inspection.get("passed"):
                summary = _artifact_summary(descriptor, inspection)
                evidence[family].append(summary)
                if family == "videos":
                    probe = inspection.get("diagnostics", {}).get("probe") or {}
                    evidence["probe"] = probe
                    metadata = descriptor.get("metadata") or {}
                    evidence["shotIds"] = metadata.get("shotIds", evidence.get("shotIds", []))
                    evidence["motionTypes"] = metadata.get("motionTypes", evidence.get("motionTypes", []))
                    evidence["captionsSynced"] = metadata.get("captionTimingValid", result.diagnostics.get("captionTimingValid", False))
                if family == "voiceovers":
                    evidence["probe"] = evidence.get("probe", {})
                    evidence["nonSilentVoice"] = True
            elif family and family not in evidence:
                evidence[family] = []
    report = evaluate_media_quality(evidence, target=target)
    artifact_blockers = [
        failure
        for summary in artifact_checks
        for failure in summary.get("failures", [])
    ]
    if artifact_blockers:
        report["blockers"] = list(dict.fromkeys(list(report.get("blockers", [])) + artifact_blockers))
        if report["status"] == "professional_ready":
            report["status"] = "standard_ready"
            report["achievedLevel"] = "standard_ready"
            report["warnings"] = list(report.get("warnings", [])) + ["artifact_quality_failed"]
    # Failed/skipped stages take precedence over degraded fallbacks: a partial
    # pipeline must never be presented as merely standard-ready.
    if failed_stages:
        report["status"] = "partial_ready"
        report["achievedLevel"] = "partial_ready"
        report["blockers"] = list(dict.fromkeys(list(report.get("blockers", [])) + ["stage_failed"]))
    # Stage degradation is honest: a SAPI/FFmpeg fallback may produce usable
    # media but can never claim professional quality.
    elif report["status"] == "professional_ready" and degraded_stages:
        report["status"] = "standard_ready"
        report["achievedLevel"] = "standard_ready"
        report["warnings"] = list(report.get("warnings", [])) + ["degraded_stage_fallback"]
        report["blockers"] = list(dict.fromkeys(list(report.get("blockers", [])) + ["degraded_stage_fallback"]))
    report.update({
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stages": stage_records,
        "artifacts": artifact_checks,
        "artifactCount": len(artifact_checks),
        "degradedStages": degraded_stages,
        "failedStages": failed_stages,
        "cloudUpload": False,
        "evidence": {key: value for key, value in evidence.items() if key not in {"probe"}},
    })
    return report


def write_quality_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    """Write a report atomically and return its resolved destination."""

    destination = Path(path).expanduser().resolve()
    atomic_write_json(destination, dict(report))
    return destination


def run_quality_gate(
    stage_results: Mapping[str, StageResult] | Iterable[StageResult],
    target: str = "professional",
    report_path: str | Path | None = None,
) -> StageResult:
    """Aggregate stages into a quality ``StageResult`` and optional report."""

    # Materialize once so generators are not consumed by report construction
    # and then accidentally produce an empty quality StageResult.
    stages = _stage_map(stage_results)
    report = build_quality_report(stages, target=target)
    if report_path is not None:
        write_quality_report(report_path, report)
    status = report["status"]
    result_status = "ready" if status == "professional_ready" else "degraded" if status in {"standard_ready", "draft_ready"} else "failed"
    artifacts: list[Artifact] = []
    if result_status != "failed":
        # Only artifacts that passed the byte/hash/probe checks may be handed
        # to a downstream publish pack.  A degraded gate can still be useful
        # for review, but it must never carry a failed artifact as ready.
        for result in stages.values():
            if result.status in {"failed", "skipped"}:
                continue
            for artifact in result.artifacts:
                if _inspect_artifact(artifact).get("passed"):
                    artifacts.append(artifact)
    return StageResult(
        status=result_status,
        provider="media_quality_gate",
        artifacts=tuple(artifacts),
        warnings=tuple(report.get("warnings", [])),
        error_code="" if result_status != "failed" else (report.get("blockers") or ["media_quality_failed"])[0],
        diagnostics=report,
    )


# Names used by early integration callers; keep them as thin aliases so the
# quality contract can evolve without breaking the public Skill entry point.
evaluate_stage_results = build_quality_report
quality_gate = run_quality_gate
write_media_quality_report = write_quality_report


__all__ = [
    "PROFESSIONAL_CHECKS",
    "QUALITY_STATUSES",
    "build_quality_report",
    "evaluate_media_quality",
    "evaluate_stage_results",
    "quality_gate",
    "run_quality_gate",
    "write_media_quality_report",
    "write_quality_report",
]

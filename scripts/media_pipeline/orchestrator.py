"""Local, resumable orchestration for the professional media pipeline.

The providers in this module are deliberately injected.  A production caller
can use the Playwright/Kokoro/ComfyUI/HyperFrames providers, while tests can use
small local fakes.  The orchestrator itself never logs in, uploads, or creates a
Hosted Worker.  Every stage writes an atomic receipt and only artifacts that are
still present and have the recorded SHA-256 are eligible for resume.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import shutil
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

from scripts.media_pipeline.capture import PlaywrightCaptureProvider, build_default_capture_plan
from scripts.media_pipeline.contracts import (
    Artifact,
    MediaJob,
    StageResult,
    atomic_write_json,
    stage_result_is_valid,
)
from scripts.media_pipeline.paths import RUNS_DIR, RunPaths, new_run_paths
from scripts.media_pipeline.security import MediaSecurityError, redact_secrets, validate_capture_shot
from scripts.media_pipeline.visuals import CommercialVisualCompositor


STAGES = ("capture", "voiceover", "scenes", "visuals", "video", "quality")
SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_path(path: str | Path, root: Path) -> Path:
    """Resolve a path and reject profile/cookie paths and path escapes."""

    value = Path(path).expanduser().resolve()
    root = root.resolve()
    try:
        value.relative_to(root)
    except ValueError as exc:
        raise MediaSecurityError("media artifact must remain in the local run") from exc
    words = " ".join(part.casefold().replace("_", " ").replace("-", " ") for part in value.parts)
    sensitive = (
        "cookie", "local storage", "login data", "user data", "web data",
        "session storage", "profile", "credential", "password", "access token",
        "refresh token", ".env", "secret",
    )
    if any(token in words for token in sensitive):
        raise MediaSecurityError("sensitive media path is not allowed")
    return value


def _provider_name(provider: Any, fallback: str) -> str:
    value = getattr(provider, "provider", None) or getattr(provider, "provider_name", None)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return provider.__class__.__name__ if provider is not None else fallback


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _load_json(path: str | Path, *, required: bool = False) -> dict[str, Any]:
    source = Path(path).expanduser()
    if not source.is_file():
        if required:
            raise FileNotFoundError(source)
        return {}
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON input must be an object")
    return payload


def _fingerprint(value: Any) -> str:
    """Hash stage inputs, including bytes of local input files."""

    def normalise(item: Any) -> Any:
        if isinstance(item, Path):
            item = str(item)
        if isinstance(item, str):
            path = Path(item).expanduser()
            if path.is_file():
                try:
                    return {"file": str(path.resolve()), "sha256": _sha256(path), "size": path.stat().st_size}
                except OSError:
                    return {"file": str(path.resolve()), "unreadable": True}
            return item
        if isinstance(item, Mapping):
            return {str(k): normalise(v) for k, v in sorted(item.items(), key=lambda pair: str(pair[0]))}
        if isinstance(item, (list, tuple, set)):
            return [normalise(v) for v in item]
        return item

    encoded = json.dumps(normalise(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _artifact_hashes(result: StageResult) -> list[str]:
    return [artifact.sha256 for artifact in result.artifacts]


def _result_dict(result: StageResult) -> dict[str, Any]:
    # All provider fields are receipt data.  Sanitize the complete result,
    # while still allowing local safe paths to remain available for resume.
    return _sanitize_public(_json_safe(result.to_dict()))


def _sanitize_public(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned = {}
        for key, item in value.items():
            name = str(key).casefold().replace("-", "_")
            if any(token in name for token in ("token", "secret", "password", "cookie", "authorization", "credential")):
                cleaned[str(key)] = "[REDACTED]"
            else:
                cleaned[str(key)] = _sanitize_public(item)
        return cleaned
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_public(item) for item in value]
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
            return "[REDACTED]"
        words = lowered.replace("\\", "/").replace("_", " ").replace("-", " ")
        if any(token in words for token in ("cookie", "local storage", "login data", "user data", "profile lock", "credential")):
            return "[REDACTED-SENSITIVE-PATH]"
    return value


def _contains_sensitive_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_sensitive_text(key) or _contains_sensitive_text(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_sensitive_text(item) for item in value)
    if isinstance(value, str):
        lowered = value.casefold().replace("\\", "/").replace("_", " ").replace("-", " ")
        return any(token in lowered for token in ("cookie", "local storage", "login data", "user data", "profile lock", "credential", "access token", "refresh token"))
    return False


def _contains_cloud_upload(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key).casefold().replace("-", "_")
            if name in {"cloudupload", "cloud_upload"} and item is not False:
                return True
            if _contains_cloud_upload(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_cloud_upload(item) for item in value)
    return False


@dataclass(frozen=True)
class OrchestrationResult:
    """The complete local run result returned by :class:`MediaOrchestrator`."""

    run_paths: RunPaths
    stages: Mapping[str, StageResult]
    manifest_path: Path
    receipt_path: Path

    @property
    def status(self) -> str:
        quality = self.stages.get("quality")
        if quality is not None:
            return quality.status
        return "failed" if any(item.status == "failed" for item in self.stages.values()) else "partial"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "runRoot": str(self.run_paths.root),
            "manifestPath": str(self.manifest_path),
            "receiptPath": str(self.receipt_path),
            "stages": {name: _result_dict(result) for name, result in self.stages.items()},
            "cloudUpload": False,
        }


@dataclass
class MediaOrchestrator:
    """Execute the six local stages with atomic receipts and safe resume."""

    capture_provider: Any | None = None
    voiceover_provider: Any | None = None
    scene_provider: Any | None = None
    visual_provider: Any | None = None
    video_provider: Callable[..., StageResult] | None = None
    quality_provider: Callable[..., StageResult] | None = None
    allow_localhost: bool = False
    # Plural aliases mirror the stage names used by the Skill contract.  They
    # are accepted for callers that prefer ``scenes_provider``/``visuals_provider``.
    scenes_provider: Any | None = None
    visuals_provider: Any | None = None

    def __post_init__(self) -> None:
        if self.scene_provider is None:
            self.scene_provider = self.scenes_provider
        if self.visual_provider is None:
            self.visual_provider = self.visuals_provider
        if self.capture_provider is None:
            self.capture_provider = PlaywrightCaptureProvider(allow_localhost=self.allow_localhost)
        if self.voiceover_provider is None:
            from scripts.media_pipeline.voiceover import KokoroVoiceoverProvider

            self.voiceover_provider = KokoroVoiceoverProvider()
        if self.visual_provider is None:
            self.visual_provider = CommercialVisualCompositor()
        # Imports are intentionally lazy for callers that only use fake
        # providers and do not have FFmpeg/Kokoro/ComfyUI installed.
        if self.video_provider is None:
            from scripts.media_pipeline.video import render_professional_video

            self.video_provider = render_professional_video
        if self.quality_provider is None:
            from scripts.media_pipeline.quality import run_quality_gate

            self.quality_provider = run_quality_gate

    def run(
        self,
        job: MediaJob | Mapping[str, Any],
        *,
        output_root: str | Path | None = None,
        run_dir: str | Path | None = None,
        resume: bool = True,
    ) -> OrchestrationResult:
        media_job = job if isinstance(job, MediaJob) else MediaJob.from_dict(dict(job))
        if not isinstance(media_job.allow_cloud_media, bool):
            root = self._prepare_run_root(media_job, output_root, run_dir, resume)
            paths = self._paths_for_root(root).create()
            return self._finish_failed(paths, media_job, "job_validation_failed", "allow_cloud_media must be a boolean")
        if media_job.allow_cloud_media is True:
            root = self._prepare_run_root(media_job, output_root, run_dir, resume)
            paths = self._paths_for_root(root).create()
            return self._finish_failed(paths, media_job, "cloud_media_disabled", "cloud media is disabled")

        root = self._prepare_run_root(media_job, output_root, run_dir, resume)
        paths = self._paths_for_root(root).create()
        try:
            self._validate_job(media_job, root)
        except (MediaSecurityError, ValueError, OSError) as exc:
            return self._finish_failed(paths, media_job, "job_validation_failed", str(exc))

        manifest_path = root / "manifest.json"
        receipt_path = root / "run-receipt.json"
        previous = self._load_manifest(manifest_path) if resume else {}
        stages: dict[str, StageResult] = {}
        records: dict[str, dict[str, Any]] = {}

        # A dependency failure closes all later stages.  Their records are
        # still written so an interrupted run never looks complete.
        failed_dependency: str | None = None
        for stage in STAGES:
            if failed_dependency is not None:
                result = StageResult(status="failed", provider="orchestrator", error_code=f"blocked_by_{failed_dependency}")
                stages[stage] = result
                records[stage] = self._record(stage, result, "blocked", "")
                self._write_state(manifest_path, receipt_path, media_job, paths, records)
                continue

            input_value = self._stage_inputs(stage, media_job, paths, stages)
            input_hash = _fingerprint(input_value)
            resumed = self._resume_result(stage, previous, input_hash, root)
            if resumed is not None:
                stages[stage] = resumed
                records[stage] = self._record(stage, resumed, "skipped", input_hash)
                self._write_state(manifest_path, receipt_path, media_job, paths, records)
                continue

            self._clear_stage_output(stage, paths)
            try:
                result = self._execute_stage(stage, media_job, paths, stages)
                result = self._safe_result(result, root)
            except Exception as exc:  # provider boundaries are fail-closed
                result = StageResult(status="failed", provider="orchestrator", error_code="stage_exception", diagnostics={"stage": stage, "exceptionType": type(exc).__name__})
            if result.status == "failed" and stage != "quality":
                # A provider may have written a partial PNG/WAV/MP4 before
                # returning failure.  Remove it before recording the receipt
                # so a later resume cannot mistake it for evidence.
                self._clear_stage_output(stage, paths)
            stages[stage] = result
            action = "completed" if result.status in {"ready", "degraded"} else "failed"
            records[stage] = self._record(stage, result, action, input_hash)
            self._write_state(manifest_path, receipt_path, media_job, paths, records)
            if result.status == "failed":
                failed_dependency = stage

        # The receipt is written once more with a stable end marker.  The JSON
        # write itself is atomic, so killing the process never leaves a partial
        # manifest that a resume can mistake for ready evidence.
        self._write_state(manifest_path, receipt_path, media_job, paths, records, complete=failed_dependency is None)
        return OrchestrationResult(paths, dict(stages), manifest_path.resolve(), receipt_path.resolve())

    execute = run

    def _prepare_run_root(self, job: MediaJob, output_root: str | Path | None, run_dir: str | Path | None, resume: bool) -> Path:
        if run_dir is not None:
            root = Path(run_dir).expanduser().resolve()
            if resume and root.exists() and not root.is_dir():
                raise ValueError("run_dir must be a directory")
            return root
        base = Path(output_root or "promotion-output_推广输出").expanduser().resolve()
        if resume:
            existing = self._find_run_by_id(base, job.run_id)
            if existing is not None:
                return existing
        return new_run_paths(base, job.product_name).root.resolve()

    @staticmethod
    def _find_run_by_id(output_root: Path, run_id: str) -> Path | None:
        runs = output_root / RUNS_DIR
        if not runs.is_dir():
            return None
        try:
            for manifest in runs.glob("*/manifest.json"):
                try:
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                except (OSError, ValueError, json.JSONDecodeError):
                    continue
                if isinstance(payload, Mapping) and str(payload.get("runId")) == str(run_id):
                    return manifest.parent.resolve()
        except OSError:
            return None
        return None

    @staticmethod
    def _paths_for_root(root: Path) -> RunPaths:
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

    def _validate_job(self, job: MediaJob, root: Path) -> None:
        _safe_path(root, root)
        for item in (job.product_data_path, job.capture_plan_path, job.generated_content_path, *job.brand_assets):
            if item:
                candidate = Path(item).expanduser()
                # Inputs may be outside the run (the user's public product
                # JSON/logo); they are still checked for profile/credential
                # names but are not copied or uploaded by this orchestrator.
                words = " ".join(part.casefold().replace("_", " ").replace("-", " ") for part in candidate.parts)
                if any(token in words for token in ("cookie", "profile", "credential", "password", "token", "user data", ".env")):
                    raise MediaSecurityError("sensitive input path is not allowed")
        validate_capture_shot(job.source_url, {"url": job.source_url, "action": "none"}, allow_localhost=self.allow_localhost)

    def _load_manifest(self, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    def _resume_result(self, stage: str, manifest: Mapping[str, Any], input_hash: str, root: Path) -> StageResult | None:
        record = manifest.get("stages", {}).get(stage) if isinstance(manifest.get("stages"), Mapping) else None
        if not isinstance(record, Mapping) or record.get("inputFingerprint") != input_hash:
            return None
        value = record.get("result")
        if not isinstance(value, Mapping):
            return None
        try:
            result = StageResult.from_dict(dict(value))
        except (KeyError, TypeError, ValueError):
            return None
        if result.status not in {"ready", "degraded"} or not stage_result_is_valid(result):
            return None
        try:
            result = self._safe_result(result, root)
        except (MediaSecurityError, OSError, ValueError):
            return None
        try:
        for artifact in result.artifacts:
            _safe_path(artifact.path, root)
            if _contains_sensitive_text({"source": artifact.source, "license": artifact.license, "metadata": artifact.metadata}):
                raise MediaSecurityError("sensitive artifact metadata is not allowed")
        except (MediaSecurityError, OSError):
            return None
        return replace(result, diagnostics={**dict(result.diagnostics), "resumed": True})

    def _stage_inputs(self, stage: str, job: MediaJob, paths: RunPaths, stages: Mapping[str, StageResult]) -> dict[str, Any]:
        content = self._content(job)
        previous = {
            name: {
                "status": result.status,
                "provider": result.provider,
                "artifactHashes": _artifact_hashes(result),
                "warnings": list(result.warnings),
                "errorCode": result.error_code,
            }
            for name, result in stages.items()
        }
        if stage == "capture":
            plan = self._capture_plan(job)
            return {"stage": stage, "plan": plan, "provider": _provider_name(self.capture_provider, stage)}
        if stage == "voiceover":
            return {"stage": stage, "text": self._narration(content), "language": job.language, "provider": _provider_name(self.voiceover_provider, stage), "capture": previous.get("capture", [])}
        if stage == "scenes":
            return {"stage": stage, "prompt": self._scene_prompt(content), "provider": _provider_name(self.scene_provider, stage), "voiceover": previous.get("voiceover", [])}
        if stage == "visuals":
            return {"stage": stage, "platforms": job.target_platforms, "title": self._title(content, job), "subtitle": self._subtitle(content), "captures": previous.get("capture", []), "scenes": previous.get("scenes", []), "logo": job.brand_assets}
        if stage == "video":
            return {"stage": stage, "platforms": job.target_platforms, "captures": previous.get("capture", []), "scenes": previous.get("scenes", []), "voiceover": previous.get("voiceover", []), "visuals": previous.get("visuals", [])}
        return {"stage": stage, "qualityTarget": job.quality_target, "allStages": previous}

    def _content(self, job: MediaJob) -> dict[str, Any]:
        content = _load_json(job.generated_content_path)
        if not content:
            content = _load_json(job.product_data_path)
        return content

    def _capture_plan(self, job: MediaJob) -> dict[str, Any]:
        plan = _load_json(job.capture_plan_path)
        return plan or build_default_capture_plan(job.source_url)

    @staticmethod
    def _title(content: Mapping[str, Any], job: MediaJob) -> str:
        return str(content.get("title") or content.get("headline") or content.get("name") or job.product_name).strip()

    @staticmethod
    def _subtitle(content: Mapping[str, Any]) -> str:
        return str(content.get("subtitle") or content.get("description") or content.get("summary") or "Turn a product page into publish-ready creative.").strip()

    @staticmethod
    def _narration(content: Mapping[str, Any]) -> str:
        return str(content.get("narration") or content.get("voiceover") or content.get("script") or content.get("body") or "").strip()

    @staticmethod
    def _scene_prompt(content: Mapping[str, Any]) -> str:
        return str(content.get("scenePrompt") or content.get("scene_prompt") or content.get("visualPrompt") or content.get("title") or "Professional product marketing scene").strip()

    def _execute_stage(self, stage: str, job: MediaJob, paths: RunPaths, stages: Mapping[str, StageResult]) -> StageResult:
        content = self._content(job)
        if stage == "capture":
            return self.capture_provider.capture(self._capture_plan(job), paths.captures)
        if stage == "voiceover":
            if self.voiceover_provider is None:
                return StageResult(status="failed", provider="orchestrator", error_code="voiceover_provider_not_configured")
            return self.voiceover_provider.generate(self._narration(content), job.language, paths.voiceovers)
        if stage == "scenes":
            if self.scene_provider is None:
                return StageResult(status="failed", provider="orchestrator", error_code="scene_provider_not_configured")
            return self._generate_scene(self.scene_provider, self._scene_prompt(content), paths.ai_scenes)
        if stage == "visuals":
            return self._render_visuals(job, paths, stages, content)
        if stage == "video":
            return self._render_video(job, paths, stages, content)
        report_path = paths.reports / "quality.json"
        provider = self.quality_provider
        if callable(provider):
            return provider(stages, target=job.quality_target, report_path=report_path)
        runner = getattr(provider, "run", None) or getattr(provider, "evaluate", None)
        if callable(runner):
            return runner(stages, target=job.quality_target, report_path=report_path)
        raise TypeError("quality provider must be callable")

    @staticmethod
    def _generate_scene(provider: Any, prompt: str, out_dir: Path) -> StageResult:
        try:
            return provider.generate(prompt, width=1920, height=1080, seed=7, output_dir=out_dir)
        except TypeError:
            # Tiny fakes often expose a deliberately smaller signature.
            return provider.generate(prompt, out_dir)

    def _render_visuals(self, job: MediaJob, paths: RunPaths, stages: Mapping[str, StageResult], content: Mapping[str, Any]) -> StageResult:
        capture = self._first_artifact(stages.get("capture"), "product_capture_image")
        scene = self._first_scene_artifact(stages.get("scenes"))
        logo = job.brand_assets[0] if job.brand_assets else None
        if capture is None or scene is None or logo is None:
            return StageResult(status="failed", provider="orchestrator", error_code="visual_inputs_missing")
        artifacts: list[Artifact] = []
        warnings: list[str] = []
        for platform in job.target_platforms:
            result = self.visual_provider.render(platform, self._title(content, job), self._subtitle(content), scene.path, capture.path, logo, paths.covers / platform, background_source={"provider": scene.provider, "source": scene.source, "license": scene.license})
            if result.status == "failed":
                return result
            artifacts.extend(result.artifacts)
            warnings.extend(result.warnings)
        return StageResult(status="degraded" if warnings else "ready", provider=_provider_name(self.visual_provider, "visuals"), artifacts=tuple(artifacts), warnings=tuple(warnings), diagnostics={"platforms": list(job.target_platforms), "count": len(artifacts)})

    def _render_video(self, job: MediaJob, paths: RunPaths, stages: Mapping[str, StageResult], content: Mapping[str, Any]) -> StageResult:
        captures = [artifact for artifact in (stages.get("capture").artifacts if stages.get("capture") else ()) if artifact.type == "product_capture_image"]
        scenes = [artifact for artifact in (stages.get("scenes").artifacts if stages.get("scenes") else ()) if artifact.type in {"ai_scene_image", "b_roll_image", "supporting_scene_image", "pexels_b_roll_image"}]
        voice = self._first_artifact(stages.get("voiceover"), "voiceover_audio")
        shots: list[dict[str, Any]] = []
        for index, artifact in enumerate(captures[:3]):
            shots.append({"id": f"product-{index + 1}", "kind": "product", "start": index * 4, "duration": 4, "src": artifact.path, "provenance": {"source": artifact.source, "provider": artifact.provider, "sha256": artifact.sha256}})
        for index, artifact in enumerate(scenes[:2]):
            shots.append({"id": f"scene-{index + 1}", "kind": "supporting", "start": (len(shots)) * 4, "duration": 4, "src": artifact.path, "provenance": {"source": artifact.source, "provider": artifact.provider, "aiGenerated": artifact.metadata.get("aiGenerated", True), "sha256": artifact.sha256}})
        if len(shots) < 5 or voice is None:
            return StageResult(status="failed", provider="orchestrator", error_code="video_inputs_missing")
        duration = max(20, len(shots) * 4)
        language = job.language
        voice_result = stages.get("voiceover")
        captions = []
        if voice_result:
            for segment in voice_result.diagnostics.get("segments", ()):
                try:
                    captions.append({"start": float(segment["start"]), "duration": float(segment["end"]) - float(segment["start"]), "text": str(segment["text"])})
                except (KeyError, TypeError, ValueError):
                    pass
        data = {"width": 1920, "height": 1080, "duration": duration, "durationRange": list(job.duration_range), "fps": 30, "motionTypes": ["zoomPan", "productHighlight", "sceneTransition"], "shots": shots, "captions": captions, "voiceover": voice.path, "provenance": {"provider": "local_orchestrator", "language": language, "cloudUpload": False}}
        return self.video_provider(data, paths.videos / "professional-demo.mp4", paths.videos / ".professional-demo-hyperframes")

    @staticmethod
    def _first_artifact(result: StageResult | None, artifact_type: str) -> Artifact | None:
        if result is None:
            return None
        return next((artifact for artifact in result.artifacts if artifact.type == artifact_type), None)

    @staticmethod
    def _first_scene_artifact(result: StageResult | None) -> Artifact | None:
        if result is None:
            return None
        return next((artifact for artifact in result.artifacts if artifact.type in {"ai_scene_image", "b_roll_image", "supporting_scene_image", "pexels_b_roll_image"}), None)

    def _safe_result(self, result: StageResult, root: Path) -> StageResult:
        if not isinstance(result, StageResult):
            raise TypeError("provider must return StageResult")
        for artifact in result.artifacts:
            safe_artifact_path = _safe_path(artifact.path, root)
            if not safe_artifact_path.is_file() or _sha256(safe_artifact_path) != artifact.sha256:
                raise MediaSecurityError("artifact hash mismatch")
            if _contains_cloud_upload(artifact.to_dict()):
                raise MediaSecurityError("cloud upload is disabled")
            # A capture may legitimately contain user-visible product data.
            # The local-only boundary is enforced by the path and
            # ``cloudUpload`` checks above; ``contains_user_data`` is retained
            # as honest metadata rather than treated as an upload request.
        if _contains_cloud_upload(result.to_dict()):
            raise MediaSecurityError("cloud upload is disabled")
        return result

    def _clear_stage_output(self, stage: str, paths: RunPaths) -> None:
        target = {"capture": paths.captures, "voiceover": paths.voiceovers, "scenes": paths.ai_scenes, "visuals": paths.covers, "video": paths.videos, "quality": paths.reports}[stage]
        if target.exists():
            for child in target.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink(missing_ok=True)

    def _record(self, stage: str, result: StageResult, action: str, input_hash: str) -> dict[str, Any]:
        safe = redact_secrets(_result_dict(result))
        return {"stage": stage, "action": action, "status": result.status, "inputFingerprint": input_hash, "artifactHashes": _artifact_hashes(result), "result": safe, "updatedAt": _utc_now()}

    def _write_state(self, manifest_path: Path, receipt_path: Path, job: MediaJob, paths: RunPaths, records: Mapping[str, Any], *, complete: bool = False) -> None:
        manifest = {"schemaVersion": SCHEMA_VERSION, "runId": job.run_id, "productName": job.product_name, "status": "complete" if complete else "running", "cloudUpload": False, "hostedWorker": False, "runRoot": str(paths.root), "stages": dict(records), "updatedAt": _utc_now()}
        atomic_write_json(manifest_path, manifest)
        atomic_write_json(receipt_path, {"schemaVersion": SCHEMA_VERSION, "runId": job.run_id, "status": manifest["status"], "manifest": str(manifest_path), "stages": {name: {"action": item.get("action"), "status": item.get("status"), "artifactHashes": item.get("artifactHashes", [])} for name, item in records.items()}, "cloudUpload": False, "hostedWorker": False, "updatedAt": manifest["updatedAt"]})
        stage_receipts = paths.reports / "stage-receipts"
        for name, record in records.items():
            atomic_write_json(stage_receipts / f"{name}.json", {"schemaVersion": SCHEMA_VERSION, "runId": job.run_id, **record, "cloudUpload": False, "hostedWorker": False})

    def _finish_failed(self, paths: RunPaths, job: MediaJob, code: str, detail: str) -> OrchestrationResult:
        result = StageResult(status="failed", provider="orchestrator", error_code=code, diagnostics={"exceptionType": detail.__class__.__name__})
        stages = {stage: result for stage in STAGES}
        records = {stage: self._record(stage, result, "failed" if stage == "capture" else "blocked", "") for stage in STAGES}
        self._write_state(paths.root / "manifest.json", paths.root / "run-receipt.json", job, paths, records)
        return OrchestrationResult(paths, stages, (paths.root / "manifest.json").resolve(), (paths.root / "run-receipt.json").resolve())


MediaPipelineOrchestrator = MediaOrchestrator


def run_media_pipeline(job: MediaJob | Mapping[str, Any], **kwargs: Any) -> OrchestrationResult:
    return MediaOrchestrator().run(job, **kwargs)


__all__ = ["STAGES", "MediaOrchestrator", "MediaPipelineOrchestrator", "OrchestrationResult", "run_media_pipeline"]

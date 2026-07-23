import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts import professional_media_pipeline as professional_cli
from scripts.media_pipeline.contracts import Artifact, MediaJob, StageResult
from scripts.media_pipeline.orchestrator import MediaOrchestrator


def _png(path: Path, color: str = "#2454a6") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (320, 180), color).save(path, format="PNG")
    return path


def _artifact(kind: str, path: Path, provider: str = "fake") -> Artifact:
    return Artifact.from_file(kind, path, provider=provider, source="local-fixture", license_id="fixture")


class _Capture:
    provider = "fake_capture"

    def __init__(self):
        self.calls = 0
        self.plan = None

    def capture(self, plan, out_dir):
        self.calls += 1
        self.plan = plan
        out = Path(out_dir)
        return StageResult.ready(self.provider, [_artifact("product_capture_image", _png(out / f"shot-{i}.png")) for i in range(5)])


class _Voice:
    provider = "fake_voice"

    def __init__(self):
        self.calls = 0

    def generate(self, _text, _language, out_dir):
        self.calls += 1
        path = Path(out_dir) / "voice.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"RIFF" + b"fixture voice")
        artifact = _artifact("voiceover_audio", path, self.provider)
        return StageResult.ready(self.provider, [artifact], {"segments": [{"start": 0, "end": 20, "text": "fixture"}]})


class _Scenes:
    provider = "fake_scenes"

    def generate(self, _prompt, **kwargs):
        out = Path(kwargs.get("output_dir"))
        return StageResult.ready(self.provider, [_artifact("ai_scene_image", _png(out / "scene-1.png", "#b34a1d")), _artifact("ai_scene_image", _png(out / "scene-2.png", "#1a8f65"))])


class _Visuals:
    provider = "fake_visuals"

    def render(self, platform, _title, _subtitle, _background, _capture, _logo, out_dir, **_kwargs):
        out = Path(out_dir)
        cover = _png(out / f"{platform}-cover.png")
        return StageResult.ready(self.provider, [Artifact.from_file("cover_image", cover, self.provider, "local-composite", "fixture")])


class _Video:
    def __init__(self):
        self.calls = 0

    def __call__(self, _data, output, _project_dir):
        self.calls += 1
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake mp4")
        return StageResult.ready("fake_video", [_artifact("professional_product_demo_video", output)])


class _InspectingVideo(_Video):
    def __init__(self):
        super().__init__()
        self.data = None

    def __call__(self, data, output, project_dir):
        self.data = data
        return super().__call__(data, output, project_dir)


class _Quality:
    def __init__(self):
        self.calls = 0

    def __call__(self, stages, *, target, report_path):
        self.calls += 1
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"target": target, "status": "professional_ready", "cloudUpload": False}), encoding="utf-8")
        return StageResult.ready("fake_quality", [_artifact("quality_report", report)], {"target": target, "status": "professional_ready"})


def _fixture_content(root: Path) -> Path:
    content = root / "content.json"
    content.write_text(json.dumps({"title": "Fixture"}), encoding="utf-8")
    return content


def _guard_job(root: Path, run_id: str, source_url: str, capture_plan_path: str) -> MediaJob:
    content = _fixture_content(root)
    return MediaJob(
        run_id=run_id,
        product_name="Fixture",
        source_url=source_url,
        language="en",
        target_platforms=("youtube",),
        quality_target="draft",
        aspect_ratios=("16:9",),
        duration_range=(20, 60),
        providers={},
        allow_cloud_media=False,
        product_data_path=str(content),
        brand_assets=(),
        generated_content_path=str(content),
        capture_plan_path=capture_plan_path,
    )


def _run_guard(root: Path, job: MediaJob, capture: _Capture, orchestrator_type=MediaOrchestrator):
    return orchestrator_type(
        capture, _Voice(), _Scenes(), _Visuals(), _Video(), _Quality()
    ).run(job, run_dir=root / "run", resume=False)


class MediaOrchestratorTest(unittest.TestCase):
    def test_offline_pipeline_writes_atomic_state_and_resumes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = root / "content.json"
            content.write_text(json.dumps({"title": "Fixture", "narration": "Fixture narration"}), encoding="utf-8")
            logo = _png(root / "logo.png", "#ffffff")
            job = MediaJob(
                run_id="fixture-run",
                product_name="Fixture",
                source_url="https://example.com/product",
                language="en",
                target_platforms=("youtube",),
                quality_target="draft",
                aspect_ratios=("16:9",),
                duration_range=(20, 60),
                providers={},
                allow_cloud_media=False,
                product_data_path=str(content),
                brand_assets=(str(logo),),
                generated_content_path=str(content),
                capture_plan_path="",
            )
            capture, voice, video, quality = _Capture(), _Voice(), _Video(), _Quality()
            orchestrator = MediaOrchestrator(capture, voice, _Scenes(), _Visuals(), video, quality)
            run_dir = root / "run"
            first = orchestrator.run(job, run_dir=run_dir, resume=False)
            self.assertEqual(first.status, "ready")
            self.assertTrue(first.manifest_path.is_file())
            self.assertTrue(first.receipt_path.is_file())
            self.assertEqual(capture.calls, 1)
            resumed = orchestrator.run(job, run_dir=run_dir, resume=True)
            self.assertEqual(resumed.status, "ready")
            self.assertEqual(capture.calls, 1)
            self.assertEqual(video.calls, 1)
            manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["stages"]["capture"]["action"], "skipped")
            self.assertFalse(manifest["cloudUpload"])
            self.assertFalse(manifest["hostedWorker"])

            # A changed artifact invalidates the receipt and reruns capture.
            capture_path = next(run_dir.joinpath("product-captures_产品录屏").glob("shot-0.png"))
            capture_path.write_bytes(capture_path.read_bytes() + b"changed")
            orchestrator.run(job, run_dir=run_dir, resume=True)
            self.assertEqual(capture.calls, 2)

    def test_manifest_publish_pack_and_local_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = root / "content.json"
            content.write_text(json.dumps({"title": "Fixture", "narration": "Fixture narration"}), encoding="utf-8")
            logo = _png(root / "logo.png", "#ffffff")
            pack = root / "publish-pack.json"
            pack.write_text(json.dumps([{"platform": "youtube", "published": True, "metrics": {"views": 1}}]), encoding="utf-8")
            job = MediaJob(
                run_id="fixture-pack",
                product_name="Fixture",
                source_url="https://example.com/product",
                language="en",
                target_platforms=("youtube",),
                quality_target="draft",
                aspect_ratios=("9:16",),
                duration_range=(10, 15),
                providers={},
                allow_cloud_media=False,
                product_data_path=str(content),
                brand_assets=(str(logo),),
                generated_content_path=str(content),
                capture_plan_path="",
            )
            video = _InspectingVideo()
            result = MediaOrchestrator(_Capture(), _Voice(), _Scenes(), _Visuals(), video, _Quality()).run(job, run_dir=root / "run", resume=False, publish_pack_path=pack)
            self.assertEqual(result.status, "ready")
            self.assertEqual(video.data["width"], 1080)
            self.assertEqual(video.data["height"], 1920)
            self.assertEqual(video.data["duration"], 10)
            self.assertTrue((result.run_paths.reports / "media-manifest.json").is_file())
            self.assertTrue((result.run_paths.reports / "media-quality-report.json").is_file())
            updated = json.loads(pack.read_text(encoding="utf-8"))[0]
            self.assertIn("video", updated)
            self.assertIn("mediaQuality", updated)
            self.assertEqual(updated["mediaQuality"]["status"], "professional_ready")
            self.assertTrue(updated["mediaQuality"]["report"].endswith("media-quality-report.json"))
            self.assertTrue(updated["published"])
            self.assertEqual(updated["metrics"], {"views": 1})

    def test_cloud_and_sensitive_provider_results_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = root / "content.json"
            content.write_text(json.dumps({"title": "Fixture"}), encoding="utf-8")
            logo = _png(root / "logo.png")
            base = {
                "runId": "guard",
                "productName": "Fixture",
                "sourceUrl": "https://example.com/product",
                "language": "en",
                "targetPlatforms": ["youtube"],
                "qualityTarget": "draft",
                "aspectRatios": ["16:9"],
                "durationRange": [20, 60],
                "providers": {},
                "productDataPath": str(content),
                "brandAssets": [str(logo)],
                "generatedContentPath": str(content),
                "capturePlanPath": "",
            }
            cloud = dict(base, allowCloudMedia=1)
            blocked = MediaOrchestrator(_Capture(), _Voice(), _Scenes(), _Visuals(), _Video(), _Quality()).run(cloud, run_dir=root / "cloud", resume=False)
            self.assertEqual(blocked.status, "failed")
            self.assertEqual(blocked.stages["capture"].error_code, "job_validation_failed")

            class _LeakyCapture(_Capture):
                def capture(self, plan, out_dir):
                    result = super().capture(plan, out_dir)
                    return StageResult(status="ready", provider="Bearer TOKEN", artifacts=result.artifacts)

            leaky = MediaOrchestrator(_LeakyCapture(), _Voice(), _Scenes(), _Visuals(), _Video(), _Quality()).run(dict(base, allowCloudMedia=False), run_dir=root / "leak", resume=False)
            self.assertEqual(leaky.status, "failed")
            self.assertEqual(leaky.stages["capture"].error_code, "stage_exception")

    def test_cli_rejects_missing_capture_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = root / "content.json"
            content.write_text(json.dumps({"title": "Fixture"}), encoding="utf-8")
            args = professional_cli.parse_args(
                [
                    "--product-url",
                    "https://example.com/product",
                    "--product-name",
                    "Fixture",
                    "--content-json",
                    str(content),
                    "--capture-plan",
                    str(root / "missing-plan.json"),
                ]
            )

            with self.assertRaises(FileNotFoundError):
                professional_cli.build_job(args)

    def test_cli_rejects_non_object_capture_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = root / "content.json"
            content.write_text(json.dumps({"title": "Fixture"}), encoding="utf-8")
            plan = root / "capture-plan.json"
            plan.write_text("[]", encoding="utf-8")
            args = professional_cli.parse_args(
                [
                    "--product-url",
                    "https://example.com/product",
                    "--product-name",
                    "Fixture",
                    "--content-json",
                    str(content),
                    "--capture-plan",
                    str(plan),
                ]
            )

            with self.assertRaisesRegex(ValueError, "capture plan JSON must contain an object"):
                professional_cli.build_job(args)

    def test_orchestrator_rejects_missing_capture_plan_before_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = _Capture()
            job = _guard_job(
                root,
                "missing-plan",
                "https://example.com/product",
                str(root / "missing-plan.json"),
            )

            result = _run_guard(root, job, capture)

            self.assertEqual(result.status, "failed")
            self.assertEqual(result.stages["capture"].error_code, "job_validation_failed")
            self.assertEqual(capture.calls, 0)

    def test_orchestrator_rejects_invalid_capture_sources_before_provider(self):
        cases = (
            ("path", "https://example.com/product", "https://example.com/other-product"),
            ("query", "https://example.com/product?id=1", "https://example.com/product?id=2"),
            ("sensitive", "https://example.com/product", "https://example.com/product?token=do-not-capture"),
            ("fragment", "https://example.com/product", "https://example.com/product#details"),
            ("percent-encoded", "https://example.com/product?%74oken=do-not-capture", "https://example.com/product?%74oken=do-not-capture"),
            ("form-encoded", "https://example.com/product?access+token=do-not-capture", "https://example.com/product?access+token=do-not-capture"),
        )
        for name, source_url, plan_url in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                plan_path = root / "capture-plan.json"
                plan_path.write_text(
                    json.dumps({"sourceUrl": plan_url, "shots": []}),
                    encoding="utf-8",
                )
                capture = _Capture()
                job = _guard_job(root, name, source_url, str(plan_path))

                result = _run_guard(root, job, capture)

                self.assertEqual(result.stages["capture"].error_code, "job_validation_failed")
                self.assertEqual(capture.calls, 0)

    def test_orchestrator_reuses_validated_capture_plan_after_file_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_path = root / "capture-plan.json"
            original_plan = {
                "sourceUrl": "https://example.com/product",
                "shots": [{"id": "original-shot"}],
            }
            plan_path.write_text(json.dumps(original_plan), encoding="utf-8")
            capture = _Capture()
            job = _guard_job(root, "plan-replacement", original_plan["sourceUrl"], str(plan_path))

            class _ReplacingOrchestrator(MediaOrchestrator):
                def _validate_job(self, *args, **kwargs):
                    validated = super()._validate_job(*args, **kwargs)
                    plan_path.write_text(
                        json.dumps(
                            {
                                "sourceUrl": "https://example.com/other-product",
                                "shots": [{"id": "replacement-shot"}],
                            }
                        ),
                        encoding="utf-8",
                    )
                    return validated

            _run_guard(root, job, capture, _ReplacingOrchestrator)

            self.assertEqual(capture.calls, 1)
            self.assertEqual(capture.plan, original_plan)

    def test_orchestrator_rejects_default_capture_fragment_before_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = _Capture()
            job = _guard_job(
                root,
                "default-fragment",
                "https://example.com/product#details",
                "",
            )

            result = _run_guard(root, job, capture)

            self.assertEqual(result.stages["capture"].error_code, "job_validation_failed")
            self.assertEqual(capture.calls, 0)


if __name__ == "__main__":
    unittest.main()

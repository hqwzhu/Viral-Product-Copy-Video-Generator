import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

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

    def capture(self, _plan, out_dir):
        self.calls += 1
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


class _Quality:
    def __init__(self):
        self.calls = 0

    def __call__(self, stages, *, target, report_path):
        self.calls += 1
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"target": target, "cloudUpload": False}), encoding="utf-8")
        return StageResult.ready("fake_quality", [_artifact("quality_report", report)])


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
                capture_plan_path=str(root / "missing-plan.json"),
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


if __name__ == "__main__":
    unittest.main()

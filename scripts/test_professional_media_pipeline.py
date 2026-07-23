import importlib
import contextlib
import functools
import hashlib
import http.server
import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import wave
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest import mock
from urllib.parse import quote, urlsplit

from scripts.media_pipeline.contracts import (
    Artifact,
    MediaJob,
    StageResult,
    atomic_write_json,
    stage_result_is_valid,
)
from scripts.media_pipeline.paths import (
    DEFAULT_OUTPUT_ROOT,
    RUNS_DIR,
    RunPaths,
    find_existing,
    new_run_paths,
    slugify,
)
from scripts.media_pipeline.security import (
    MediaSecurityError,
    cloud_file_allowed,
    redact_secrets,
    validate_capture_shot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "scripts" / "setup_professional_media.py"
PRODUCT_FIXTURE = (
    REPO_ROOT / "references" / "professional-media-fixture" / "product.html"
)


class QuietFixtureHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        path = self.path.partition("?")[0]
        if path == "/status/404":
            self.send_error(404)
            return
        if path == "/status/500":
            self.send_error(500)
            return
        super().do_GET()


@contextlib.contextmanager
def serve_product_fixture():
    handler = functools.partial(
        QuietFixtureHandler, directory=str(PRODUCT_FIXTURE.parent)
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/{PRODUCT_FIXTURE.name}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def load_capture_module(test_case):
    module_name = "scripts.media_pipeline.capture"
    test_case.assertIsNotNone(
        importlib.util.find_spec(module_name),
        "capture module must implement the product capture contract",
    )
    return importlib.import_module(module_name)


def load_setup_module():
    spec = importlib.util.spec_from_file_location("setup_professional_media", SETUP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SETUP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_voiceover_module(test_case):
    module_name = "scripts.media_pipeline.voiceover"
    test_case.assertIsNotNone(
        importlib.util.find_spec(module_name),
        "voiceover module must implement the local narration contract",
    )
    return importlib.import_module(module_name)


def load_scenes_module(test_case):
    module_name = "scripts.media_pipeline.scenes"
    test_case.assertIsNotNone(
        importlib.util.find_spec(module_name),
        "scenes module must implement AI scene and B-roll providers",
    )
    return importlib.import_module(module_name)


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-scene-pixels"


class _FakeComfyHandler(http.server.BaseHTTPRequestHandler):
    state = None

    def log_message(self, _format, *_args):
        pass

    def _json(self, value, status=200):
        payload = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/system_stats":
            self._json(self.state.get("health_payload", {"system": {"os": "fake"}}))
        elif path.startswith("/history/"):
            if self.state.get("malformed_history"):
                self._json({"bad": True})
            elif self.state.get("history_responses"):
                self._json(self.state["history_responses"].pop(0))
            elif self.state.get("history_empty"):
                self._json({})
            else:
                self._json({"fake-prompt-id": {"outputs": {"7": {"images": [{
                    "filename": "scene.png", "subfolder": "", "type": "output"
                }]}}}})
        elif path == "/view":
            self.state["view_query"] = query
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(PNG_BYTES)))
            self.end_headers()
            self.wfile.write(PNG_BYTES)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/prompt":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        self.state["prompt_payload"] = json.loads(self.rfile.read(length))
        self._json({"prompt_id": "fake-prompt-id"})


class _RedirectHandler(http.server.BaseHTTPRequestHandler):
    state = None

    def log_message(self, _format, *_args):
        pass

    def do_GET(self):
        if self.path == "/start":
            self.send_response(302)
            self.send_header("Location", "/dest")
            self.end_headers()
            return
        if self.path == "/dest":
            self.state["destination_calls"] = self.state.get("destination_calls", 0) + 1
            self.state["destination_authorization"] = self.headers.get("Authorization")
            payload = b'{"photos": []}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_error(404)


@contextlib.contextmanager
def serve_fake_comfyui(state=None):
    state = state if state is not None else {}
    _FakeComfyHandler.state = state
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeComfyHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def serve_redirect_target(state=None):
    state = state if state is not None else {}
    _RedirectHandler.state = state
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RedirectHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class SceneProviderTest(unittest.TestCase):
    def setUp(self):
        self.scenes = load_scenes_module(self)
        self.workflow = REPO_ROOT / "references" / "comfyui" / "flux1-schnell-api.json"
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_comfyui_flux_fake_protocol_materializes_pinned_workflow_and_png(self):
        state = {}
        with serve_fake_comfyui(state) as base_url:
            provider = self.scenes.ComfyUiFluxProvider(base_url, self.workflow)
            result = provider.generate(
                "A software workflow dashboard",
                width=1080,
                height=1080,
                seed=7,
                output_dir=self.root,
            )

        self.assertEqual(result.status, "ready", result.to_dict())
        self.assertEqual(len(result.artifacts), 1)
        artifact = result.artifacts[0]
        self.assertEqual(artifact.type, "ai_scene")
        self.assertEqual(artifact.source, "ai-generated")
        self.assertEqual(artifact.license, "Apache-2.0")
        self.assertTrue(artifact.metadata["aiGenerated"])
        target = Path(artifact.path)
        self.assertTrue(target.name.startswith("ai-scene-"))
        self.assertEqual(target.read_bytes(), PNG_BYTES)
        self.assertEqual(artifact.sha256, hashlib.sha256(PNG_BYTES).hexdigest())

        payload = state["prompt_payload"]
        self.assertEqual(set(payload), {"prompt", "client_id"})
        workflow = payload["prompt"]
        nodes = list(workflow.values())
        checkpoint = next(node for node in nodes if node["class_type"] == "CheckpointLoaderSimple")
        self.assertEqual(checkpoint["inputs"]["ckpt_name"], "flux1-schnell-fp8.safetensors")
        sampler = next(node for node in nodes if node["class_type"] == "KSampler")["inputs"]
        self.assertEqual({sampler["steps"], sampler["cfg"], sampler["sampler_name"], sampler["scheduler"]}, {4, 1.0, "euler", "simple"})
        self.assertEqual(sampler["seed"], 7)
        text_nodes = [node for node in nodes if node["class_type"] == "CLIPTextEncode"]
        self.assertIn("A software workflow dashboard", [node["inputs"]["text"] for node in text_nodes])
        latent = next(node for node in nodes if node["class_type"] == "EmptyLatentImage")["inputs"]
        self.assertEqual((latent["width"], latent["height"]), (1080, 1080))
        save = next(node for node in nodes if node["class_type"] == "SaveImage")["inputs"]
        self.assertTrue(save["filename_prefix"].startswith("ai-scene-"))

    def test_comfyui_cloud_gate_and_health_or_malformed_failures(self):
        provider = self.scenes.ComfyUiFluxProvider("https://comfy.example.invalid", self.workflow)
        with mock.patch.object(provider, "health", return_value=True) as health:
            result = provider.generate("blocked", output_dir=self.root)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "cloud_media_not_allowed")
        health.assert_not_called()

        state = {"malformed_history": True}
        with serve_fake_comfyui(state) as base_url:
            result = self.scenes.ComfyUiFluxProvider(base_url, self.workflow).generate(
                "bad history", output_dir=self.root
            )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "comfyui_history_malformed")
        self.assertEqual(result.artifacts, ())

    def test_comfyui_unavailable_is_skipped(self):
        provider = self.scenes.ComfyUiFluxProvider(
            "http://127.0.0.1:1", self.workflow, timeout_seconds=1
        )
        result = provider.generate("unavailable", output_dir=self.root)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "comfyui_unavailable")

    def test_comfyui_empty_history_is_in_progress_then_ready(self):
        state = {
            "history_responses": [
                {},
                {"fake-prompt-id": {"outputs": {"7": {"images": [{
                    "filename": "scene.png", "subfolder": "", "type": "output"
                }]}}}},
            ]
        }
        with serve_fake_comfyui(state) as base_url:
            result = self.scenes.ComfyUiFluxProvider(
                base_url, self.workflow, timeout_seconds=2
            ).generate("async", output_dir=self.root)
        self.assertEqual(result.status, "ready", result.to_dict())

    def test_comfyui_empty_history_times_out_without_prompt_retry(self):
        state = {"history_empty": True}
        with serve_fake_comfyui(state) as base_url:
            result = self.scenes.ComfyUiFluxProvider(
                base_url, self.workflow, timeout_seconds=0.2
            ).generate("still running", output_dir=self.root)
        self.assertEqual(result.status, "failed", result.to_dict())
        self.assertEqual(result.error_code, "comfyui_timeout")
        self.assertEqual(result.artifacts, ())

    def test_comfyui_bad_health_skips_before_prompt(self):
        for health_payload in ({}, {"error": "down"}, {"system": {}}):
            with self.subTest(health_payload=health_payload):
                state = {"health_payload": health_payload}
                with serve_fake_comfyui(state) as base_url:
                    result = self.scenes.ComfyUiFluxProvider(
                        base_url, self.workflow, timeout_seconds=1
                    ).generate("bad health", output_dir=self.root)
                self.assertEqual(result.status, "skipped", result.to_dict())
                self.assertEqual(result.error_code, "comfyui_unavailable")
                self.assertNotIn("prompt_payload", state)

    def test_pexels_unconfigured_skips_without_secret(self):
        result = self.scenes.PexelsProvider(api_key="").search(
            "software workflow", self.root, 2
        )
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "pexels_not_configured")
        self.assertNotIn("api_key", json.dumps(result.to_dict(), sort_keys=True))

    def test_pexels_fake_search_downloads_only_landscape_and_redacts_key(self):
        class Response:
            def __init__(self, body):
                self.body = body

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return self.body

        photos = {
            "photos": [
                {
                    "width": 1200,
                    "height": 800,
                    "photographer": "Ada",
                    "url": "https://www.pexels.com/photo/1/",
                    "src": {"original": "https://images.pexels.com/one.jpg"},
                },
                {
                    "width": 800,
                    "height": 800,
                    "photographer": "Square",
                    "url": "https://www.pexels.com/photo/2/",
                    "src": {"original": "https://images.example/two.jpg"},
                },
            ]
        }
        calls = []

        def fake_urlopen(req, timeout):
            calls.append((req, timeout))
            if len(calls) == 1:
                self.assertEqual(req.get_header("Authorization"), "SECRET-PEXELS")
                self.assertIn("api.pexels.com/v1/search", req.full_url)
                return Response(json.dumps(photos).encode("utf-8"))
            return Response(b"JPEG-BYTES")

        with mock.patch.object(self.scenes, "_open_no_redirect", side_effect=fake_urlopen):
            result = self.scenes.PexelsProvider("SECRET-PEXELS").search(
                "software workflow", self.root, 2
            )
        self.assertEqual(result.status, "ready", result.to_dict())
        self.assertEqual(len(result.artifacts), 1)
        artifact = result.artifacts[0]
        self.assertEqual(artifact.type, "b_roll_image")
        self.assertEqual(artifact.metadata["orientation"], "landscape")
        self.assertEqual(Path(artifact.path).read_bytes(), b"JPEG-BYTES")
        serialized = json.dumps(result.to_dict(), sort_keys=True)
        self.assertNotIn("SECRET-PEXELS", serialized)

    def test_pexels_rejects_non_https_or_untrusted_image_urls_before_download(self):
        class Response:
            def __init__(self, body):
                self.body = body

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return self.body

        for original_url in (
            "file:///secret.txt",
            "http://images.pexels.com/unsafe.jpg",
            "https://127.0.0.1/unsafe.jpg",
            "https://evil.example/unsafe.jpg",
            "https://images.example/unsafe.jpg",
            "https://evil.pexels.com/unsafe.jpg",
        ):
            with self.subTest(original_url=original_url):
                calls = []
                payload = {
                    "photos": [{
                        "width": 1200,
                        "height": 800,
                        "photographer": "Attacker",
                        "url": "https://www.pexels.com/photo/unsafe/",
                        "src": {"original": original_url},
                    }]
                }

                def fake_urlopen(req, timeout):
                    calls.append(req)
                    return Response(json.dumps(payload).encode("utf-8"))

                with mock.patch.object(
                    self.scenes, "_open_no_redirect", side_effect=fake_urlopen
                ):
                    result = self.scenes.PexelsProvider("SECRET-PEXELS").search(
                        "unsafe", self.root, 1
                    )
                self.assertEqual(result.status, "failed", result.to_dict())
                self.assertEqual(result.error_code, "pexels_request_failed")
                self.assertEqual(len(calls), 1)

    def test_redirects_are_denied_without_forwarding_authorization(self):
        state = {}
        with serve_redirect_target(state) as base_url:
            with self.assertRaises(self.scenes._RedirectDenied):
                self.scenes._request_bytes(
                    f"{base_url}/start",
                    timeout=1,
                    headers={"Authorization": "SECRET-PEXELS"},
                )
        self.assertEqual(state.get("destination_calls", 0), 0)
        self.assertIsNone(state.get("destination_authorization"))

    def test_pexels_api_redirect_fails_without_leaking_authorization(self):
        state = {}
        with serve_redirect_target(state) as base_url:
            with mock.patch.object(
                self.scenes, "_endpoint", return_value=f"{base_url}/start"
            ):
                result = self.scenes.PexelsProvider("SECRET-PEXELS").search(
                    "redirect", self.root, 1
                )
        self.assertEqual(result.status, "failed", result.to_dict())
        self.assertEqual(result.error_code, "pexels_redirect_denied")
        self.assertEqual(state.get("destination_calls", 0), 0)

    def test_pexels_image_redirect_fails_without_ready_artifact(self):
        class Response:
            def __init__(self, body):
                self.body = body

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return self.body

        payload = {
            "photos": [{
                "width": 1200,
                "height": 800,
                "photographer": "Ada",
                "url": "https://www.pexels.com/photo/redirect/",
                "src": {"original": "https://images.pexels.com/start.jpg"},
            }]
        }
        calls = []

        def fake_open(req, timeout):
            calls.append(req)
            if len(calls) == 1:
                return Response(json.dumps(payload).encode("utf-8"))
            raise self.scenes._RedirectDenied

        with mock.patch.object(self.scenes, "_open_no_redirect", side_effect=fake_open):
            result = self.scenes.PexelsProvider("SECRET-PEXELS").search(
                "redirect", self.root, 1
            )
        self.assertEqual(result.status, "failed", result.to_dict())
        self.assertEqual(result.error_code, "pexels_redirect_denied")
        self.assertEqual(result.artifacts, ())


class RuntimeSetupTest(unittest.TestCase):
    def setUp(self):
        self.setup = load_setup_module()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_runtime_plan_is_pinned_and_never_contains_secrets(self):
        plan = self.setup.build_install_plan(
            Path("C:/runtime"), with_comfyui=True, with_musetalk=False
        )
        serialized = json.dumps(plan, sort_keys=True)

        self.assertIn("hyperframes@0.7.68", serialized)
        self.assertIn(
            "f6d30bce9a862d56d9184dd65341621a8905ea3e", serialized
        )
        self.assertIn(
            "7d679837b018bfeb28eca55734b335efcd0e7100", serialized
        )
        self.assertIn(
            "7d679837b018bfeb28eca55734b335efcd0e7100/flux1-schnell-fp8.safetensors?download=true",
            serialized,
        )
        self.assertNotIn("HF_TOKEN", serialized)
        self.assertNotIn("apiKey", serialized)

    def test_manifest_pins_size_and_sha256_for_every_model_asset(self):
        manifest = self.setup._manifest()
        assets = [*manifest["kokoro"]["model"]["files"], manifest["flux"]]

        for asset in assets:
            with self.subTest(filename=asset["filename"]):
                self.assertIsInstance(asset.get("sizeBytes"), int)
                self.assertGreater(asset["sizeBytes"], 0)
                self.assertRegex(asset.get("sha256", ""), r"^[0-9a-f]{64}$")

    def test_same_size_corrupt_file_fails_integrity(self):
        expected = b"trusted-model"
        corrupt = b"damaged-model"
        self.assertEqual(len(expected), len(corrupt))
        path = self.root / "same-size-model.bin"
        path.write_bytes(corrupt)

        self.assertFalse(
            self.setup._matches_integrity(
                path, len(expected), hashlib.sha256(expected).hexdigest()
            )
        )

    def test_command_resolves_windows_cmd_executable(self):
        npm_cmd = str(self.root / "npm.CMD")
        action = {
            "id": "install-node",
            "scope": "core",
            "kind": "command",
            "arguments": ["npm", "ci"],
        }

        with mock.patch.object(self.setup.shutil, "which", return_value=npm_cmd), mock.patch.object(
            self.setup.subprocess, "run"
        ) as run:
            self.setup._execute_action(action)

        self.assertEqual(run.call_args.args[0], [npm_cmd, "ci"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_disk_guard_rejects_before_any_mutation(self):
        runtime_root = self.root / "does-not-exist" / "runtime"
        low_space = SimpleNamespace(free=self.setup.MINIMUM_COMFYUI_FREE_BYTES - 1)

        with mock.patch.object(self.setup.shutil, "disk_usage", return_value=low_space), mock.patch.object(
            self.setup, "build_install_plan"
        ) as build_plan, mock.patch.object(self.setup, "_execute_scope") as execute_scope:
            with self.assertRaisesRegex(RuntimeError, "25 GiB"):
                self.setup.install_comfyui(runtime_root)

        self.assertFalse(runtime_root.exists())
        build_plan.assert_not_called()
        execute_scope.assert_not_called()

    def test_dry_run_never_executes_actions(self):
        stdout = io.StringIO()
        argv = [
            "setup_professional_media.py",
            "--dry-run",
            "--with-comfyui",
            "--runtime-root",
            str(self.root / "runtime"),
        ]

        with mock.patch.object(sys, "argv", argv), mock.patch.object(
            self.setup, "_execute_action"
        ) as execute_action, contextlib.redirect_stdout(stdout):
            result = self.setup.main()

        self.assertEqual(result, 0)
        execute_action.assert_not_called()
        self.assertTrue(json.loads(stdout.getvalue())["features"]["comfyui"])

    def test_command_failure_propagates(self):
        failure = subprocess.CalledProcessError(9, ["tool", "arg"])
        action = {
            "id": "failing-command",
            "scope": "core",
            "kind": "command",
            "arguments": ["tool", "arg"],
        }

        with mock.patch.object(
            self.setup.shutil, "which", return_value=str(self.root / "tool.exe")
        ), mock.patch.object(self.setup.subprocess, "run", side_effect=failure):
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                self.setup._execute_action(action)

        self.assertIs(raised.exception, failure)

    def test_venv_action_can_run_twice(self):
        runtime_root = self.root / "runtime"
        action = next(
            action
            for action in self.setup.build_install_plan(runtime_root)["actions"]
            if action["id"] == "create-core-venv"
        )

        self.setup._execute_action(action)
        self.setup._execute_action(action)

        python = self.setup._venv_python(runtime_root / "core" / ".venv")
        version = subprocess.run(
            [str(python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(version, "3.12")

    def test_venv_action_recovers_partial_first_attempt(self):
        runtime_root = self.root / "runtime"
        action = next(
            action
            for action in self.setup.build_install_plan(runtime_root)["actions"]
            if action["id"] == "create-core-venv"
        )
        venv = runtime_root / "core" / ".venv"
        venv.mkdir(parents=True)
        (venv / "interrupted.part").write_text("partial", encoding="utf-8")

        self.setup._execute_action(action)

        python = self.setup._venv_python(venv)
        version = subprocess.run(
            [str(python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(version, "3.12")

    def test_venv_action_repairs_missing_pyvenv_cfg(self):
        runtime_root = self.root / "runtime"
        action = next(
            action
            for action in self.setup.build_install_plan(runtime_root)["actions"]
            if action["id"] == "create-core-venv"
        )
        venv = runtime_root / "core" / ".venv"
        self.setup._execute_action(action)
        (venv / "pyvenv.cfg").unlink()

        self.setup._execute_action(action)

        self.assertTrue((venv / "pyvenv.cfg").is_file())
        self.assertEqual(
            self.setup._venv_runtime_version(self.setup._venv_python(venv)), "3.12"
        )

    def test_corrupt_venv_python_fails_closed_without_deleting_files(self):
        runtime_root = self.root / "runtime"
        action = next(
            action
            for action in self.setup.build_install_plan(runtime_root)["actions"]
            if action["id"] == "create-core-venv"
        )
        venv = runtime_root / "core" / ".venv"
        python = self.setup._venv_python(venv)
        python.parent.mkdir(parents=True)
        python.write_bytes(b"not an executable")
        (venv / "pyvenv.cfg").write_text("version = 3.12.9\n", encoding="utf-8")
        sentinel = venv / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "validate existing venv Python"):
            self.setup._execute_action(action)

        self.assertEqual(python.read_bytes(), b"not an executable")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_partial_download_is_cleaned_after_bounded_retries(self):
        destination = self.root / "models" / "model.bin"

        class BrokenResponse:
            def __init__(self):
                self.reads = 0

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _size=-1):
                self.reads += 1
                if self.reads == 1:
                    return b"partial"
                raise TimeoutError("interrupted")

        with mock.patch.object(
            self.setup.urllib.request,
            "urlopen",
            side_effect=lambda *_args, **_kwargs: BrokenResponse(),
        ) as urlopen, mock.patch.object(self.setup.time, "sleep"):
            with self.assertRaises(TimeoutError):
                self.setup._download_public_file(
                    "https://example.invalid/model",
                    destination,
                    expected_size=len(b"complete"),
                    expected_sha256=hashlib.sha256(b"complete").hexdigest(),
                )

        self.assertEqual(urlopen.call_count, self.setup.DOWNLOAD_ATTEMPTS)
        self.assertTrue(
            all(call.kwargs["timeout"] == self.setup.DOWNLOAD_TIMEOUT_SECONDS for call in urlopen.call_args_list)
        )
        self.assertFalse(destination.exists())
        self.assertFalse(destination.with_name("model.bin.part").exists())

    def test_download_without_fixed_or_upstream_integrity_fails_closed(self):
        destination = self.root / "untrusted-model.bin"

        with mock.patch.object(
            self.setup.urllib.request,
            "urlopen",
            side_effect=lambda *_args, **_kwargs: io.BytesIO(b"arbitrary content"),
        ), mock.patch.object(self.setup.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "trusted integrity"):
                self.setup._download_public_file(
                    "https://example.invalid/model", destination
                )

        self.assertFalse(destination.exists())

    def test_corrupt_existing_file_is_replaced_and_verified(self):
        destination = self.root / "model.bin"
        destination.write_bytes(b"corrupt")
        expected = b"verified model"
        expected_sha256 = hashlib.sha256(expected).hexdigest()

        with mock.patch.object(
            self.setup.urllib.request, "urlopen", return_value=io.BytesIO(expected)
        ) as urlopen:
            self.setup._download_public_file(
                "https://example.invalid/model",
                destination,
                expected_size=len(expected),
                expected_sha256=expected_sha256,
            )

        urlopen.assert_called_once()
        self.assertEqual(destination.read_bytes(), expected)

    def test_download_with_wrong_digest_is_never_installed(self):
        destination = self.root / "model.bin"
        downloaded = b"damaged model"

        with mock.patch.object(
            self.setup.urllib.request,
            "urlopen",
            side_effect=lambda *_args, **_kwargs: io.BytesIO(downloaded),
        ), mock.patch.object(self.setup.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                self.setup._download_public_file(
                    "https://example.invalid/model",
                    destination,
                    expected_size=len(downloaded),
                    expected_sha256=hashlib.sha256(b"expected model").hexdigest(),
                )

        self.assertFalse(destination.exists())
        self.assertFalse(destination.with_name("model.bin.part").exists())

    def test_download_uses_upstream_linked_integrity_when_available(self):
        destination = self.root / "model.bin"
        damaged = b"same length bad"
        expected_digest = hashlib.sha256(b"same length ok!").hexdigest()

        class LinkedResponse(io.BytesIO):
            headers = {
                "X-Linked-Size": str(len(damaged)),
                "X-Linked-ETag": f'"{expected_digest}"',
            }

        with mock.patch.object(
            self.setup.urllib.request,
            "urlopen",
            side_effect=lambda *_args, **_kwargs: LinkedResponse(damaged),
        ), mock.patch.object(self.setup.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                self.setup._download_public_file(
                    "https://example.invalid/model", destination
                )

        self.assertFalse(destination.exists())

    def test_verified_download_writes_matching_receipt_atomically(self):
        destination = self.root / "model.bin"
        receipt = self.root / "receipts" / "model.json"
        content = b"verified download"
        digest = hashlib.sha256(content).hexdigest()

        class LinkedResponse(io.BytesIO):
            headers = {
                "X-Linked-Size": str(len(content)),
                "X-Linked-ETag": f'"{digest}"',
            }

        action = {
            "id": "download-model",
            "scope": "comfyui",
            "kind": "download",
            "arguments": [],
            "url": "https://example.invalid/model",
            "destination": str(destination),
            "receipt": str(receipt),
            "revision": "pinned-revision",
        }
        with mock.patch.object(
            self.setup.urllib.request,
            "urlopen",
            return_value=LinkedResponse(content),
        ):
            self.setup._execute_action(action)

        saved = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(saved["revision"], "pinned-revision")
        self.assertEqual(saved["sizeBytes"], len(content))
        self.assertEqual(saved["sha256"], digest)
        self.assertFalse(receipt.with_name("model.json.part").exists())

    def _make_git_source(self) -> tuple[Path, str, str]:
        source = self.root / "source"
        source.mkdir()
        subprocess.run(["git", "init", "--quiet", str(source)], check=True)
        first_file = source / "version.txt"
        first_file.write_text("first", encoding="utf-8")
        subprocess.run(["git", "-C", str(source), "add", "version.txt"], check=True)
        commit = [
            "git",
            "-c",
            "user.name=Runtime Test",
            "-c",
            "user.email=runtime-test@example.invalid",
            "-C",
            str(source),
            "commit",
            "--quiet",
            "-m",
        ]
        subprocess.run([*commit, "first"], check=True)
        first = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        first_file.write_text("second", encoding="utf-8")
        subprocess.run(["git", "-C", str(source), "add", "version.txt"], check=True)
        subprocess.run([*commit, "second"], check=True)
        second = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return source, first, second

    def test_pinned_checkout_recovers_wrong_revision(self):
        source, expected, wrong = self._make_git_source()
        checkout = self.root / "checkout"
        subprocess.run(["git", "clone", "--quiet", str(source), str(checkout)], check=True)
        self.assertEqual(self.setup._git_head(checkout), wrong)

        self.setup._ensure_git_checkout(str(source), checkout, expected)

        self.assertEqual(self.setup._git_head(checkout), expected)

    def test_wrong_origin_repo_is_not_mutated(self):
        source, expected, wrong = self._make_git_source()
        checkout = self.root / "checkout"
        subprocess.run(["git", "clone", "--quiet", str(source), str(checkout)], check=True)
        sentinel = checkout / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "not managed"):
            self.setup._ensure_git_checkout(
                str(self.root / "different-origin"), checkout, expected
            )

        self.assertEqual(self.setup._git_head(checkout), wrong)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_parent_repository_is_not_mutated_through_child_destination(self):
        source, expected, parent_head = self._make_git_source()
        parent = self.root / "parent-checkout"
        subprocess.run(["git", "clone", "--quiet", str(source), str(parent)], check=True)
        child = parent / "runtime-child"
        child.mkdir()
        sentinel = child / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")
        tracked = parent / "version.txt"
        self.assertEqual(tracked.read_text(encoding="utf-8"), "second")

        with self.assertRaisesRegex(RuntimeError, "top level"):
            self.setup._ensure_git_checkout(str(source), child, expected)

        self.assertEqual(self.setup._git_head(parent), parent_head)
        self.assertEqual(tracked.read_text(encoding="utf-8"), "second")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_pinned_checkout_clones_clean_destination(self):
        source, expected, _wrong = self._make_git_source()
        checkout = self.root / "checkout"

        self.setup._ensure_git_checkout(str(source), checkout, expected)

        self.assertEqual(self.setup._git_head(checkout), expected)
        self.assertEqual((checkout / "version.txt").read_text(encoding="utf-8"), "first")

    def test_missing_git_preserves_existing_destination(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        sentinel = checkout / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")

        with mock.patch.object(self.setup.shutil, "which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                self.setup._ensure_git_checkout("unused", checkout, "pinned")

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_non_repository_destination_preserves_user_files(self):
        source, expected, _wrong = self._make_git_source()
        checkout = self.root / "checkout"
        checkout.mkdir()
        sentinel = checkout / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "inspect existing Git checkout"):
            self.setup._ensure_git_checkout(str(source), checkout, expected)

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_corrupt_git_directory_is_never_deleted(self):
        source, expected, _wrong = self._make_git_source()
        checkout = self.root / "checkout"
        (checkout / ".git").mkdir(parents=True)
        sentinel = checkout / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "inspect existing Git checkout"):
            self.setup._ensure_git_checkout(str(source), checkout, expected)

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_rev_parse_failure_preserves_git_file_and_user_data(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        (checkout / ".git").write_text("gitdir: missing", encoding="utf-8")
        sentinel = checkout / "USER_DATA.txt"
        sentinel.write_text("keep", encoding="utf-8")
        failure = subprocess.CalledProcessError(128, ["git", "rev-parse"])

        with mock.patch.object(
            self.setup, "_resolve_executable", return_value=str(self.root / "git.exe")
        ), mock.patch.object(self.setup.subprocess, "run", side_effect=failure):
            with self.assertRaisesRegex(RuntimeError, "inspect existing Git checkout"):
                self.setup._ensure_git_checkout("unused", checkout, "pinned")

        self.assertTrue((checkout / ".git").is_file())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_check_runtime_rejects_unpinned_comfyui_checkout(self):
        source, _first, _second = self._make_git_source()
        comfyui = self.root / "runtime" / "ComfyUI"
        subprocess.run(["git", "clone", "--quiet", str(source), str(comfyui)], check=True)

        status = self.setup.check_runtime(self.root / "runtime")

        self.assertFalse(status["installed"]["comfyui"])

    def test_receipt_size_and_sha256_are_verified_by_runtime_check(self):
        runtime_root = self.root / "runtime"
        manifest = self.setup._manifest()
        model = (
            runtime_root
            / "ComfyUI"
            / "models"
            / "checkpoints"
            / manifest["flux"]["filename"]
        )
        model.parent.mkdir(parents=True)
        model.write_bytes(b"complete model")
        receipt = runtime_root / "receipts" / "comfyui-flux.json"
        action = {
            "id": "write-receipt",
            "scope": "comfyui",
            "kind": "receipt",
            "arguments": [],
            "source": str(model),
            "destination": str(receipt),
            "revision": manifest["flux"]["revision"],
        }

        self.setup._execute_action(action)

        saved = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(saved["sizeBytes"], len(b"complete model"))
        self.assertEqual(saved["sha256"], hashlib.sha256(b"complete model").hexdigest())
        manifest["flux"]["sizeBytes"] = len(b"complete model")
        manifest["flux"]["sha256"] = hashlib.sha256(b"complete model").hexdigest()
        with mock.patch.object(self.setup, "_manifest", return_value=manifest):
            self.assertTrue(self.setup.check_runtime(runtime_root)["installed"]["flux"])

            model.write_bytes(b"corrupt")
            self.assertFalse(self.setup.check_runtime(runtime_root)["installed"]["flux"])

    def test_receipt_refuses_model_that_misses_expected_integrity(self):
        model = self.root / "model.bin"
        model.write_bytes(b"damaged")
        receipt = self.root / "receipt.json"
        action = {
            "id": "write-receipt",
            "scope": "comfyui",
            "kind": "receipt",
            "arguments": [],
            "source": str(model),
            "destination": str(receipt),
            "revision": "pinned-revision",
            "expectedSizeBytes": len(b"expected"),
            "expectedSha256": hashlib.sha256(b"expected").hexdigest(),
        }

        with self.assertRaisesRegex(RuntimeError, "integrity"):
            self.setup._execute_action(action)

        self.assertFalse(receipt.exists())

    def test_runtime_check_rejects_receipt_without_size_and_sha256(self):
        runtime_root = self.root / "runtime"
        manifest = self.setup._manifest()
        model = (
            runtime_root
            / "ComfyUI"
            / "models"
            / "checkpoints"
            / manifest["flux"]["filename"]
        )
        model.parent.mkdir(parents=True)
        model.write_bytes(b"unverified")
        receipt = runtime_root / "receipts" / "comfyui-flux.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text(
            json.dumps(
                {
                    "revision": manifest["flux"]["revision"],
                    "filename": manifest["flux"]["filename"],
                }
            ),
            encoding="utf-8",
        )

        self.assertFalse(self.setup.check_runtime(runtime_root)["installed"]["flux"])


class VoiceoverTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _write_test_wav(path, seconds=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16_000)
            output.writeframes(b"\x00\x00" * 16_000 * seconds)

    def test_voice_selection_uses_exact_language_map_and_english_default(self):
        voiceover = load_voiceover_module(self)

        self.assertEqual(voiceover.voice_for_language("zh-CN"), ("zf_xiaobei", "zh"))
        self.assertEqual(voiceover.voice_for_language("en"), ("af_heart", "en-us"))
        self.assertEqual(voiceover.voice_for_language("unknown"), ("af_heart", "en-us"))

    def test_actual_kokoro_generates_verified_chinese_wav_and_segments(self):
        voiceover = load_voiceover_module(self)
        if not voiceover.professional_tts_available():
            self.skipTest("pinned professional TTS runtime is not installed")

        result = voiceover.KokoroVoiceoverProvider().generate(
            "把产品网页变成推广素材。", "zh-CN", self.root
        )

        self.assertEqual(result.status, "ready", result)
        self.assertEqual(result.provider, "kokoro_onnx")
        artifact = result.artifacts[0]
        wav_path = Path(artifact.path)
        self.assertEqual(artifact.type, "voiceover_audio")
        self.assertEqual(artifact.provider, "kokoro_onnx")
        self.assertEqual(artifact.source, "generated")
        self.assertEqual(artifact.license, "Apache-2.0")
        self.assertTrue(wav_path.is_file())
        self.assertGreater(wav_path.stat().st_size, 4096)
        header = wav_path.read_bytes()[:12]
        self.assertEqual(header[:4], b"RIFF")
        self.assertEqual(header[8:12], b"WAVE")

        duration = result.diagnostics["durationSeconds"]
        segments = result.diagnostics["segments"]
        self.assertGreater(duration, 0)
        self.assertTrue(segments)
        self.assertAlmostEqual(segments[0]["start"], 0.0)
        for previous, current in zip(segments, segments[1:]):
            self.assertAlmostEqual(previous["end"], current["start"], places=6)
        self.assertAlmostEqual(segments[-1]["end"], duration, places=6)
        self.assertEqual(result.diagnostics["voice"], "zf_xiaobei")
        self.assertEqual(result.diagnostics["language"], "zh-CN")
        self.assertEqual(result.diagnostics["lang"], "zh")
        self.assertEqual(artifact.metadata["voice"], "zf_xiaobei")
        self.assertEqual(artifact.metadata["language"], "zh-CN")
        self.assertEqual(artifact.metadata["lang"], "zh")

    def test_english_generation_passes_selected_voice_and_lang_to_runtime(self):
        voiceover = load_voiceover_module(self)
        runtime_root = self.root / "runtime"
        captured = {}

        def synthesize(root, text, voice, lang, destination):
            captured.update(root=root, text=text, voice=voice, lang=lang)
            self._write_test_wav(destination)

        with mock.patch.object(
            voiceover, "professional_tts_available", return_value=True
        ), mock.patch.object(
            voiceover, "_synthesize_kokoro", side_effect=synthesize
        ), mock.patch.object(voiceover, "_audio_duration", return_value=1.0):
            result = voiceover.KokoroVoiceoverProvider(runtime_root).generate(
                "Turn a product page into promotional media.", "en", self.root
            )

        self.assertEqual(result.status, "ready")
        self.assertEqual(captured["root"], runtime_root)
        self.assertEqual(captured["voice"], "af_heart")
        self.assertEqual(captured["lang"], "en-us")
        self.assertEqual(result.artifacts[0].metadata["voice"], "af_heart")

    def test_sapi_success_is_degraded_review_audio(self):
        voiceover = load_voiceover_module(self)

        with mock.patch.object(
            voiceover,
            "_synthesize_windows_sapi",
            side_effect=lambda _text, destination: self._write_test_wav(destination),
        ), mock.patch.object(voiceover, "_audio_duration", return_value=1.0):
            result = voiceover.SapiVoiceoverProvider().generate(
                "Review voice only.", "en", self.root
            )

        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.provider, "windows_sapi")
        self.assertEqual(result.warnings, ("review_voice_only",))
        artifact = result.artifacts[0]
        self.assertEqual(artifact.type, "voiceover_audio")
        self.assertEqual(artifact.provider, "windows_sapi")
        self.assertEqual(artifact.license, "")
        self.assertGreater(Path(artifact.path).stat().st_size, 4096)

    def test_sapi_missing_powershell_fails_explicitly(self):
        voiceover = load_voiceover_module(self)

        with mock.patch.object(voiceover.shutil, "which", return_value=None):
            result = voiceover.SapiVoiceoverProvider().generate(
                "Review voice only.", "en", self.root
            )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.provider, "windows_sapi")
        self.assertEqual(result.error_code, "sapi_unavailable")
        self.assertFalse(result.artifacts)

    def test_sapi_passes_text_over_stdin_instead_of_command_arguments(self):
        voiceover = load_voiceover_module(self)
        dangerous_text = "'); Remove-Item -Recurse C:\\\\; #"

        with mock.patch.object(
            voiceover.shutil, "which", return_value="C:/Windows/powershell.exe"
        ), mock.patch.object(voiceover.subprocess, "run") as run:
            voiceover._synthesize_windows_sapi(
                dangerous_text, self.root / "review.wav"
            )

        arguments = run.call_args.args[0]
        self.assertNotIn(dangerous_text, arguments)
        self.assertEqual(run.call_args.kwargs["input"], dangerous_text)
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_corrupt_pinned_runtime_is_unavailable_and_never_falls_back(self):
        voiceover = load_voiceover_module(self)
        runtime_root = self.root / "runtime"
        model_root = runtime_root / "models" / "kokoro"
        model_root.mkdir(parents=True)
        (model_root / "kokoro-v1.0.onnx").write_bytes(b"wrong model")
        (model_root / "voices-v1.0.bin").write_bytes(b"wrong voices")
        (self.root / "kokoro-v1.0.onnx").write_bytes(b"global-looking model")
        (self.root / "voices-v1.0.bin").write_bytes(b"global-looking voices")

        self.assertFalse(voiceover.professional_tts_available(runtime_root))
        result = voiceover.KokoroVoiceoverProvider(runtime_root).generate(
            "Must not use global files.", "en", self.root / "output"
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "tts_runtime_unavailable")
        self.assertFalse(result.artifacts)

    def test_empty_text_fails_without_claiming_ready_audio(self):
        voiceover = load_voiceover_module(self)

        result = voiceover.KokoroVoiceoverProvider(self.root).generate(
            "   ", "en", self.root / "output"
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "empty_voiceover_text")
        self.assertFalse(result.artifacts)

    def test_nonfinite_ffprobe_duration_never_returns_ready(self):
        voiceover = load_voiceover_module(self)

        for stdout in ("nan\n", "inf\n"):
            with self.subTest(stdout=stdout.strip()), mock.patch.object(
                voiceover, "professional_tts_available", return_value=True
            ), mock.patch.object(
                voiceover,
                "_synthesize_kokoro",
                side_effect=lambda _root, _text, _voice, _lang, destination: self._write_test_wav(
                    destination
                ),
            ), mock.patch.object(
                voiceover.shutil, "which", return_value="ffprobe.exe"
            ), mock.patch.object(
                voiceover.subprocess,
                "run",
                return_value=SimpleNamespace(stdout=stdout),
            ):
                result = voiceover.KokoroVoiceoverProvider(self.root).generate(
                    "Speak this sentence.", "en", self.root / stdout.strip()
                )

            self.assertEqual(result.status, "failed")
            self.assertFalse(result.artifacts)

    def test_ffprobe_duration_call_has_a_bounded_timeout(self):
        voiceover = load_voiceover_module(self)
        audio = self.root / "audio.wav"
        audio.write_bytes(b"RIFF" + b"\x00" * 40 + b"WAVE")

        with mock.patch.object(
            voiceover.shutil, "which", return_value="ffprobe.exe"
        ), mock.patch.object(
            voiceover.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="1.25\n"),
        ) as run:
            self.assertEqual(voiceover._audio_duration(audio), 1.25)

        self.assertEqual(run.call_args.kwargs.get("timeout"), 30)

    def test_invalid_segments_never_return_ready(self):
        voiceover = load_voiceover_module(self)
        invalid_segments = [
            [{"text": "one", "start": 0.0, "end": 0.4}, {"text": "two", "start": 0.5, "end": 1.0}],
            [{"text": "one", "start": -0.1, "end": 0.4}],
            [{"text": "one", "start": 0.0, "end": 1.1}],
        ]

        for segments in invalid_segments:
            with self.subTest(segments=segments), mock.patch.object(
                voiceover, "professional_tts_available", return_value=True
            ), mock.patch.object(
                voiceover,
                "_synthesize_kokoro",
                side_effect=lambda _root, _text, _voice, _lang, destination: self._write_test_wav(
                    destination
                ),
            ), mock.patch.object(
                voiceover, "_audio_duration", return_value=1.0
            ), mock.patch.object(
                voiceover, "_sentence_segments", return_value=segments
            ):
                result = voiceover.KokoroVoiceoverProvider(self.root).generate(
                    "Speak this sentence.", "en", self.root / "invalid-segments"
                )

            self.assertEqual(result.status, "failed")
            self.assertFalse(result.artifacts)
            self.assertFalse(
                (self.root / "invalid-segments" / "voiceover.wav").exists()
            )

    def test_english_and_chinese_punctuation_only_text_never_returns_ready(self):
        voiceover = load_voiceover_module(self)

        for text in ("!!!", "，！？"):
            with self.subTest(text=text), mock.patch.object(
                voiceover, "professional_tts_available", return_value=True
            ), mock.patch.object(
                voiceover,
                "_synthesize_kokoro",
                side_effect=lambda _root, _text, _voice, _lang, destination: self._write_test_wav(
                    destination
                ),
            ), mock.patch.object(voiceover, "_audio_duration", return_value=1.0):
                result = voiceover.KokoroVoiceoverProvider(self.root).generate(
                    text, "en", self.root / "punctuation"
                )

            self.assertEqual(result.status, "failed")
            self.assertFalse(result.artifacts)

    def test_sapi_punctuation_only_text_never_returns_degraded_ready(self):
        voiceover = load_voiceover_module(self)

        with mock.patch.object(
            voiceover.shutil, "which", return_value="powershell.exe"
        ), mock.patch.object(
            voiceover,
            "_synthesize_windows_sapi",
            side_effect=lambda _text, destination: self._write_test_wav(destination),
        ), mock.patch.object(voiceover, "_audio_duration", return_value=1.0):
            result = voiceover.SapiVoiceoverProvider().generate(
                "!!!", "en", self.root / "sapi-punctuation"
            )

        self.assertEqual(result.status, "failed")
        self.assertFalse(result.artifacts)


class MediaSecurityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_clear_stage_output_removes_windows_junction_without_following_it(self):
        if sys.platform != "win32":
            self.skipTest("Windows junction semantics are only available on Windows")

        from scripts.media_pipeline.orchestrator import MediaOrchestrator

        paths = new_run_paths(
            self.root, "ENHE", now="20260723-120000"
        ).create()
        external = self.root / "external-output"
        external.mkdir()
        sentinel = external / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")
        junction = paths.videos / "external-link"
        created = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(external)],
            capture_output=True,
            check=False,
        )
        if created.returncode != 0:
            self.skipTest(f"mklink /J unavailable: {created.stderr or created.stdout}")

        MediaOrchestrator()._clear_stage_output("video", paths)

        self.assertFalse(junction.exists())
        self.assertTrue(sentinel.exists())

    def test_colon_form_secrets_are_rejected_and_redacted_everywhere(self):
        orchestrator = importlib.import_module("scripts.media_pipeline.orchestrator")
        quality = importlib.import_module("scripts.media_pipeline.quality")
        secret = "TOPSECRET123"
        artifact_path = self.root / "capture.png"
        artifact_path.write_bytes(PNG_BYTES)
        artifact = replace(
            Artifact.from_file(
                "product_capture_image",
                artifact_path,
                "local",
                f"api_key: {secret}",
            ),
            metadata={"viewport": [1, 1], "cloudUpload": False},
        )
        results = (
            StageResult(status="ready", provider=f"password: {secret}"),
            StageResult(
                status="failed",
                provider="local",
                error_code=f"api_key: {secret}",
            ),
            StageResult.ready(
                "local",
                [],
                diagnostics={"note": f"api_key: {secret}"},
            ),
            StageResult.ready("local", [artifact]),
        )
        media_orchestrator = orchestrator.MediaOrchestrator()

        for result in results:
            with self.subTest(result=result.to_dict()):
                self.assertTrue(orchestrator._contains_sensitive_text(result.to_dict()))
                with self.assertRaises(MediaSecurityError):
                    media_orchestrator._safe_result(result, self.root)
                safe_record = media_orchestrator._record(
                    "capture", result, "failed", ""
                )
                self.assertNotIn(secret, json.dumps(safe_record))

        quality_value = {"note": f"password: {secret}"}
        self.assertTrue(quality._contains_sensitive(quality_value))
        self.assertNotIn(
            secret,
            json.dumps(quality._safe_report_value(quality_value)),
        )

    def test_capture_rejects_cross_origin_and_private_routes(self):
        source = "https://enhe.test/product"

        with self.assertRaises(MediaSecurityError):
            validate_capture_shot(
                source,
                {"url": "https://evil.test/x", "selector": "main"},
            )
        with self.assertRaises(MediaSecurityError):
            validate_capture_shot(
                source,
                {"url": "https://enhe.test/admin", "selector": "main"},
            )
        with self.assertRaises(MediaSecurityError):
            validate_capture_shot(
                source,
                {"url": "https://enhe.test/%61dmin", "selector": "main"},
            )

    def test_capture_rejects_localhost_and_invalid_actions_by_default(self):
        with self.assertRaises(MediaSecurityError):
            validate_capture_shot(
                "http://localhost:8000/product",
                {"selector": "main"},
            )
        with self.assertRaises(MediaSecurityError):
            validate_capture_shot(
                "https://enhe.test/product",
                {"selector": "main", "action": "type-password"},
            )

    def test_capture_allows_explicit_local_deterministic_fixture(self):
        self.assertIsNone(
            validate_capture_shot(
                "http://127.0.0.1:8000/product",
                {
                    "url": "http://127.0.0.1:8000/fixture",
                    "selector": "main",
                    "action": "scroll",
                },
                allow_localhost=True,
            )
        )

    def test_capture_rejects_truthy_non_boolean_localhost_permission(self):
        for allow_localhost in (1, "yes"):
            with self.subTest(allow_localhost=allow_localhost):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(
                        "http://127.0.0.1:8000/product",
                        {"selector": "main"},
                        allow_localhost=allow_localhost,
                    )

    def test_capture_rejects_browser_ambiguous_urls(self):
        source = "https://enhe.test/product"
        ambiguous_targets = (
            r"https://evil.test\@enhe.test/product",
            "https://user@enhe.test/product",
            "https://enhe.test/prod\nuct",
            "https://enhe.test/prod\x85uct",
        )

        for target in ambiguous_targets:
            with self.subTest(target=repr(target)):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(source, {"url": target, "selector": "main"})

        self.assertIsNone(
            validate_capture_shot(
                source,
                {"url": "https://ENHE.TEST:443/products/guide", "selector": "main"},
            )
        )

    def test_capture_rejects_nonstandard_numeric_ipv4_hosts(self):
        for hostname in (
            "127.1",
            "2130706433",
            "0x7f000001",
            "017700000001",
        ):
            with self.subTest(hostname=hostname):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(
                        f"http://{hostname}/product",
                        {"selector": "main"},
                        allow_localhost=True,
                    )

    def test_capture_rejects_encoded_and_non_ascii_hosts(self):
        ambiguous_sources = (
            "http://%6cocalhost/product",
            "http://127%2e0%2e0%2e1/product",
            "http://%31%32%37.0.0.1/product",
            "http://127。0。0。1/product",
            "http://１２７.０.０.１/product",
        )

        for source in ambiguous_sources:
            with self.subTest(source=source, allow_localhost="default"):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(source, {"selector": "main"})
            with self.subTest(source=source, allow_localhost=True):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(
                        source,
                        {"selector": "main"},
                        allow_localhost=True,
                    )

    def test_capture_handles_canonical_ip_loopback_hosts(self):
        for source in (
            "https://203.0.113.10/product",
            "http://[2001:db8::1]/product",
        ):
            self.assertIsNone(
                validate_capture_shot(
                    source,
                    {"selector": "main"},
                )
            )

        for source in (
            "http://127.0.0.1/product",
            "http://[::ffff:127.0.0.1]/product",
        ):
            with self.subTest(source=source):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(source, {"selector": "main"})
                self.assertIsNone(
                    validate_capture_shot(
                        source,
                        {"selector": "main"},
                        allow_localhost=True,
                    )
                )

    def test_capture_rejects_nested_private_and_backslash_paths(self):
        source = "https://enhe.test/product"
        private_targets = (
            r"https://enhe.test/safe\..\admin",
            "https://enhe.test/%2561dmin",
            "https://enhe.test/%252561dmin",
            "https://enhe.test/safe%255c..%255cadmin",
        )

        for target in private_targets:
            with self.subTest(target=target):
                with self.assertRaises(MediaSecurityError):
                    validate_capture_shot(source, {"url": target, "selector": "main"})

        self.assertIsNone(
            validate_capture_shot(
                source,
                {
                    "url": "https://enhe.test/products%252Fguide",
                    "selector": "main",
                },
            )
        )

    def test_capture_rejects_paths_beyond_decode_limit(self):
        encoded_path = "/safe%2Fguide"
        for _ in range(8):
            encoded_path = quote(encoded_path, safe="/")

        with self.assertRaises(MediaSecurityError):
            validate_capture_shot(
                "https://enhe.test/product",
                {"url": f"https://enhe.test{encoded_path}", "selector": "main"},
            )

    def test_cloud_media_requires_flag_and_exact_allowlist_membership(self):
        allowed = self.root / "approved" / "product.png"
        other = self.root / "approved" / "other.png"

        self.assertFalse(cloud_file_allowed(allowed, False, [allowed]))
        self.assertTrue(cloud_file_allowed(allowed, True, [allowed]))
        self.assertFalse(cloud_file_allowed(other, True, [allowed]))

    def test_cloud_media_rejects_sensitive_paths_even_when_allowlisted(self):
        cookies = self.root / "Chrome" / "User Data" / "Default" / "Cookies"
        token = self.root / "exports" / "api-token.json"
        login_data = self.root / "exports" / "Login Data.json"

        self.assertFalse(cloud_file_allowed(cookies, True, [cookies]))
        self.assertFalse(cloud_file_allowed(token, True, [token]))
        self.assertFalse(cloud_file_allowed(login_data, True, [login_data]))

    def test_stage_result_detects_changed_and_unchanged_artifacts(self):
        path = self.root / "capture.bin"
        path.write_bytes(b"first")
        artifact = Artifact.from_file(
            "product_capture_image",
            path,
            "playwright",
            "user-authorized",
        )
        result = StageResult.ready("playwright", [artifact])

        with mock.patch.object(
            Path,
            "read_bytes",
            side_effect=AssertionError("Stage validation must stream the file"),
        ):
            self.assertTrue(stage_result_is_valid(result))

        path.write_bytes(b"changed")
        self.assertFalse(stage_result_is_valid(result))

    def test_stage_result_rejects_non_resumable_states(self):
        path = self.root / "capture.bin"
        path.write_bytes(b"first")
        artifact = Artifact.from_file(
            "product_capture_image",
            path,
            "playwright",
            "user-authorized",
        )

        self.assertTrue(
            stage_result_is_valid(
                StageResult(status="degraded", provider="playwright", artifacts=(artifact,))
            )
        )
        self.assertFalse(
            stage_result_is_valid(
                StageResult(status="failed", provider="playwright", artifacts=(artifact,))
            )
        )
        self.assertFalse(
            stage_result_is_valid(
                StageResult(status="skipped", provider="playwright", artifacts=(artifact,))
            )
        )
        self.assertFalse(stage_result_is_valid(StageResult.ready("playwright", [])))
        path.unlink()
        self.assertFalse(
            stage_result_is_valid(StageResult.ready("playwright", [artifact]))
        )
        self.assertFalse(stage_result_is_valid(None))

    def test_redact_secrets_recurses_and_returns_independent_json_containers(self):
        nested = [{"value": "keep"}]
        source = MappingProxyType(
            {
                "api_key": "one",
                "api-key": "two",
                "TOKEN": "three",
                "clientSecret": "four",
                "cookieJar": "five",
                "authorization": {"nested": "six"},
                "safe": {"nested": nested, "tuple": ("a", {"plain": "b"})},
            }
        )

        redacted = redact_secrets(source)

        for key in (
            "api_key",
            "api-key",
            "TOKEN",
            "clientSecret",
            "cookieJar",
            "authorization",
        ):
            self.assertEqual(redacted[key], "[REDACTED]")
        self.assertEqual(
            redacted["safe"],
            {"nested": [{"value": "keep"}], "tuple": ["a", {"plain": "b"}]},
        )
        self.assertIs(type(redacted), dict)
        self.assertIs(type(redacted["safe"]), dict)
        self.assertIs(type(redacted["safe"]["nested"]), list)
        self.assertIs(type(redacted["safe"]["tuple"]), list)
        json.dumps(redacted)

        redacted["safe"]["nested"][0]["value"] = "changed-output"
        self.assertEqual(nested[0]["value"], "keep")
        nested[0]["value"] = "changed-input"
        self.assertEqual(redacted["safe"]["tuple"][1]["plain"], "b")


class PathContractTest(unittest.TestCase):
    def test_artifact_and_stage_result_freeze_nested_json_and_thaw_copies(self):
        metadata = {"origin": {"tags": ["capture"]}}
        artifact = Artifact(
            type="product_capture_image",
            path="C:/captures/product.png",
            sha256="a" * 64,
            source="user-authorized",
            license="owned",
            provider="playwright",
            metadata=metadata,
        )
        stage_payload = {
            "status": "ready",
            "provider": "playwright",
            "artifacts": [artifact.to_dict()],
            "warnings": ["reviewed"],
            "errorCode": "",
            "diagnostics": {"steps": [{"name": "capture"}]},
        }
        result = StageResult.from_dict(stage_payload)

        metadata["origin"]["tags"].append("mutated-input")
        stage_payload["diagnostics"]["steps"][0]["name"] = "mutated-input"
        self.assertEqual(artifact.metadata["origin"]["tags"], ("capture",))
        self.assertEqual(result.diagnostics["steps"][0]["name"], "capture")
        self.assertIsInstance(result.artifacts, tuple)
        self.assertIsInstance(result.warnings, tuple)

        artifact_payload = artifact.to_dict()
        result_payload = result.to_dict()
        artifact_payload["metadata"]["origin"]["tags"].append("mutated-output")
        result_payload["diagnostics"]["steps"][0]["name"] = "mutated-output"
        self.assertEqual(artifact.metadata["origin"]["tags"], ("capture",))
        self.assertEqual(result.diagnostics["steps"][0]["name"], "capture")
        self.assertIsInstance(artifact_payload["metadata"]["origin"]["tags"], list)

        with self.assertRaises(TypeError):
            artifact.metadata["new"] = "value"
        with self.assertRaises(FrozenInstanceError):
            artifact.metadata = {}
        with self.assertRaises(TypeError):
            result.diagnostics["new"] = "value"
        with self.assertRaises(FrozenInstanceError):
            result.diagnostics = {}

        self.assertEqual(Artifact.from_dict(artifact.to_dict()), artifact)
        self.assertEqual(StageResult.from_dict(result.to_dict()), result)

    def test_atomic_write_json_preserves_valid_file_after_write_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "job.json"
            destination.write_text('{"status": "valid"}\n', encoding="utf-8")
            unrelated = Path(temp) / "unrelated.tmp"
            unrelated.write_text("keep", encoding="utf-8")

            with self.assertRaises(TypeError):
                atomic_write_json(destination, {"invalid": object()})

            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                '{"status": "valid"}\n',
            )
            self.assertFalse(destination.with_suffix(".json.tmp").exists())
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")

    def test_atomic_write_json_preserves_unicode_and_replaces_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "nested" / "job.json"

            atomic_write_json(destination, {"标题": "产品录屏", "version": 1})
            atomic_write_json(destination, {"标题": "专业视频", "version": 2})

            text = destination.read_text(encoding="utf-8")
            self.assertIn("专业视频", text)
            self.assertNotIn("产品录屏", text)
            self.assertTrue(text.endswith("\n"))
            self.assertEqual(json.loads(text), {"标题": "专业视频", "version": 2})
            self.assertFalse(destination.with_suffix(".json.tmp").exists())

    def test_media_job_uses_camel_case_json_and_preserves_tuples(self):
        providers = {"capture": "playwright", "voice": "kokoro"}
        job = MediaJob(
            run_id="20260723-120000-enhe-api",
            product_name="ENHE API",
            source_url="https://example.com/enhe",
            language="zh-CN",
            target_platforms=["douyin", "xiaohongshu"],
            quality_target="professional",
            aspect_ratios=["9:16", "1:1"],
            duration_range=[30, 60],
            providers=providers,
            allow_cloud_media=False,
            product_data_path="source-assets_源素材/product.json",
            brand_assets=["logo.png", "palette.json"],
            generated_content_path="generated-content_生成内容/content.json",
            capture_plan_path="product-captures_产品录屏/plan.json",
        )

        providers["capture"] = "mutated-input"
        self.assertEqual(job.providers["capture"], "playwright")
        self.assertIsInstance(job.target_platforms, tuple)
        self.assertIsInstance(job.aspect_ratios, tuple)
        self.assertIsInstance(job.duration_range, tuple)
        self.assertIsInstance(job.brand_assets, tuple)

        payload = job.to_dict()

        self.assertEqual(
            tuple(field.name for field in fields(MediaJob)),
            (
                "run_id",
                "product_name",
                "source_url",
                "language",
                "target_platforms",
                "quality_target",
                "aspect_ratios",
                "duration_range",
                "providers",
                "allow_cloud_media",
                "product_data_path",
                "brand_assets",
                "generated_content_path",
                "capture_plan_path",
                "presenter",
            ),
        )
        self.assertEqual(
            payload,
            {
                "runId": "20260723-120000-enhe-api",
                "productName": "ENHE API",
                "sourceUrl": "https://example.com/enhe",
                "language": "zh-CN",
                "targetPlatforms": ["douyin", "xiaohongshu"],
                "qualityTarget": "professional",
                "aspectRatios": ["9:16", "1:1"],
                "durationRange": [30, 60],
                "providers": {"capture": "playwright", "voice": "kokoro"},
                "allowCloudMedia": False,
                "productDataPath": "source-assets_源素材/product.json",
                "brandAssets": ["logo.png", "palette.json"],
                "generatedContentPath": "generated-content_生成内容/content.json",
                "capturePlanPath": "product-captures_产品录屏/plan.json",
                "presenter": "none",
            },
        )
        round_trip = MediaJob.from_dict(payload)
        self.assertEqual(round_trip, job)
        payload["providers"]["capture"] = "mutated-output"
        self.assertEqual(job.providers["capture"], "playwright")
        self.assertEqual(round_trip.providers["capture"], "playwright")
        with self.assertRaises(TypeError):
            job.providers["capture"] = "mutated-item"
        with self.assertRaises(FrozenInstanceError):
            job.providers = {}

    def test_build_job_serializes_brand_assets_as_absolute_strings(self):
        pipeline = importlib.import_module("scripts.professional_media_pipeline")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = root / "content.json"
            content.write_text("{}", encoding="utf-8")
            logo = root / "logo.png"
            logo.write_bytes(PNG_BYTES)
            args = pipeline.parse_args(
                [
                    "--product-url",
                    "https://example.com/product",
                    "--product-name",
                    "ENHE",
                    "--content-json",
                    str(content),
                    "--brand-logo",
                    str(logo),
                ]
            )

            payload = pipeline.build_job(args).to_dict()
            self.assertEqual(payload["brandAssets"], [str(logo.resolve())])
            json.dumps(payload)

    def test_artifact_and_ready_stage_result_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "capture.png"
            source.write_bytes(b"capture")

            with mock.patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("Artifact hashing must stream the file"),
            ):
                artifact = Artifact.from_file(
                    "product_capture_image",
                    source,
                    "playwright",
                    "user-authorized",
                )
            result = StageResult.ready(
                "playwright", [artifact], diagnostics={"captureCount": 1}
            )
            payload = result.to_dict()

            self.assertEqual(len(artifact.sha256), 64)
            self.assertEqual(
                artifact.sha256,
                "460ee6aa3a80359181b794cc31a7185addba77626e9f719c10e3c8efb8668a1d",
            )
            self.assertEqual(artifact.path, str(source.resolve()))
            self.assertEqual(
                payload,
                {
                    "status": "ready",
                    "provider": "playwright",
                    "artifacts": [
                        {
                            "type": "product_capture_image",
                            "path": str(source.resolve()),
                            "sha256": artifact.sha256,
                            "source": "user-authorized",
                            "license": "",
                            "provider": "playwright",
                            "containsUserData": False,
                            "metadata": {},
                        }
                    ],
                    "warnings": [],
                    "errorCode": "",
                    "diagnostics": {"captureCount": 1},
                },
            )
            self.assertEqual(StageResult.from_dict(payload), result)

    def test_chinese_products_get_distinct_stable_slugged_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            output_root = Path(temp)
            first = new_run_paths(
                output_root, "产品甲", now="20260723-120000"
            )
            second = new_run_paths(
                output_root, "产品乙", now="20260723-120000"
            )

            self.assertNotEqual(first.root, second.root)
            self.assertRegex(
                first.root.name,
                r"^20260723-120000-product-[0-9a-f]{8}$",
            )
            self.assertRegex(
                second.root.name,
                r"^20260723-120000-product-[0-9a-f]{8}$",
            )
            self.assertEqual(slugify("产品甲"), "product-8547c721")
            self.assertEqual(slugify("产品乙"), "product-bf689d1d")

    def test_existing_run_root_gets_next_sequence_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output_root = Path(temp)
            first = new_run_paths(
                output_root, "中文产品", now="20260723-120000"
            ).create()
            sentinel = first.root / "existing.txt"
            sentinel.write_text("keep", encoding="utf-8")

            second = new_run_paths(
                output_root, "中文产品", now="20260723-120000"
            )
            self.assertEqual(second.root.name, f"{first.root.name}-002")
            second.create()
            third = new_run_paths(
                output_root, "中文产品", now="20260723-120000"
            )

            self.assertEqual(third.root.name, f"{first.root.name}-003")
            self.assertNotEqual(first.root, second.root)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_new_run_paths_uses_bilingual_layout(self):
        paths = new_run_paths(
            Path("C:/work/promotion-output_推广输出"),
            "ENHE API",
            now="20260723-120000",
        )

        self.assertEqual(DEFAULT_OUTPUT_ROOT, Path("promotion-output_推广输出"))
        self.assertEqual(RUNS_DIR, "runs_运行记录")
        self.assertEqual(slugify("ENHE API"), "enhe-api")
        self.assertRegex(slugify("中文"), r"^product-[0-9a-f]{8}$")
        self.assertEqual(paths.root.parent.name, RUNS_DIR)
        self.assertEqual(paths.root.name, "20260723-120000-enhe-api")
        self.assertEqual(
            {
                name: getattr(paths, name).name
                for name in (
                    "source_assets",
                    "captures",
                    "generated_content",
                    "voiceovers",
                    "b_roll",
                    "ai_scenes",
                    "videos",
                    "covers",
                    "detail_images",
                    "publish_packs",
                    "reports",
                )
            },
            {
                "source_assets": "source-assets_源素材",
                "captures": "product-captures_产品录屏",
                "generated_content": "generated-content_生成内容",
                "voiceovers": "voiceovers_配音",
                "b_roll": "b-roll_辅助镜头",
                "ai_scenes": "ai-scenes_AI场景图",
                "videos": "videos_视频",
                "covers": "covers_封面",
                "detail_images": "detail-images_详情图",
                "publish_packs": "publish-packs_发布包",
                "reports": "reports_报告",
            },
        )
        self.assertNotIn(
            "promotion-output/product-batch-runs", paths.root.as_posix()
        )

    def test_create_builds_every_directory_and_find_existing_prefers_new(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = new_run_paths(root, "ENHE API", now="20260723-120000")

            returned = paths.create()

            self.assertIs(returned, paths)
            self.assertEqual(
                tuple(field.name for field in fields(RunPaths)),
                (
                    "root",
                    "source_assets",
                    "captures",
                    "generated_content",
                    "voiceovers",
                    "b_roll",
                    "ai_scenes",
                    "videos",
                    "covers",
                    "detail_images",
                    "publish_packs",
                    "reports",
                ),
            )
            self.assertTrue(
                all(
                    getattr(paths, field.name).is_dir()
                    for field in fields(RunPaths)
                )
            )

            new = root / "new"
            legacy = root / "legacy"
            self.assertEqual(find_existing(new, legacy), new)
            legacy.mkdir()
            self.assertEqual(find_existing(new, legacy), legacy)
            new.mkdir()
            self.assertEqual(find_existing(new, legacy), new)


class ProductCaptureTest(unittest.TestCase):
    def test_default_plan_has_five_exact_product_shots(self):
        capture = load_capture_module(self)
        source_url = "https://example.com/product"

        self.assertEqual(
            capture.build_default_capture_plan(source_url),
            {
                "sourceUrl": source_url,
                "shots": [
                    {
                        "id": "hero",
                        "url": source_url,
                        "selector": "#hero",
                        "action": "none",
                        "viewport": [1440, 900],
                        "screenshotMode": "viewport",
                        "duration": 3,
                    },
                    {
                        "id": "workflow",
                        "url": source_url,
                        "selector": "#workflow",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "screenshotMode": "viewport",
                        "duration": 4,
                    },
                    {
                        "id": "features",
                        "url": source_url,
                        "selector": "#features",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "screenshotMode": "viewport",
                        "duration": 4,
                    },
                    {
                        "id": "proof",
                        "url": source_url,
                        "selector": "#proof",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "screenshotMode": "viewport",
                        "duration": 3,
                    },
                    {
                        "id": "cta",
                        "url": source_url,
                        "selector": "#cta",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "screenshotMode": "viewport",
                        "duration": 3,
                    },
                ],
            },
        )

    def test_captures_real_screenshots_and_interaction_video(self):
        capture = load_capture_module(self)
        if not capture.playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")

        with serve_product_fixture() as source_url, tempfile.TemporaryDirectory() as temp:
            plan = capture.build_default_capture_plan(source_url)
            result = capture.PlaywrightCaptureProvider(
                allow_localhost=True
            ).capture(plan, Path(temp))

            self.assertEqual(result.status, "ready", result.to_dict())
            images = [
                artifact
                for artifact in result.artifacts
                if artifact.type == "product_capture_image"
            ]
            videos = [
                artifact
                for artifact in result.artifacts
                if artifact.type == "product_capture_video"
            ]
            self.assertGreaterEqual(len(images), 5)
            self.assertGreaterEqual(
                len({artifact.sha256 for artifact in images}), 3
            )
            self.assertGreaterEqual(len(videos), 1)

            for artifact in result.artifacts:
                path = Path(artifact.path)
                self.assertTrue(path.is_file(), artifact.path)
                self.assertGreater(path.stat().st_size, 1000, artifact.path)

            image_keys = {
                "shotId",
                "requestedSelector",
                "resolvedSelector",
                "selectorFallback",
                "finalUrl",
                "viewport",
                "screenshotMode",
            }
            for artifact in images:
                metadata = artifact.to_dict()["metadata"]
                self.assertTrue(image_keys.issubset(metadata), metadata)
                self.assertEqual(metadata["viewport"], [1440, 900])
                self.assertEqual(metadata["screenshotMode"], "viewport")
                from PIL import Image

                with Image.open(artifact.path) as image:
                    self.assertEqual(image.size, (1440, 900))

            for artifact in videos:
                metadata = artifact.to_dict()["metadata"]
                self.assertTrue(
                    {"finalUrl", "viewport", "shotIds"}.issubset(metadata),
                    metadata,
                )
                self.assertEqual(metadata["viewport"], [1440, 900])
                self.assertEqual(
                    metadata["shotIds"],
                    ["hero", "workflow", "features", "proof", "cta"],
                )

    def test_missing_selector_falls_back_to_main_and_records_metadata(self):
        capture = load_capture_module(self)
        if not capture.playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")

        with serve_product_fixture() as source_url, tempfile.TemporaryDirectory() as temp:
            plan = capture.build_default_capture_plan(source_url)
            shot = dict(plan["shots"][0])
            shot["selector"] = "#missing-product-section"
            plan["shots"] = [shot]

            result = capture.PlaywrightCaptureProvider(
                allow_localhost=True
            ).capture(plan, Path(temp))

            self.assertEqual(result.status, "ready", result.to_dict())
            image = next(
                artifact
                for artifact in result.artifacts
                if artifact.type == "product_capture_image"
            )
            metadata = image.to_dict()["metadata"]
            self.assertEqual(
                metadata["requestedSelector"], "#missing-product-section"
            )
            self.assertEqual(metadata["resolvedSelector"], "main")
            self.assertIs(metadata["selectorFallback"], True)

    def test_invalid_remote_plans_raise_before_playwright_launch(self):
        capture = load_capture_module(self)
        cross_origin = capture.build_default_capture_plan(
            "https://example.com/product"
        )
        cross_origin["shots"][0]["url"] = "https://other.example/product"
        private_route = capture.build_default_capture_plan(
            "https://example.com/admin/product"
        )

        for plan in (cross_origin, private_route):
            with self.subTest(
                source_url=plan["sourceUrl"]
            ), tempfile.TemporaryDirectory() as temp:
                with mock.patch.object(capture, "sync_playwright") as start:
                    launch = start.return_value.start.return_value.chromium.launch
                    with self.assertRaises(MediaSecurityError):
                        capture.PlaywrightCaptureProvider().capture(
                            plan, Path(temp)
                        )

                start.assert_not_called()
                launch.assert_not_called()

    def test_click_rejects_cross_origin_link_before_request(self):
        capture = load_capture_module(self)
        if not capture.playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")

        target_hits = []

        class TargetHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                pass

            def do_GET(self):
                target_hits.append(self.path)
                payload = b"target"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        target_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), TargetHandler
        )
        target_server.daemon_threads = True
        target_thread = threading.Thread(
            target=target_server.serve_forever, daemon=True
        )
        target_thread.start()

        class SourceHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                pass

            def do_GET(self):
                target_url = (
                    f"http://127.0.0.1:{target_server.server_port}/target"
                )
                payload = (
                    "<main><a id='leave' href='"
                    + target_url
                    + "'>Leave</a></main>"
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        source_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), SourceHandler
        )
        source_server.daemon_threads = True
        source_thread = threading.Thread(
            target=source_server.serve_forever, daemon=True
        )
        source_thread.start()
        try:
            source_url = f"http://127.0.0.1:{source_server.server_port}/"
            plan = {
                "sourceUrl": source_url,
                "shots": [
                    {
                        "id": "leave",
                        "url": source_url,
                        "selector": "#leave",
                        "action": "click",
                        "viewport": [800, 600],
                        "screenshotMode": "viewport",
                        "duration": 1,
                    }
                ],
            }
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(MediaSecurityError):
                    capture.PlaywrightCaptureProvider(
                        allow_localhost=True
                    ).capture(plan, Path(temp))
            self.assertEqual(target_hits, [])
        finally:
            source_server.shutdown()
            source_server.server_close()
            source_thread.join(timeout=5)
            target_server.shutdown()
            target_server.server_close()
            target_thread.join(timeout=5)

    def test_http_errors_fail_without_ready_artifacts(self):
        capture = load_capture_module(self)
        if not capture.playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")

        with serve_product_fixture() as source_url, tempfile.TemporaryDirectory() as temp:
            fixture_root = source_url.rsplit("/", 1)[0]
            initial_404 = capture.build_default_capture_plan(
                f"{fixture_root}/status/404"
            )
            shot_500 = capture.build_default_capture_plan(source_url)
            shot_500["shots"][1]["url"] = f"{fixture_root}/status/500"

            for plan, error_code in (
                (initial_404, "navigate_source_failed"),
                (shot_500, "navigate_workflow_failed"),
            ):
                with self.subTest(error_code=error_code):
                    result = capture.PlaywrightCaptureProvider(
                        allow_localhost=True
                    ).capture(plan, Path(temp) / error_code)

                    self.assertEqual(result.status, "failed", result.to_dict())
                    self.assertEqual(result.error_code, error_code)
                    self.assertEqual(result.artifacts, ())

    def test_invalid_screenshot_mode_is_rejected_before_playwright_launch(self):
        capture = load_capture_module(self)
        plan = capture.build_default_capture_plan("https://example.com/product")
        plan["shots"][0]["screenshotMode"] = "full-page"

        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
            capture, "sync_playwright"
        ) as start:
            with self.assertRaisesRegex(
                MediaSecurityError, "screenshotMode must be element or viewport"
            ):
                capture.PlaywrightCaptureProvider().capture(plan, Path(temp))
            start.assert_not_called()

    def test_malformed_selector_fails_instead_of_using_fallback(self):
        capture = load_capture_module(self)
        if not capture.playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")

        with serve_product_fixture() as source_url, tempfile.TemporaryDirectory() as temp:
            plan = capture.build_default_capture_plan(source_url)
            plan["shots"] = [dict(plan["shots"][0], selector="[bad")]

            result = capture.PlaywrightCaptureProvider(
                allow_localhost=True
            ).capture(plan, Path(temp))

            self.assertEqual(result.status, "failed", result.to_dict())
            self.assertEqual(result.error_code, "capture_hero_failed")
            self.assertEqual(result.artifacts, ())

    def test_artifact_urls_remove_sensitive_query_and_fragment(self):
        capture = load_capture_module(self)
        if not capture.playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")

        secret = "SECRET123"
        with serve_product_fixture() as source_url, tempfile.TemporaryDirectory() as temp:
            private_source_url = (
                f"{source_url}?token={secret}&view=demo#private-fragment"
            )
            result = capture.PlaywrightCaptureProvider(
                allow_localhost=True
            ).capture(
                capture.build_default_capture_plan(private_source_url), Path(temp)
            )

            self.assertEqual(result.status, "ready", result.to_dict())
            serialized = json.dumps(result.to_dict(), sort_keys=True)
            self.assertNotIn(secret, serialized)
            for artifact in result.artifacts:
                final_url = urlsplit(artifact.to_dict()["metadata"]["finalUrl"])
                self.assertEqual(final_url.scheme, "http")
                self.assertEqual(final_url.hostname, "127.0.0.1")
                self.assertEqual(final_url.path, "/product.html")
                self.assertEqual(final_url.query, "")
                self.assertEqual(final_url.fragment, "")


class CommercialVisualTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        from PIL import Image, ImageDraw

        self.background = self.root / "ai-background.png"
        self.capture = self.root / "product-capture.png"
        self.logo = self.root / "brand-logo.png"
        Image.new("RGB", (1200, 1200), (34, 62, 118)).save(self.background)
        capture = Image.new("RGB", (800, 500), (245, 246, 250))
        draw = ImageDraw.Draw(capture)
        draw.rectangle((50, 40, 750, 105), fill=(29, 78, 216))
        draw.text((80, 60), "REAL PRODUCT CAPTURE", fill="white")
        draw.rectangle((75, 145, 725, 430), outline=(16, 185, 129), width=12)
        capture.save(self.capture)
        Image.new("RGBA", (200, 100), (239, 68, 68, 255)).save(self.logo)

    def tearDown(self):
        self.temp.cleanup()

    def test_xiaohongshu_render_is_ready_with_product_provenance(self):
        visuals = importlib.import_module("scripts.media_pipeline.visuals")
        result = visuals.CommercialVisualCompositor().render(
            platform="xiaohongshu",
            title="把产品网页变成推广素材",
            subtitle="真实录屏 · 有声视频 · 商业视觉",
            background=self.background,
            product_capture=self.capture,
            logo=self.logo,
            out_dir=self.root / "outputs",
            background_source={"provider": "local-internal", "source": "test-fixture", "license": "fixture-license"},
        )
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.provider, "local_compositor")
        self.assertGreaterEqual(len(result.artifacts), 5)
        cover = next(a for a in result.artifacts if a.type == "cover_image")
        with self.subTest(cover=cover.path):
            from PIL import Image, ImageStat

            with Image.open(cover.path) as cover_image:
                self.assertEqual(cover_image.size, (1080, 1440))
                self.assertEqual(cover_image.format, "PNG")
                self.assertTrue(Path(cover.path).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
                # The central product frame contains source pixels, rather than
                # a generated dashboard/card substitute.
                frame_stats = ImageStat.Stat(cover_image.crop((100, 650, 980, 1250)))
                self.assertGreater(max(frame_stats.stddev), 8.0)
        contact = next(a for a in result.artifacts if a.type == "contact_sheet")
        self.assertEqual(contact.metadata["count"], 4)
        self.assertEqual(contact.metadata["platforms"], ("xiaohongshu",))
        expected_hash = hashlib.sha256(self.capture.read_bytes()).hexdigest()
        for artifact in result.artifacts:
            if artifact.type in {"cover_image", "detail_image"}:
                metadata = artifact.to_dict()["metadata"]
                self.assertTrue(metadata["containsProductCapture"])
                self.assertEqual(metadata["productCaptureSha256"], expected_hash)
                self.assertTrue(metadata["hasBrand"])
                self.assertTrue(metadata["usesAiScene"])
                self.assertEqual(artifact.license, "fixture-license")
                self.assertEqual(metadata["dimensions"], [1080, 1440])
                self.assertEqual(metadata["logoSha256"], hashlib.sha256(self.logo.read_bytes()).hexdigest())
                self.assertIn(metadata["capturePixelMode"], {"native", "resized"})
                self.assertTrue(metadata["sourcePixelsEmbedded"])
                self.assertEqual(metadata["productCaptureProvenance"]["source"], "local-input")
                self.assertEqual(
                    metadata["aiSceneProvenance"],
                    {
                        "provider": "local-internal",
                        "source": "test-fixture",
                        "license": "fixture-license",
                        "sha256": hashlib.sha256(self.background.read_bytes()).hexdigest(),
                    },
                )
                self.assertTrue(
                    all(
                        metadata["safeMargins"][side] >= 0.05
                        for side in ("top", "right", "bottom", "left")
                    )
                )

    def test_all_supported_platform_dimensions_and_details(self):
        visuals = importlib.import_module("scripts.media_pipeline.visuals")
        expected = {
            "youtube": (1920, 1080),
            "zhihu": (1200, 628),
            "xiaohongshu": (1080, 1440),
            "douyin": (1080, 1920),
            "github": (1280, 640),
        }
        for platform, dimensions in expected.items():
            with self.subTest(platform=platform):
                result = visuals.CommercialVisualCompositor().render(
                    platform=platform,
                    title="Product promotion",
                    subtitle="Local capture",
                    background=self.background,
                    product_capture=self.capture,
                    logo=self.logo,
                    out_dir=self.root / platform,
                    background_source={"provider": "local-internal", "source": "test-fixture", "license": "fixture-license"},
                )
                self.assertEqual(result.status, "ready")
                covers = [a for a in result.artifacts if a.type == "cover_image"]
                details = [a for a in result.artifacts if a.type == "detail_image"]
                self.assertEqual(len(covers), 1)
                self.assertGreaterEqual(len(details), 2)
                from PIL import Image

                with Image.open(covers[0].path) as cover_image:
                    self.assertEqual(cover_image.size, dimensions)
                for detail in details:
                    with Image.open(detail.path) as detail_image:
                        self.assertEqual(detail_image.size, dimensions)
                self.assertGreaterEqual(len({a.sha256 for a in details}), 2)

    def test_invalid_input_fails_without_ready_artifacts(self):
        visuals = importlib.import_module("scripts.media_pipeline.visuals")
        result = visuals.CommercialVisualCompositor().render(
            platform="xiaohongshu",
            title="Title",
            subtitle="Subtitle",
            background=self.root / "missing.png",
            product_capture=self.capture,
            logo=self.logo,
            out_dir=self.root / "invalid",
        )
        self.assertEqual(result.status, "failed")
        self.assertFalse(result.artifacts)
        self.assertTrue(result.error_code)

    def test_missing_or_unlicensed_ai_provenance_fails_closed(self):
        visuals = importlib.import_module("scripts.media_pipeline.visuals")
        for provenance in (None, {"provider": "local", "source": "fixture", "license": ""}):
            with self.subTest(provenance=provenance):
                result = visuals.CommercialVisualCompositor().render(
                    platform="xiaohongshu",
                    title="Title",
                    subtitle="Subtitle",
                    background=self.background,
                    product_capture=self.capture,
                    logo=self.logo,
                    out_dir=self.root / "missing-provenance",
                    background_source=provenance,
                )
                self.assertEqual(result.status, "failed")
                self.assertFalse(result.artifacts)
                self.assertIn(result.error_code, {"missing_ai_scene_provenance", "invalid_ai_scene_provenance"})

    def test_failed_rerender_removes_stale_compositor_targets(self):
        visuals = importlib.import_module("scripts.media_pipeline.visuals")
        output = self.root / "stale-output"
        provenance = {"provider": "local-internal", "source": "test-fixture", "license": "fixture-license"}
        compositor = visuals.CommercialVisualCompositor()
        ready = compositor.render(
            platform="xiaohongshu",
            title="Title",
            subtitle="Subtitle",
            background=self.background,
            product_capture=self.capture,
            logo=self.logo,
            out_dir=output,
            background_source=provenance,
        )
        self.assertEqual(ready.status, "ready")
        targets = [
            output / "xiaohongshu-cover.png",
            output / "xiaohongshu-detail-01.png",
            output / "xiaohongshu-detail-02.png",
            output / "xiaohongshu-detail-03.png",
            output / "xiaohongshu-contact-sheet.png",
        ]
        self.assertTrue(all(path.is_file() for path in targets))
        original_save = visuals._atomic_save
        calls = {"count": 0}

        def fail_third(image, path):
            calls["count"] += 1
            if calls["count"] == 3:
                raise RuntimeError("injected_atomic_failure")
            return original_save(image, path)

        with mock.patch.object(visuals, "_atomic_save", side_effect=fail_third):
            failed = compositor.render(
                platform="xiaohongshu",
                title="Title",
                subtitle="Subtitle",
                background=self.background,
                product_capture=self.capture,
                logo=self.logo,
                out_dir=output,
                background_source=provenance,
            )
        self.assertEqual(failed.status, "failed")
        self.assertTrue(all(not path.exists() for path in targets))

        missing = compositor.render(
            platform="xiaohongshu",
            title="Title",
            subtitle="Subtitle",
            background=self.background,
            product_capture=self.capture,
            logo=self.logo,
            out_dir=output,
        )
        self.assertEqual(missing.status, "failed")
        self.assertTrue(all(not path.exists() for path in targets))


class ProfessionalVideoTest(unittest.TestCase):
    def load_video(self):
        module_name = "scripts.media_pipeline.video"
        self.assertIsNotNone(
            importlib.util.find_spec(module_name),
            "video module must implement the HyperFrames product-demo contract",
        )
        return importlib.import_module(module_name)

    def test_project_contains_five_shots_three_motion_types_and_local_gsap(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = video.sample_composition_data(root)
            project = video.materialize_hyperframes_project(data, root / "project")
            html = (project / "index.html").read_text(encoding="utf-8")
            script = (project / "composition.js").read_text(encoding="utf-8")
            self.assertNotIn("cdn.jsdelivr.net", html)
            self.assertTrue((project / "vendor" / "gsap.min.js").is_file())
            self.assertIn('data-composition-id="root"', html)
            self.assertIn('data-width="1920"', html)
            self.assertIn('data-height="1080"', html)
            self.assertIn('data-duration="20.0"', html)
            self.assertGreaterEqual(len(data["shots"]), 5)
            self.assertEqual(set(video.MOTION_TYPES), set(data["motionTypes"]))
            for motion_type in video.MOTION_TYPES:
                self.assertIn(motion_type, script)
            self.assertIn("escapeHtml", script)
            self.assertIn("gsap.timeline({ paused: true", script)
            self.assertIn("window.__timelines.root", script)
            serialised = json.loads(
                (project / "composition-data.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(serialised["shots"]), 5)
            self.assertTrue(
                all(not Path(shot["src"]).is_absolute() for shot in serialised["shots"])
            )

    def test_project_inlines_data_driven_timeline_for_hyperframes_compiler(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = video.materialize_hyperframes_project(
                video.sample_composition_data(root), root / "project"
            )
            index = (project / "index.html").read_text(encoding="utf-8")

            self.assertNotIn('<script src="./composition.js"></script>', index)
            self.assertIn("shots.forEach(addShot);", index)
            self.assertIn("window.__timelines.root = timeline;", index)

    def test_professional_render_has_h264_aac_and_non_silent_audio(self):
        video = self.load_video()
        if not video.professional_render_available():
            self.skipTest("HyperFrames/Kokoro/FFmpeg runtime unavailable")
        with tempfile.TemporaryDirectory() as temp:
            result = video.render_fixture_professional_video(Path(temp))
            self.assertEqual(result.status, "ready", result.to_dict())
            probe = result.diagnostics["probe"]
            self.assertEqual(probe["videoCodec"], "h264")
            self.assertEqual(probe["audioCodec"], "aac")
            self.assertTrue(probe["nonSilent"])
            self.assertGreaterEqual(probe["shortEdge"], 1080)
            artifact = result.artifacts[0].to_dict()
            metadata = artifact["metadata"]
            self.assertEqual(metadata["sourceAssetCount"], 6)
            self.assertEqual(len(metadata["sourceHashes"]), 5)
            self.assertEqual(len(metadata["voiceoverSha256"]), 64)
            self.assertTrue(all(len(item["sha256"]) == 64 for item in metadata["sourceHashes"]))
            self.assertFalse(metadata["cloudUpload"])


    def test_inline_payload_escapes_script_terminators(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = video.sample_composition_data(root)
            data["shots"][0]["title"] = "</script><script>window.PWN=1</script>"
            data["captions"][0]["text"] = "</script><img src=x onerror=alert(1)>"
            project = video.materialize_hyperframes_project(data, root / "project")
            html = (project / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("</script><script>window.PWN", html)
            self.assertIn(r"\u003c/script\u003e", html)

    def test_quality_gate_rejects_invalid_probe(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = video.sample_composition_data(root)
            output = root / "invalid-quality.mp4"
            output.write_bytes(b"OLD_VALID")
            bad_probe = {
                "videoCodec": "mpeg4",
                "audioCodec": "",
                "videoStreams": 1,
                "audioStreams": 0,
                "nonSilent": False,
                "shortEdge": 360,
                "duration": 1.0,
            }
            with mock.patch.object(video, "materialize_hyperframes_project"), mock.patch.object(
                video, "hyperframes_executable", return_value=Path("hyperframes.mjs")
            ), mock.patch.object(video, "_tool", side_effect=lambda name: "node.exe" if name == "node" else None), mock.patch.object(
                video, "_run", return_value=mock.Mock(stdout="", stderr="")
            ), mock.patch.object(video, "_encode_final"), mock.patch.object(
                video, "probe_media", return_value=bad_probe
            ):
                result = video.render_professional_video(data, output, root / "project")
            self.assertEqual(result.status, "failed")
            self.assertEqual(result.error_code, "professional_video_quality_gate_failed")
            self.assertEqual(output.read_bytes(), b"OLD_VALID")
            self.assertIn("video_codec_not_h264", result.warnings)

    def test_final_encode_is_atomic_and_preserves_previous_output(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "raw.mp4"
            output = root / "final.mp4"
            raw.write_bytes(b"raw")
            output.write_bytes(b"OLD_VALID")

            def fail_after_partial(command, cwd=None):
                Path(command[-1]).write_bytes(b"PARTIAL")
                raise subprocess.CalledProcessError(1, command, stderr="encode failed")

            with mock.patch.object(video, "_tool", return_value="ffmpeg"), mock.patch.object(
                video, "probe_media", return_value={"audioStreams": 0}
            ), mock.patch.object(video, "_run", side_effect=fail_after_partial):
                with self.assertRaises(subprocess.CalledProcessError):
                    video._encode_final(raw, output, None, 2.0)
            self.assertEqual(output.read_bytes(), b"OLD_VALID")
            self.assertFalse(Path(str(output) + ".part").exists())

    def test_resolution_presets_and_css_follow_composition_size(self):
        video = self.load_video()
        self.assertEqual(video._resolution_preset(1920, 1080), "landscape")
        self.assertEqual(video._resolution_preset(1080, 1920), "portrait")
        self.assertEqual(video._resolution_preset(1080, 1080), "square")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = video.sample_composition_data(root)
            data.update({"width": 1080, "height": 1920})
            project = video.materialize_hyperframes_project(data, root / "project")
            style = (project / "style.css").read_text(encoding="utf-8")
            index = (project / "index.html").read_text(encoding="utf-8")
            self.assertIn("--width: 1080px", style)
            self.assertIn("--height: 1920px", style)
            self.assertIn('data-width="1080"', index)
            self.assertIn('data-height="1920"', index)

    def test_quality_gate_requires_distinct_sources_and_default_duration_range(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = video.sample_composition_data(root)
            clean = video._normalise_data(data)
            duplicate_hash = "a" * 64
            clean["sourceHashes"] = [
                {"shotId": shot["id"], "sha256": duplicate_hash}
                for shot in clean["shots"]
            ]
            probe = {
                "videoCodec": "h264",
                "audioCodec": "aac",
                "videoStreams": 1,
                "audioStreams": 1,
                "nonSilent": True,
                "shortEdge": 1080,
                "duration": 20.0,
                "sampledVisualFrames": 10,
                "distinctVisualFrames": 5,
            }
            errors = video._quality_errors(clean, probe)
            self.assertIn("product_sources_not_distinct", errors)
            self.assertIn("supporting_sources_not_distinct", errors)
            clean["sourceHashes"] = [
                {"shotId": shot["id"], "sha256": f"{index + 1:064x}"}
                for index, shot in enumerate(clean["shots"])
            ]
            clean["duration"] = 1
            errors = video._quality_errors(clean, {**probe, "duration": 1.0})
            self.assertIn("target_duration_out_of_range", errors)
            clean["duration"] = 20
            self.assertIn("rendered_duration_out_of_range", video._quality_errors(clean, {**probe, "duration": 18.0}))
            clean["duration"] = 60
            self.assertIn("rendered_duration_out_of_range", video._quality_errors(clean, {**probe, "duration": 60.4}))

    def test_quality_gate_rejects_static_visual_video(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            clean = video._normalise_data(video.sample_composition_data(Path(temp)))
            clean["sourceHashes"] = [
                {"shotId": shot["id"], "sha256": f"{index + 1:064x}"}
                for index, shot in enumerate(clean["shots"])
            ]
            probe = {
                "videoCodec": "h264",
                "audioCodec": "aac",
                "videoStreams": 1,
                "audioStreams": 1,
                "nonSilent": True,
                "shortEdge": 1080,
                "duration": 20.0,
                "sampledVisualFrames": 10,
                "distinctVisualFrames": 1,
            }

            self.assertIn("video_visuals_static", video._quality_errors(clean, probe))

    def test_quality_gate_rejects_dimension_mismatch_and_empty_captions(self):
        video = self.load_video()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = video.sample_composition_data(root)
            data.update({"width": 1080, "height": 1920, "captions": []})
            clean = video._normalise_data(data)
            clean["sourceHashes"] = [
                {"shotId": shot["id"], "sha256": f"{index + 1:064x}"}
                for index, shot in enumerate(clean["shots"])
            ]
            probe = {
                "videoCodec": "h264",
                "audioCodec": "aac",
                "videoStreams": 1,
                "audioStreams": 1,
                "nonSilent": True,
                "width": 1920,
                "height": 1080,
                "shortEdge": 1080,
                "duration": 20.0,
                "sampledVisualFrames": 10,
                "distinctVisualFrames": 5,
            }
            errors = video._quality_errors(clean, probe)
            self.assertIn("resolution_dimensions_mismatch", errors)
            self.assertIn("captions_missing", errors)


class MediaQualityTest(unittest.TestCase):
    """Offline regression tests for the fail-closed quality gate."""

    @staticmethod
    def complete_evidence():
        return {
            "probe": {
                "videoCodec": "h264",
                "audioCodec": "aac",
                "shortEdge": 1080,
                "duration": 20.0,
                "nonSilent": True,
                "sampledVisualFrames": 10,
                "distinctVisualFrames": 5,
            },
            "productCaptures": [{"sha256": f"capture-{index}"} for index in range(3)],
            "videos": [{"shotIds": [f"shot-{index}" for index in range(5)]}],
            "supportingScenes": [{"sha256": "scene-1"}, {"sha256": "scene-2"}],
            "aiScenes": [{"aiGenerated": True}],
            "motionTypes": ["zoomPan", "productHighlight", "sceneTransition"],
            "captionsSynced": True,
            "covers": [{"containsProductCapture": True, "hasBrand": True}],
            "detailImages": [{"containsProductCapture": True}],
            "contactSheets": [{}],
        }

    def test_professional_requires_every_video_and_visual_gate(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        report = quality.evaluate_media_quality(self.complete_evidence(), target="professional")
        self.assertEqual(report["status"], "professional_ready")
        self.assertEqual(report["blockers"], [])

        evidence = self.complete_evidence()
        evidence["probe"]["authorization"] = "Bearer LEAK_TOKEN"
        evidence["probe"]["sourceUrl"] = "https://example.test/?token=LEAK_QUERY"
        safe_report = quality.evaluate_media_quality(evidence, target="professional")
        rendered = json.dumps(safe_report, ensure_ascii=False)
        self.assertNotIn("LEAK_TOKEN", rendered)
        self.assertNotIn("LEAK_QUERY", rendered)

    def test_missing_ai_scene_downgrades_to_standard(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        evidence = self.complete_evidence()
        evidence["aiScenes"] = []
        report = quality.evaluate_media_quality(evidence, target="professional")
        self.assertEqual(report["status"], "standard_ready")
        self.assertIn("ai_photographic_scene_missing", report["blockers"])

    def test_static_visual_probe_downgrades_professional_quality(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        evidence = self.complete_evidence()
        evidence["probe"]["distinctVisualFrames"] = 1

        report = quality.evaluate_media_quality(evidence, target="professional")

        self.assertEqual(report["status"], "standard_ready")
        self.assertIn("video_visuals_static", report["blockers"])

        evidence["probe"]["sampledVisualFrames"] = "not-a-number"
        report = quality.evaluate_media_quality(evidence, target="professional")
        self.assertEqual(report["status"], "standard_ready")
        self.assertIn("video_visuals_static", report["blockers"])

    def test_missing_capture_or_visual_family_is_partial(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        evidence = self.complete_evidence()
        evidence["productCaptures"] = []
        report = quality.evaluate_media_quality(evidence, target="professional")
        self.assertEqual(report["status"], "partial_ready")

        video_only_probe = self.complete_evidence()
        video_only_probe["videos"] = []
        video_only_probe["video"] = []
        report = quality.evaluate_media_quality(video_only_probe, target="professional")
        self.assertIn("videos", report["missingFamilies"])

    def test_artifact_gate_rejects_corruption_dimensions_silence_and_secrets(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            try:
                from PIL import Image
            except ImportError:
                self.skipTest("Pillow unavailable")
            image_path = root / "capture.png"
            Image.new("RGB", (20, 20), "#29466d").save(image_path, format="PNG")
            capture = Artifact.from_file("product_capture_image", image_path, "playwright", "product_page")
            capture = replace(capture, metadata={"viewport": [21, 20], "cloudUpload": False})
            capture_stage = StageResult.ready("playwright", [capture])
            report = quality.build_quality_report({"capture": capture_stage}, target="professional")
            self.assertEqual(report["status"], "partial_ready")
            self.assertIn("png_dimensions_mismatch", report["artifacts"][0]["failures"])

            damaged = root / "damaged.png"
            damaged.write_bytes(b"not a png")
            damaged_artifact = Artifact.from_file("cover_image", damaged, "local", "composite")
            damaged_artifact = replace(damaged_artifact, metadata={"cloudUpload": False})
            result = quality.build_quality_report({"visuals": StageResult.ready("local", [damaged_artifact])})
            self.assertIn("png_invalid", result["artifacts"][0]["failures"])

            silent = root / "silent.mp4"
            silent.write_bytes(b"fake mp4")
            video_artifact = Artifact.from_file("professional_product_demo_video", silent, "local", "composition")
            video_artifact = replace(video_artifact, metadata={"cloudUpload": False})
            with mock.patch.object(quality, "probe_media", return_value={"videoCodec": "h264", "audioCodec": "aac", "shortEdge": 1080, "duration": 4.0, "nonSilent": False, "sampledVisualFrames": 2, "distinctVisualFrames": 2}):
                video_report = quality.build_quality_report({"video": StageResult.ready("local", [video_artifact])})
            self.assertIn("video_silent", video_report["artifacts"][0]["failures"])
            with mock.patch.object(quality, "probe_media", return_value={"videoCodec": "h264", "audioCodec": "aac", "shortEdge": 1080, "duration": 4.0, "nonSilent": True, "sampledVisualFrames": 2, "distinctVisualFrames": 2, "sourceUrl": "https://example.test/?token=LEAK_PROBE"}):
                probe_report = quality.build_quality_report({"video": StageResult.ready("local", [video_artifact])})
            self.assertNotIn("LEAK_PROBE", json.dumps(probe_report, ensure_ascii=False))

            interaction = root / "interaction.webm"
            interaction.write_bytes(b"fake webm")
            interaction_artifact = replace(
                Artifact.from_file(
                    "product_capture_video", interaction, "playwright", "product_page"
                ),
                metadata={"cloudUpload": False},
            )
            interaction_probe = {
                "videoCodec": "vp8",
                "audioCodec": "",
                "shortEdge": 900,
                "duration": 8.0,
                "nonSilent": False,
            }
            with mock.patch.object(quality, "probe_media", return_value=interaction_probe):
                interaction_report = quality.build_quality_report(
                    {"capture": StageResult.ready("playwright", [interaction_artifact])}
                )
            interaction_check = interaction_report["artifacts"][0]
            self.assertTrue(interaction_check["passed"])
            self.assertNotIn("video_codec_mismatch", interaction_check["failures"])
            self.assertNotIn("video_resolution_too_small", interaction_check["failures"])
            self.assertNotIn("video_silent", interaction_check["failures"])
            self.assertIn("videos", interaction_report["missingFamilies"])

            leaky_provenance = replace(capture, provider="Bearer LEAK_PROVIDER", source="https://example.test/?token=LEAK_SOURCE")
            provenance_report = quality.build_quality_report({"capture": StageResult.ready("local", [leaky_provenance])})
            self.assertIn("artifact_provider_secret", provenance_report["artifacts"][0]["failures"])
            self.assertIn("artifact_source_secret", provenance_report["artifacts"][0]["failures"])

            secret = Artifact.from_file("product_capture_image", image_path, "playwright", "product_page")
            secret = replace(secret, metadata={"viewport": [20, 20], "cloudUpload": False, "api_key": "do-not-log", "safeMargins": "Bearer LEAK_META", "dimensions": ["token=LEAK_DIM", 1]})
            secret_report = quality.build_quality_report({"capture": StageResult.ready("playwright", [secret])})
            self.assertIn("secret_metadata_rejected", secret_report["artifacts"][0]["failures"])
            secret_rendered = json.dumps(secret_report, ensure_ascii=False)
            self.assertNotIn("LEAK_META", secret_rendered)
            self.assertNotIn("LEAK_DIM", secret_rendered)

            invalid_descriptor = quality._inspect_artifact({"type": "", "path": "C:/Cookies/secret.bin"})
            self.assertEqual(invalid_descriptor["path"], "redacted_sensitive_value")

            sensitive_dir = root / "Cookies"
            sensitive_dir.mkdir()
            sensitive_path = sensitive_dir / "capture.png"
            sensitive_path.write_bytes(b"not-a-png")
            sensitive = Artifact.from_file("product_capture_image", sensitive_path, "playwright", "product_page")
            sensitive_report = quality.build_quality_report({"capture": StageResult.ready("playwright", [sensitive])})
            self.assertEqual(sensitive_report["artifacts"][0]["path"], "[redacted-sensitive-path]")

    def test_atomic_machine_report_and_stage_result_statuses(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reports" / "media-quality-report.json"
            report = quality.evaluate_media_quality(self.complete_evidence())
            destination = quality.write_quality_report(path, report)
            self.assertEqual(destination, path.resolve())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["status"], "professional_ready")
            self.assertFalse(path.with_name(path.name + ".tmp").exists())
            gate = quality.run_quality_gate({}, report_path=Path(temp) / "empty.json")
            self.assertEqual(gate.status, "failed")
            self.assertEqual(gate.provider, "media_quality_gate")

    def test_degraded_gate_drops_failed_artifacts_and_redacts_sensitive_paths(self):
        quality = importlib.import_module("scripts.media_pipeline.quality")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            try:
                from PIL import Image
            except ImportError:
                self.skipTest("Pillow unavailable")
            valid_path = root / "valid.png"
            Image.new("RGB", (20, 20), "#29466d").save(valid_path, format="PNG")
            valid = replace(
                Artifact.from_file("product_capture_image", valid_path, "local", "fixture"),
                metadata={"viewport": [20, 20], "cloudUpload": False},
            )
            sensitive_dir = root / "cookies"
            sensitive_dir.mkdir()
            sensitive_path = sensitive_dir / "capture.png"
            Image.new("RGB", (20, 20), "#29466d").save(sensitive_path, format="PNG")
            sensitive = replace(
                Artifact.from_file("product_capture_image", sensitive_path, "local", "fixture"),
                metadata={"viewport": [20, 20], "cloudUpload": False},
            )
            report = quality.build_quality_report({"capture": StageResult.ready("local", [sensitive])})
            self.assertEqual(report["artifacts"][0]["path"], "[redacted-sensitive-path]")
            self.assertNotIn("cookies", json.dumps(report, ensure_ascii=False))

            with mock.patch.object(
                quality,
                "build_quality_report",
                return_value={"status": "standard_ready", "warnings": [], "blockers": []},
            ), mock.patch.object(
                quality,
                "_inspect_artifact",
                side_effect=[{"passed": False}, {"passed": True}],
            ):
                gate = quality.run_quality_gate(
                    {"capture": StageResult(status="degraded", provider="local", artifacts=(sensitive, valid))}
                )
            self.assertEqual(gate.status, "degraded")
            self.assertEqual(gate.artifacts, (valid,))

            leaky = replace(valid, provider="Bearer LEAK_TOKEN", source="https://example.test/?token=LEAK_QUERY")
            leaky_stage = StageResult(
                status="failed",
                provider="Bearer STAGE_TOKEN",
                error_code="err_LEAK_ERROR",
                artifacts=(leaky,),
            )
            leaky_report = quality.build_quality_report({"failed": leaky_stage})
            rendered = json.dumps(leaky_report, ensure_ascii=False)
            self.assertNotIn("LEAK_TOKEN", rendered)
            self.assertNotIn("LEAK_QUERY", rendered)
            self.assertNotIn("STAGE_TOKEN", rendered)
            self.assertNotIn("LEAK_ERROR", rendered)
            with mock.patch.object(
                quality,
                "build_quality_report",
                return_value={"status": "standard_ready", "warnings": [], "blockers": [], "artifacts": []},
            ), mock.patch.object(quality, "_inspect_artifact", return_value={"passed": True}):
                failed_gate = quality.run_quality_gate({"failed": leaky_stage}, target="standard")
            self.assertEqual(failed_gate.artifacts, ())
            failed_gate_draft = quality.run_quality_gate({"failed": leaky_stage}, target="draft")
            self.assertEqual(failed_gate_draft.artifacts, ())

            mixed_gate = quality.run_quality_gate(
                {
                    "degraded": StageResult(status="degraded", provider="local"),
                    "failed": StageResult(status="failed", provider="local"),
                }
            )
            self.assertEqual(mixed_gate.status, "failed")

            unknown_path = root / "unknown.bin"
            unknown_path.write_bytes(b"unknown")
            unknown = Artifact.from_file("unknown_artifact", unknown_path, "local", "fixture")
            unknown_gate = quality.run_quality_gate(
                {"capture": StageResult(status="degraded", provider="local", artifacts=(unknown,))},
                target="standard",
            )
            self.assertEqual(unknown_gate.artifacts, ())

            ai_scene = replace(
                Artifact.from_file("ai_scene", valid_path, "comfyui_flux_local", "flux-workflow"),
                metadata={"aiGenerated": True, "cloudUpload": False},
            )
            ai_report = quality.build_quality_report({"scene": StageResult.ready("comfyui_flux_local", [ai_scene])})
            self.assertEqual(ai_report["evidence"]["aiScenes"][0]["type"], "ai_scene")


class WorkflowIntegrationTest(unittest.TestCase):
    def test_skill_entry_defaults_to_bilingual_root_and_professional_media(self):
        skill_entry = importlib.import_module("scripts.skill_entry")
        argv = [
            "skill_entry.py",
            "--link",
            "https://example.com/product",
            "--link-mode",
            "product",
        ]
        with mock.patch.object(sys, "argv", argv):
            args = skill_entry.parse_args()

        self.assertEqual(args.out_dir, "./promotion-output_推广输出")
        self.assertEqual(args.media_quality, "professional")
        self.assertEqual(args.presenter, "none")
        self.assertFalse(args.allow_cloud_media)

    def test_product_batch_run_uses_bilingual_runs_directory(self):
        product_batch = importlib.import_module("scripts.product_batch_runner")

        run_dir = product_batch.product_run_dir(
            Path("C:/output"), 1, "ENHE API", now="20260723-120000"
        )

        self.assertEqual(
            run_dir,
            Path("C:/output/runs_运行记录/20260723-120000-001-enhe-api"),
        )

    def test_final_readiness_discovers_bilingual_run_reports(self):
        readiness = importlib.import_module("scripts.final_capability_readiness")
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp)
            report = out_dir / "runs_运行记录" / "20260723-120000-enhe" / "reports" / "promotion-manager" / "publish-readiness" / "publish-readiness.json"
            report.parent.mkdir(parents=True)
            report.write_text("{}", encoding="utf-8")
            with mock.patch.object(sys, "argv", ["final_capability_readiness.py", "--out-dir", str(out_dir)]):
                args = readiness.parse_args()

            sources = readiness.load_sources(args, out_dir)

        self.assertEqual(sources["publishReadinessPaths"], [report])

    def test_workflow_defaults_to_professional_media_and_bilingual_root(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        argv = ["run_promotion_workflow.py", "--product-url", "https://example.com/product"]
        with mock.patch.object(sys, "argv", argv):
            args = workflow.parse_args()

        self.assertEqual(args.out_dir, "./promotion-output_推广输出")
        self.assertEqual(args.media_quality, "professional")
        self.assertEqual(args.comfyui_url, "http://127.0.0.1:8188")

    def test_media_flags_propagate_through_default_workflow_commands(self):
        common = [
            "--media-quality",
            "professional",
            "--brand-logo",
            "C:/brand/logo.png",
            "--comfyui-url",
            "http://127.0.0.1:8188",
            "--presenter",
            "none",
            "--presenter-asset",
            "C:/brand/presenter.png",
            "--portrait-authorized",
            "--allow-cloud-media",
        ]

        final_runner = importlib.import_module("scripts.final_capability_runner")
        with mock.patch.object(sys, "argv", ["final_capability_runner.py", *common]):
            final_args = final_runner.parse_args()
        batch_command = [sys.executable, "product_batch_runner.py"]
        final_runner.append_common_batch_args(batch_command, final_args)
        self.assert_media_flags(batch_command)

        product_batch = importlib.import_module("scripts.product_batch_runner")
        with mock.patch.object(sys, "argv", ["product_batch_runner.py", *common]):
            batch_args = product_batch.parse_args()
        cycle_command = product_batch.build_cycle_command(
            batch_args,
            {"product": {}, "id": "enhe"},
            {"flag": "--product-url", "value": "https://example.com/product"},
            Path("C:/output/run"),
        )
        self.assert_media_flags(cycle_command)

        scripts_path = str(REPO_ROOT / "scripts")
        with mock.patch.object(sys, "path", [scripts_path, *sys.path]):
            promotion_cycle = importlib.import_module("scripts.promotion_cycle_runner")
        with mock.patch.object(sys, "argv", ["promotion_cycle_runner.py", "--product-url", "https://example.com/product", *common]):
            cycle_args = promotion_cycle.parse_args()
        workflow_command = promotion_cycle.build_workflow_command(
            cycle_args, Path("C:/output/run")
        )
        self.assert_media_flags(workflow_command)

        real_playbook = importlib.import_module("scripts.real_run_playbook")
        with mock.patch.object(sys, "argv", ["real_run_playbook.py", *common]):
            playbook_args = real_playbook.parse_args()
        final_command = real_playbook.final_capability_command(
            playbook_args, Path("C:/output")
        )
        self.assert_media_flags(final_command)

    def test_professional_media_branch_invokes_local_pipeline(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp)
            content_dir = out_dir / "generated-content_生成内容"
            publish_dir = out_dir / "publish-packs_发布包"
            content_dir.mkdir(parents=True)
            publish_dir.mkdir(parents=True)
            content_path = content_dir / "enhe-platform-content.json"
            publish_path = publish_dir / "enhe-publish-pack.json"
            content_path.write_text(
                json.dumps(
                    {
                        "youtube": {
                            "title": "ENHE product demo",
                            "description": "Turn one product page into campaign assets.",
                            "voiceover": "See how ENHE turns one product page into professional campaign assets.",
                            "coverText": "One link to a full campaign",
                        }
                    }
                ),
                encoding="utf-8",
            )
            publish_path.write_text("[]", encoding="utf-8")
            logo = out_dir / "logo.png"
            logo.write_bytes(PNG_BYTES)
            args = SimpleNamespace(
                skip_video=False,
                media_quality="professional",
                language="zh-CN",
                platforms="youtube,xiaohongshu",
                brand_logo=str(logo),
                comfyui_url="http://127.0.0.1:8188",
                presenter="none",
                presenter_asset="",
                portrait_authorized=False,
                allow_cloud_media=False,
            )
            product = {"name": "ENHE", "url": "https://example.com/product", "platforms": ["youtube", "xiaohongshu"]}
            captured = []

            def fake_run(name, command, check=False):
                captured.append((name, command, check))
                reports = out_dir / "reports_报告"
                videos = out_dir / "videos_视频"
                reports.mkdir()
                videos.mkdir()
                video = videos / "professional-demo.mp4"
                video.write_bytes(b"video")
                (reports / "media-quality-report.json").write_text(
                    json.dumps({"status": "professional_ready", "blockers": [], "missingFamilies": []}),
                    encoding="utf-8",
                )
                (reports / "media-manifest.json").write_text(
                    json.dumps({"status": "complete"}), encoding="utf-8"
                )
                return {"command": command, "exitCode": 0, "stdoutTail": "", "stderrTail": ""}

            with mock.patch.object(workflow, "run_command", side_effect=fake_run):
                result = workflow.run_professional_media(args, product, out_dir, [])

            media_input = json.loads(
                (out_dir / "generated-content_生成内容" / "professional-media-input.json").read_text(encoding="utf-8")
            )

        self.assertEqual(result["status"], "professional_ready")
        self.assertEqual(len(result["videos"]), 1)
        self.assertTrue(media_input["narration"])
        self.assertEqual(media_input["sourcePlatform"], "youtube")
        self.assertEqual(captured[0][0], "professional_media_pipeline")
        command = captured[0][1]
        self.assertIn("--quality-target", command)
        self.assertIn("professional", command)
        self.assertIn("--brand-logo", command)
        self.assertIn("--comfyui-url", command)
        self.assertNotIn("--allow-cloud-media", command)

    def test_professional_media_requires_explicit_brand_logo(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        args = SimpleNamespace(skip_video=False, brand_logo="")

        result = workflow.run_professional_media(
            args,
            {"name": "ENHE", "url": "https://example.com/product", "platforms": ["youtube"]},
            Path("C:/output"),
            [],
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reasonCode"], "brand_logo_required")

    def test_professional_media_does_not_reuse_stale_success_after_subprocess_failure(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp)
            content_dir = out_dir / "generated-content_生成内容"
            publish_dir = out_dir / "publish-packs_发布包"
            reports = out_dir / "reports_报告"
            videos = out_dir / "videos_视频"
            content_dir.mkdir(parents=True)
            publish_dir.mkdir(parents=True)
            reports.mkdir()
            videos.mkdir()
            (content_dir / "enhe-platform-content.json").write_text(
                json.dumps(
                    {
                        "youtube": {
                            "title": "ENHE",
                            "description": "Product campaign",
                            "voiceover": "Generate professional campaign media.",
                        }
                    }
                ),
                encoding="utf-8",
            )
            (publish_dir / "enhe-publish-pack.json").write_text("[]", encoding="utf-8")
            (reports / "media-quality-report.json").write_text(
                json.dumps(
                    {
                        "status": "professional_ready",
                        "blockers": [],
                        "missingFamilies": [],
                    }
                ),
                encoding="utf-8",
            )
            (videos / "stale-professional.mp4").write_bytes(b"stale")
            logo = out_dir / "logo.png"
            logo.write_bytes(PNG_BYTES)
            args = SimpleNamespace(
                skip_video=False,
                media_quality="professional",
                language="zh-CN",
                platforms="youtube",
                brand_logo=str(logo),
                comfyui_url="http://127.0.0.1:8188",
                presenter="none",
                presenter_asset="",
                portrait_authorized=False,
                allow_cloud_media=False,
                video_platforms="auto",
            )
            product = {
                "name": "ENHE",
                "url": "https://example.com/product",
                "platforms": ["youtube"],
            }
            failed_step = {
                "command": ["python", "professional_media_pipeline.py"],
                "exitCode": 1,
                "stdoutTail": "",
                "stderrTail": "render failed",
            }

            with mock.patch.object(workflow, "run_command", return_value=failed_step):
                result = workflow.run_professional_media(args, product, out_dir, [])

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["videos"], [])
        with self.assertRaises(SystemExit):
            workflow.enforce_professional_media_result(args, result)

    def test_professional_default_fails_closed_below_professional_ready(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        args = SimpleNamespace(media_quality="professional", skip_video=False)

        with self.assertRaises(SystemExit):
            workflow.enforce_professional_media_result(args, {"status": "standard_ready"})

        workflow.enforce_professional_media_result(args, {"status": "professional_ready"})
        workflow.enforce_professional_media_result(
            SimpleNamespace(media_quality="draft", skip_video=False),
            {"status": "blocked"},
        )

    def test_professional_video_renders_and_binds_each_platform_aspect(self):
        from scripts.media_pipeline.orchestrator import MediaOrchestrator

        calls = []
        with tempfile.TemporaryDirectory() as temp:
            paths = new_run_paths(Path(temp), "ENHE", now="20260723-120000").create()

            def artifact(name, artifact_type):
                path = paths.source_assets / name
                path.write_bytes(b"asset")
                return Artifact.from_file(artifact_type, path, "fixture", "fixture")

            def fake_video_provider(data, output_path, _workspace):
                calls.append((data["width"], data["height"], tuple(data["platforms"])))
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(b"video")
                return StageResult.ready(
                    "fixture",
                    [Artifact.from_file("professional_product_demo_video", output_path, "fixture", "fixture")],
                    diagnostics={"captionTimingValid": True},
                )

            job = MediaJob(
                run_id=paths.root.name,
                product_name="ENHE",
                source_url="https://example.com/product",
                language="zh-CN",
                target_platforms=("youtube", "douyin", "github"),
                quality_target="professional",
                aspect_ratios=("16:9", "9:16", "1:1"),
                duration_range=(20, 60),
                providers={},
                allow_cloud_media=False,
                product_data_path=str(paths.source_assets / "content.json"),
                brand_assets=(),
                generated_content_path=str(paths.source_assets / "content.json"),
                capture_plan_path="",
            )
            stages = {
                "capture": StageResult.ready("fixture", [artifact(f"capture-{index}.png", "product_capture_image") for index in range(3)]),
                "scenes": StageResult.ready("fixture", [artifact(f"scene-{index}.png", "ai_scene") for index in range(2)]),
                "voiceover": StageResult.ready("fixture", [artifact("voice.wav", "voiceover_audio")]),
            }
            orchestrator = MediaOrchestrator(video_provider=fake_video_provider)

            result = orchestrator._render_video(job, paths, stages, {})

            pack = paths.publish_packs / "pack.json"
            pack.write_text(
                json.dumps([{"platform": "youtube"}, {"platform": "douyin"}, {"platform": "github"}]),
                encoding="utf-8",
            )
            orchestrator._update_publish_pack(
                pack,
                job,
                paths,
                {
                    "video": result,
                    "visuals": StageResult.ready("fixture", []),
                    "quality": StageResult(status="ready", provider="fixture", diagnostics={"status": "professional_ready"}),
                },
            )
            updated = json.loads(pack.read_text(encoding="utf-8"))

        self.assertEqual(
            calls,
            [
                (1920, 1080, ("youtube",)),
                (1080, 1920, ("douyin",)),
                (1080, 1080, ("github",)),
            ],
        )
        self.assertEqual(len({item["video"]["path"] for item in updated}), 3)
        self.assertTrue(result.diagnostics["captionTimingValid"])
        self.assertTrue(
            all(artifact.metadata["captionTimingValid"] for artifact in result.artifacts)
        )

    def test_skill_entry_returns_failure_only_for_internal_blocked_status(self):
        skill_entry = importlib.import_module("scripts.skill_entry")

        self.assertEqual(skill_entry.entry_exit_code({"status": "blocked"}), 1)
        self.assertEqual(skill_entry.entry_exit_code({"status": "error"}), 1)
        self.assertEqual(
            skill_entry.entry_exit_code(
                {"status": "partial_ready_blocked_by_platform_or_safety_limits"}
            ),
            0,
        )
        self.assertEqual(skill_entry.entry_exit_code({"status": "professional_ready"}), 0)

    def test_professional_workflow_routes_content_and_publish_pack_to_bilingual_dirs(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        args = SimpleNamespace(media_quality="professional", skip_video=False)
        out_dir = Path("C:/output/run")

        self.assertEqual(
            workflow.generated_content_dir(args, out_dir),
            out_dir / "generated-content_生成内容",
        )
        self.assertEqual(
            workflow.publish_pack_dir(args, out_dir),
            out_dir / "publish-packs_发布包",
        )

        command = []
        with mock.patch.object(workflow, "run_command", side_effect=lambda _name, value: command.extend(value) or {}):
            workflow.run_promotion_manager(
                SimpleNamespace(
                    language="zh-CN",
                    media_quality="professional",
                    skip_video=False,
                ),
                {
                    "name": "ENHE",
                    "url": "https://example.com/product",
                    "audience": ["creator"],
                    "painPoints": ["slow content"],
                    "valueProposition": "one link to campaign assets",
                    "pricing": "19",
                    "goal": "leads",
                    "platforms": ["youtube"],
                },
                out_dir,
                [],
            )

        self.assertEqual(
            Path(command[command.index("--generated-content-dir") + 1]),
            out_dir / "generated-content_生成内容",
        )
        self.assertEqual(
            Path(command[command.index("--publish-pack-dir") + 1]),
            out_dir / "publish-packs_发布包",
        )

    def test_explicit_draft_workflow_keeps_legacy_content_paths(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        args = SimpleNamespace(media_quality="draft", skip_video=False)
        out_dir = Path("C:/output/run")

        self.assertEqual(
            workflow.generated_content_dir(args, out_dir),
            out_dir / "reports/promotion-manager/generated-content",
        )
        self.assertEqual(
            workflow.publish_pack_dir(args, out_dir),
            out_dir / "reports/promotion-manager/publish-packs",
        )

    def test_direct_professional_workflow_allocates_a_unique_bilingual_run(self):
        workflow = importlib.import_module("scripts.run_promotion_workflow")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = SimpleNamespace(
                out_dir=str(root),
                media_quality="professional",
                skip_video=False,
                product_name="ENHE",
                product_url="https://example.com/product",
                browser_url="",
                html_file="",
                text_file="",
                structured_json="",
            )

            run_dir = workflow.resolve_workflow_out_dir(args)

        self.assertEqual(run_dir.parent.name, RUNS_DIR)
        self.assertTrue(run_dir.name.endswith("-enhe"))

    def test_professional_compatibility_wrappers_accept_authoritative_inputs(self):
        render_video = importlib.import_module("scripts.render_video")
        with mock.patch.object(
            sys,
            "argv",
            [
                "render_video.py",
                "--media-quality",
                "professional",
                "--media-job",
                "C:/run/reports_报告/media-job.json",
            ],
        ):
            render_args = render_video.parse_args()
        self.assertEqual(render_args.media_quality, "professional")
        self.assertEqual(render_args.media_job, "C:/run/reports_报告/media-job.json")
        self.assertIsNone(render_args.content_json)

        media_assets = importlib.import_module("scripts.media_asset_pack")
        with mock.patch.object(
            sys,
            "argv",
            [
                "media_asset_pack.py",
                "--professional-manifest",
                "C:/run/reports_报告/media-manifest.json",
                "--publish-pack",
                "C:/run/publish-packs_发布包/enhe-publish-pack.json",
            ],
        ):
            asset_args = media_assets.parse_args()
        self.assertEqual(
            asset_args.professional_manifest,
            "C:/run/reports_报告/media-manifest.json",
        )
        self.assertIsNone(asset_args.content_json)

    def test_professional_manifest_uses_referenced_quality_report_status(self):
        media_assets = importlib.import_module("scripts.media_asset_pack")
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            reports = run_dir / "reports_报告"
            reports.mkdir()
            quality_report = reports / "media-quality-report.json"
            quality_report.write_text(
                json.dumps(
                    {
                        "status": "professional_ready",
                        "target": "professional",
                    }
                ),
                encoding="utf-8",
            )
            video = run_dir / "videos_视频" / "youtube.mp4"
            video.parent.mkdir()
            video.write_bytes(b"video")
            manifest = reports / "media-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "status": "complete",
                        "qualityReport": str(quality_report),
                        "artifacts": [
                            {
                                "type": "professional_product_demo_video",
                                "path": str(video),
                                "metadata": {"platforms": ["youtube"]},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            publish_pack = run_dir / "publish-packs_发布包" / "enhe-publish-pack.json"
            publish_pack.parent.mkdir()
            publish_pack.write_text(
                json.dumps([{"platform": "youtube"}]),
                encoding="utf-8",
            )

            media_assets.attach_professional_manifest(manifest, publish_pack)
            updated = json.loads(publish_pack.read_text(encoding="utf-8"))[0]

        self.assertEqual(updated["mediaQuality"]["status"], "professional_ready")
        self.assertEqual(
            updated["mediaQuality"]["report"],
            str(quality_report.resolve()),
        )

    def test_professional_manifest_falls_back_to_partial_ready_for_bad_quality_report(self):
        media_assets = importlib.import_module("scripts.media_asset_pack")
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            reports = run_dir / "reports_报告"
            reports.mkdir()
            quality_report = reports / "media-quality-report.json"
            quality_report.write_text(
                json.dumps({"status": "complete"}),
                encoding="utf-8",
            )
            manifest = reports / "media-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "status": "complete",
                        "qualityReport": str(quality_report),
                        "artifacts": [],
                    }
                ),
                encoding="utf-8",
            )
            publish_pack = run_dir / "publish-packs_发布包" / "enhe-publish-pack.json"
            publish_pack.parent.mkdir()
            publish_pack.write_text(
                json.dumps([{"platform": "youtube"}]),
                encoding="utf-8",
            )

            media_assets.attach_professional_manifest(manifest, publish_pack)
            updated = json.loads(publish_pack.read_text(encoding="utf-8"))[0]

        self.assertEqual(updated["mediaQuality"]["status"], "partial_ready")

    def test_professional_manifest_falls_back_to_partial_ready_when_quality_report_is_missing(self):
        media_assets = importlib.import_module("scripts.media_asset_pack")
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            reports = run_dir / "reports_报告"
            reports.mkdir()
            quality_report = reports / "missing-quality-report.json"
            manifest = reports / "media-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "status": "complete",
                        "qualityReport": str(quality_report),
                        "artifacts": [],
                    }
                ),
                encoding="utf-8",
            )
            publish_pack = run_dir / "publish-packs_发布包" / "enhe-publish-pack.json"
            publish_pack.parent.mkdir()
            publish_pack.write_text(
                json.dumps([{"platform": "youtube"}]),
                encoding="utf-8",
            )

            media_assets.attach_professional_manifest(manifest, publish_pack)
            updated = json.loads(publish_pack.read_text(encoding="utf-8"))[0]

        self.assertEqual(updated["mediaQuality"]["status"], "partial_ready")
        self.assertEqual(
            updated["mediaQuality"]["report"],
            str(quality_report.resolve()),
        )

    def test_render_video_professional_wrapper_delegates_authoritative_media_job(self):
        render_video = importlib.import_module("scripts.render_video")
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            reports = run_dir / "reports_报告"
            reports.mkdir()
            content = run_dir / "generated-content_生成内容" / "enhe.json"
            content.parent.mkdir()
            content.write_text("{}", encoding="utf-8")
            capture_plan = reports / "capture-plan.json"
            capture_plan.write_text("{}", encoding="utf-8")
            logo = run_dir / "source-assets_源素材" / "logo.png"
            logo.parent.mkdir()
            logo.write_bytes(PNG_BYTES)
            publish_pack = (
                run_dir / "publish-packs_发布包" / "enhe-publish-pack.json"
            )
            publish_pack.parent.mkdir()
            publish_pack.write_text("[]", encoding="utf-8")
            media_job = reports / "media-job.json"
            media_job.write_text(
                json.dumps(
                    {
                        "sourceUrl": "https://example.com/product",
                        "productName": "ENHE",
                        "generatedContentPath": str(content),
                        "language": "zh-CN",
                        "targetPlatforms": ["youtube", "douyin"],
                        "qualityTarget": "professional",
                        "brandAssets": [str(logo)],
                        "capturePlanPath": str(capture_plan),
                        "providers": {"comfyuiUrl": "http://127.0.0.1:8188"},
                        "allowCloudMedia": True,
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "render_video.py",
                        "--media-quality",
                        "professional",
                        "--media-job",
                        str(media_job),
                    ],
                ),
                mock.patch.object(
                    render_video.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=0),
                ) as run,
            ):
                render_video.main()

        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "professional_media_pipeline.py")
        self.assertEqual(
            Path(command[command.index("--run-dir") + 1]),
            run_dir.resolve(),
        )
        self.assertEqual(
            command[command.index("--platforms") + 1],
            "youtube,douyin",
        )
        self.assertEqual(
            Path(command[command.index("--publish-pack") + 1]),
            publish_pack,
        )
        self.assertIn("--allow-cloud-media", command)

    def test_media_asset_professional_wrapper_updates_pack_and_writes_report(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            reports = run_dir / "reports_报告"
            reports.mkdir()
            quality_report = reports / "media-quality-report.json"
            quality_report.write_text(
                json.dumps(
                    {
                        "status": "professional_ready",
                        "target": "professional",
                    }
                ),
                encoding="utf-8",
            )
            cover = run_dir / "covers_封面" / "youtube" / "cover.png"
            cover.parent.mkdir(parents=True)
            cover.write_bytes(PNG_BYTES)
            manifest = reports / "media-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "status": "complete",
                        "qualityReport": str(quality_report),
                        "artifacts": [
                            {
                                "type": "cover_image",
                                "path": str(cover),
                                "metadata": {"platforms": ["youtube"]},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            publish_pack = (
                run_dir / "publish-packs_发布包" / "enhe-publish-pack.json"
            )
            publish_pack.parent.mkdir()
            publish_pack.write_text(
                json.dumps([{"platform": "youtube"}]),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "media_asset_pack.py"),
                    "--professional-manifest",
                    str(manifest),
                    "--publish-pack",
                    str(publish_pack),
                    "--out-dir",
                    str(run_dir),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            updated = json.loads(publish_pack.read_text(encoding="utf-8"))[0]
            wrapper_report = json.loads(
                (
                    run_dir
                    / "reports"
                    / "promotion-manager"
                    / "media-assets"
                    / "media-asset-pack.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(updated["mediaQuality"]["status"], "professional_ready")
        self.assertEqual(Path(updated["cover"]["path"]), cover)
        self.assertEqual(wrapper_report["summary"]["attachedAssets"], 1)

    def test_public_runners_return_nonzero_only_for_internal_failures(self):
        scripts_path = str(REPO_ROOT / "scripts")
        with mock.patch.object(sys, "path", [scripts_path, *sys.path]):
            promotion_cycle = importlib.import_module("scripts.promotion_cycle_runner")
            product_batch = importlib.import_module("scripts.product_batch_runner")
            final_runner = importlib.import_module("scripts.final_capability_runner")

        self.assertEqual(
            promotion_cycle.report_exit_code({"status": "workflow_failed"}), 1
        )
        self.assertEqual(promotion_cycle.report_exit_code({"status": "ready"}), 0)
        self.assertEqual(product_batch.report_exit_code({"status": "blocked"}), 1)
        self.assertEqual(
            product_batch.report_exit_code(
                {
                    "status": "partial_ready",
                    "summary": {"failedPromotionCycles": 1},
                }
            ),
            1,
        )
        self.assertEqual(
            product_batch.report_exit_code(
                {
                    "status": "partial_ready",
                    "summary": {"failedPromotionCycles": 0},
                }
            ),
            0,
        )
        self.assertEqual(final_runner.report_exit_code({"status": "blocked"}), 1)
        self.assertEqual(
            final_runner.report_exit_code({"status": "partial_ready_with_errors"}),
            1,
        )
        self.assertEqual(
            final_runner.report_exit_code({"status": "partial_ready"}), 0
        )

    def test_promotion_cycle_cli_exit_codes_follow_actual_automation_status(self):
        scripts_path = str(REPO_ROOT / "scripts")
        with mock.patch.object(sys, "path", [scripts_path, *sys.path]):
            runner = importlib.import_module("scripts.promotion_cycle_runner")

        cases = (
            (
                {"status": "error"},
                {"status": "skipped"},
                {"status": "skipped"},
                1,
            ),
            (
                {"status": "ready"},
                {"status": "skipped"},
                {"status": "waiting_real_data"},
                0,
            ),
        )
        for workflow, metrics, next_round, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                skipped = {"status": "skipped"}
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "promotion_cycle_runner.py",
                            "--workflow-manifest",
                            str(Path(temp) / "workflow-manifest.json"),
                            "--out-dir",
                            temp,
                        ],
                    ),
                    mock.patch.object(
                        runner, "prepare_workflow", return_value=workflow
                    ),
                    mock.patch.object(
                        runner, "run_publish_queue", return_value=skipped
                    ),
                    mock.patch.object(
                        runner, "run_published_items", return_value=skipped
                    ),
                    mock.patch.object(
                        runner,
                        "run_post_publish_metrics_capture",
                        return_value=skipped,
                    ),
                    mock.patch.object(
                        runner, "run_comment_evidence_capture", return_value=skipped
                    ),
                    mock.patch.object(
                        runner, "run_business_attribution", return_value=skipped
                    ),
                    mock.patch.object(
                        runner, "run_metrics_recovery", return_value=metrics
                    ),
                    mock.patch.object(
                        runner,
                        "run_next_round_optimization",
                        return_value=next_round,
                    ),
                ):
                    with self.assertRaises(SystemExit) as raised:
                        runner.main()

                self.assertEqual(raised.exception.code, expected)

    def test_product_batch_cli_keeps_waiting_real_data_zero_and_failures_nonzero(self):
        runner = importlib.import_module("scripts.product_batch_runner")
        cases = (
            (
                [
                    {
                        "status": "error",
                        "multiQueryViralDiscovery": {"status": "skipped"},
                        "nextRoundOptimization": {"status": "skipped"},
                    }
                ],
                1,
            ),
            (
                [
                    {
                        "status": "ready",
                        "multiQueryViralDiscovery": {"status": "skipped"},
                        "nextRoundOptimization": {"status": "waiting_real_data"},
                    }
                ],
                0,
            ),
        )
        for runs, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "product_batch_runner.py",
                            "--url",
                            "https://example.com/product",
                            "--out-dir",
                            temp,
                        ],
                    ),
                    mock.patch.object(
                        runner,
                        "run_product_url_discovery",
                        return_value={"status": "skipped"},
                    ),
                    mock.patch.object(
                        runner,
                        "run_product_url_reader",
                        return_value={"status": "ready", "records": []},
                    ),
                    mock.patch.object(
                        runner, "run_promotion_cycles", return_value=runs
                    ),
                    mock.patch.object(
                        runner, "attach_multi_query_viral_discovery"
                    ),
                ):
                    with self.assertRaises(SystemExit) as raised:
                        runner.main()

                self.assertEqual(raised.exception.code, expected)

    def test_final_capability_cli_keeps_partial_ready_zero_and_failures_nonzero(self):
        runner = importlib.import_module("scripts.final_capability_runner")
        cases = (
            ({"status": "blocked", "promotionRuns": [], "summary": {}}, 1),
            ({"status": "partial_ready", "promotionRuns": [], "summary": {}}, 0),
        )
        for batch, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                empty = []
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        ["final_capability_runner.py", "--out-dir", temp],
                    ),
                    mock.patch.object(
                        runner, "run_product_batch", return_value=batch
                    ),
                    mock.patch.object(
                        runner, "run_publish_readiness", return_value=empty
                    ),
                    mock.patch.object(
                        runner, "run_publish_setup_assistant", return_value=empty
                    ),
                    mock.patch.object(
                        runner, "run_real_evidence_setup", return_value=empty
                    ),
                    mock.patch.object(
                        runner, "run_browser_publish_assistant", return_value=empty
                    ),
                    mock.patch.object(
                        runner, "run_browser_form_fill", return_value=empty
                    ),
                    mock.patch.object(
                        runner, "run_launch_unlock_pack", return_value=empty
                    ),
                    mock.patch.object(runner, "run_audits", return_value={}),
                    mock.patch.object(
                        runner, "collect_cycle_evidence", return_value=empty
                    ),
                    mock.patch.object(
                        runner,
                        "run_final_readiness_matrix",
                        return_value={"status": "waiting_real_data"},
                    ),
                ):
                    with self.assertRaises(SystemExit) as raised:
                        runner.main()

                self.assertEqual(raised.exception.code, expected)

    def test_orchestrator_writes_authoritative_media_job_and_capture_plan(self):
        from scripts.media_pipeline.orchestrator import MediaOrchestrator

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = new_run_paths(root, "ENHE", now="20260723-120000")
            job = MediaJob(
                run_id=paths.root.name,
                product_name="ENHE",
                source_url="https://example.com/product",
                language="zh-CN",
                target_platforms=("youtube",),
                quality_target="professional",
                aspect_ratios=("16:9",),
                duration_range=(20, 60),
                providers={},
                allow_cloud_media=False,
                product_data_path="C:/content.json",
                brand_assets=("C:/logo.png",),
                generated_content_path="C:/content.json",
                capture_plan_path="",
            )
            capture_plan = {
                "sourceUrl": "https://example.com/product",
                "shots": [{"url": "https://example.com/product", "action": "none"}],
            }
            orchestrator = MediaOrchestrator()

            orchestrator._write_authoritative_inputs(job, paths, capture_plan)

            media_job = json.loads(
                (paths.reports / "media-job.json").read_text(encoding="utf-8")
            )
            saved_plan = json.loads(
                (paths.reports / "capture-plan.json").read_text(encoding="utf-8")
            )

        self.assertEqual(media_job["runId"], job.run_id)
        self.assertEqual(media_job["qualityTarget"], "professional")
        self.assertEqual(saved_plan, capture_plan)

    def test_quality_cleanup_preserves_authoritative_inputs_and_stage_receipts(self):
        from scripts.media_pipeline.orchestrator import MediaOrchestrator

        with tempfile.TemporaryDirectory() as temp:
            paths = new_run_paths(
                Path(temp), "ENHE", now="20260723-120000"
            ).create()
            media_job = paths.reports / "media-job.json"
            capture_plan = paths.reports / "capture-plan.json"
            stage_receipt = paths.reports / "stage-receipts" / "capture.json"
            quality_report = paths.reports / "media-quality-report.json"
            for path in (media_job, capture_plan, stage_receipt, quality_report):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")

            MediaOrchestrator()._clear_stage_output("quality", paths)

            self.assertTrue(media_job.exists())
            self.assertTrue(capture_plan.exists())
            self.assertTrue(stage_receipt.exists())
            self.assertFalse(quality_report.exists())

    def test_orchestrator_moves_detail_artifacts_to_detail_images_directory(self):
        from scripts.media_pipeline.orchestrator import MediaOrchestrator

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = new_run_paths(root, "ENHE", now="20260723-120000").create()
            cover = paths.covers / "youtube" / "youtube-cover.png"
            detail = paths.covers / "youtube" / "youtube-detail-01.png"
            contact = paths.covers / "youtube" / "youtube-contact-sheet.png"
            for path in (cover, detail, contact):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(PNG_BYTES)
            result = StageResult.ready(
                "fixture",
                [
                    Artifact.from_file("cover_image", cover, "fixture", "fixture"),
                    Artifact.from_file("detail_image", detail, "fixture", "fixture"),
                    Artifact.from_file("contact_sheet", contact, "fixture", "fixture"),
                ],
            )

            moved = MediaOrchestrator()._separate_visual_artifacts(
                result, paths, "youtube"
            )
            detail_artifact = next(
                artifact
                for artifact in moved.artifacts
                if artifact.type == "detail_image"
            )
            self.assertTrue(
                Path(detail_artifact.path).is_relative_to(paths.detail_images)
            )
            self.assertTrue(Path(detail_artifact.path).exists())
            self.assertTrue(cover.exists())
            self.assertTrue(contact.exists())

    def assert_media_flags(self, command):
        self.assertEqual(command[command.index("--media-quality") + 1], "professional")
        self.assertEqual(command[command.index("--brand-logo") + 1], "C:/brand/logo.png")
        self.assertEqual(command[command.index("--comfyui-url") + 1], "http://127.0.0.1:8188")
        self.assertEqual(command[command.index("--presenter") + 1], "none")
        self.assertEqual(command[command.index("--presenter-asset") + 1], "C:/brand/presenter.png")
        self.assertIn("--portrait-authorized", command)
        self.assertIn("--allow-cloud-media", command)


class ProfessionalMediaDocsTest(unittest.TestCase):
    def test_docs_explain_install_run_quality_and_cloud_boundary_in_both_languages(self):
        documents = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "README.zh-CN.md",
            REPO_ROOT / "README.en.md",
            REPO_ROOT / "SKILL.md",
        ]
        for path in documents:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for required in (
                    "professional_ready",
                    "--media-quality professional",
                    "--brand-logo",
                    "--allow-cloud-media",
                    "promotion-output_推广输出",
                    "setup_professional_media.py --install-core",
                    "setup_professional_media.py --install-comfyui",
                ):
                    self.assertIn(required, text)

    def test_formal_quick_start_commands_include_the_required_brand_logo(self):
        for filename in ("README.en.md", "README.zh-CN.md", "SKILL.md"):
            text = (REPO_ROOT / filename).read_text(encoding="utf-8")
            marker = (
                "python scripts/skill_entry.py"
                if filename == "SKILL.md"
                else "python scripts\\skill_entry.py"
            )
            self.assertIn(marker, text)
            first_block = text.split(marker, 1)[1].split("```", 1)[0]
            self.assertIn("--brand-logo", first_block, filename)


if __name__ == "__main__":
    unittest.main()

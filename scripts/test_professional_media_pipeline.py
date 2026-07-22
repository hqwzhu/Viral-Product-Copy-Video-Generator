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
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest import mock
from urllib.parse import quote

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


class MediaSecurityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

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
                        "duration": 3,
                    },
                    {
                        "id": "workflow",
                        "url": source_url,
                        "selector": "#workflow",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "duration": 4,
                    },
                    {
                        "id": "features",
                        "url": source_url,
                        "selector": "#features",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "duration": 4,
                    },
                    {
                        "id": "proof",
                        "url": source_url,
                        "selector": "#proof",
                        "action": "scroll",
                        "viewport": [1440, 900],
                        "duration": 3,
                    },
                    {
                        "id": "cta",
                        "url": source_url,
                        "selector": "#cta",
                        "action": "scroll",
                        "viewport": [1440, 900],
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
            }
            for artifact in images:
                metadata = artifact.to_dict()["metadata"]
                self.assertTrue(image_keys.issubset(metadata), metadata)
                self.assertEqual(metadata["viewport"], [1440, 900])

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


if __name__ == "__main__":
    unittest.main()

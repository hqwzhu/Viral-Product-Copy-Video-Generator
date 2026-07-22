import importlib.util
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "scripts" / "setup_professional_media.py"


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
                self.setup._download_public_file("https://example.invalid/model", destination)

        self.assertEqual(urlopen.call_count, self.setup.DOWNLOAD_ATTEMPTS)
        self.assertTrue(
            all(call.kwargs["timeout"] == self.setup.DOWNLOAD_TIMEOUT_SECONDS for call in urlopen.call_args_list)
        )
        self.assertFalse(destination.exists())
        self.assertFalse(destination.with_name("model.bin.part").exists())

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

    def test_pinned_checkout_recovers_incomplete_clone(self):
        source, expected, _wrong = self._make_git_source()
        checkout = self.root / "checkout"
        (checkout / ".git").mkdir(parents=True)
        (checkout / "stale.part").write_text("incomplete", encoding="utf-8")

        self.setup._ensure_git_checkout(str(source), checkout, expected)

        self.assertEqual(self.setup._git_head(checkout), expected)
        self.assertFalse((checkout / "stale.part").exists())

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


if __name__ == "__main__":
    unittest.main()

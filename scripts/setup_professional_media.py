#!/usr/bin/env python3
"""Plan, inspect, and explicitly install the pinned local media runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_REFERENCE = REPO_ROOT / "references" / "professional-media-runtime.json"
PYTHON_REQUIREMENTS = REPO_ROOT / "requirements-professional-media.txt"
NODE_RUNTIME = REPO_ROOT / "tools" / "hyperframes-runtime"
MINIMUM_COMFYUI_FREE_BYTES = 25 * 1024**3
DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_TIMEOUT_SECONDS = 60


def default_runtime_root() -> Path:
    """Return the per-user runtime root without exposing environment contents."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is required to locate the media runtime")
    return Path(local_app_data) / "ENHE" / "professional-media"


def _manifest() -> dict[str, Any]:
    return json.loads(RUNTIME_REFERENCE.read_text(encoding="utf-8"))


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _command(
    action_id: str,
    scope: str,
    arguments: list[str],
    *,
    cwd: Path | None = None,
    packages: list[str] | None = None,
) -> dict[str, Any]:
    action: dict[str, Any] = {
        "id": action_id,
        "scope": scope,
        "kind": "command",
        "arguments": arguments,
    }
    if cwd is not None:
        action["cwd"] = str(cwd)
    if packages is not None:
        action["packages"] = packages
    return action


def _download(
    action_id: str,
    scope: str,
    url: str,
    destination: Path,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
    receipt: Path | None = None,
    revision: str | None = None,
) -> dict[str, Any]:
    action: dict[str, Any] = {
        "id": action_id,
        "scope": scope,
        "kind": "download",
        "arguments": [],
        "url": url,
        "destination": str(destination),
    }
    if expected_size is not None:
        action["expectedSizeBytes"] = expected_size
    if expected_sha256 is not None:
        action["expectedSha256"] = expected_sha256
    if receipt is not None:
        action["receipt"] = str(receipt)
    if revision is not None:
        action["revision"] = revision
    return action


def _git_checkout(
    action_id: str,
    scope: str,
    repository: str,
    destination: Path,
    revision: str,
) -> dict[str, Any]:
    return {
        "id": action_id,
        "scope": scope,
        "kind": "git-checkout",
        "arguments": ["git", "clone", repository, str(destination)],
        "repository": repository,
        "destination": str(destination),
        "revision": revision,
    }


def build_install_plan(
    runtime_root: Path,
    *,
    with_comfyui: bool = False,
    with_musetalk: bool = False,
) -> dict[str, Any]:
    """Build a serializable, secret-free installation plan without executing it."""
    runtime_root = Path(runtime_root)
    manifest = _manifest()
    core_venv = runtime_root / "core" / ".venv"
    core_python = _venv_python(core_venv)
    kokoro_dir = runtime_root / "models" / "kokoro"

    actions: list[dict[str, Any]] = [
        _command(
            "create-core-venv",
            "core",
            [
                "uv",
                "venv",
                "--python",
                manifest["python"]["version"],
                str(core_venv),
            ],
        ),
        _command(
            "install-core-python-packages",
            "core",
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(core_python),
                "-r",
                str(PYTHON_REQUIREMENTS),
            ],
        ),
        _command(
            "install-hyperframes-runtime",
            "core",
            ["npm", "ci", "--prefix", str(NODE_RUNTIME), "--no-audit", "--no-fund"],
            packages=["hyperframes@0.7.68", "gsap@3.13.0"],
        ),
        _command(
            "install-playwright-chromium",
            "core",
            [str(core_python), "-m", "playwright", "install", "chromium"],
        ),
    ]
    for model_file in manifest["kokoro"]["model"]["files"]:
        actions.append(
            _download(
                f"download-{model_file['filename']}",
                "core",
                model_file["url"],
                kokoro_dir / model_file["filename"],
                expected_size=model_file.get("sizeBytes"),
                expected_sha256=model_file.get("sha256"),
            )
        )

    if with_comfyui:
        comfy = manifest["comfyui"]
        flux = manifest["flux"]
        comfy_dir = runtime_root / "ComfyUI"
        comfy_venv = comfy_dir / ".venv"
        comfy_python = _venv_python(comfy_venv)
        flux_file = comfy_dir / "models" / "checkpoints" / flux["filename"]
        flux_receipt = runtime_root / "receipts" / "comfyui-flux.json"
        cuda_packages = [
            f"{name}=={version}" for name, version in comfy["cudaPackages"].items()
        ]
        actions.extend(
            [
                _git_checkout(
                    "checkout-comfyui",
                    "comfyui",
                    comfy["repository"],
                    comfy_dir,
                    comfy["revision"],
                ),
                _command(
                    "create-comfyui-venv",
                    "comfyui",
                    [
                        "uv",
                        "venv",
                        "--python",
                        manifest["python"]["version"],
                        str(comfy_venv),
                    ],
                ),
                _command(
                    "install-comfyui-cuda-packages",
                    "comfyui",
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(comfy_python),
                        "--index-url",
                        comfy["cudaIndexUrl"],
                        *cuda_packages,
                    ],
                    packages=cuda_packages,
                ),
                _command(
                    "install-comfyui-requirements",
                    "comfyui",
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(comfy_python),
                        "-r",
                        str(comfy_dir / "requirements.txt"),
                    ],
                ),
                _download(
                    "download-flux-model",
                    "comfyui",
                    flux["url"],
                    flux_file,
                    expected_size=flux.get("sizeBytes"),
                    expected_sha256=flux.get("sha256"),
                    receipt=flux_receipt,
                    revision=flux["revision"],
                ),
            ]
        )

    if with_musetalk:
        musetalk = manifest["musetalk"]
        musetalk_dir = runtime_root / "MuseTalk"
        actions.extend(
            [
                _git_checkout(
                    "checkout-musetalk",
                    "musetalk",
                    musetalk["repository"],
                    musetalk_dir,
                    musetalk["revision"],
                ),
            ]
        )

    return {
        "runtimeRoot": str(runtime_root),
        "pins": {
            "python": manifest["python"]["version"],
            "hyperframes": f"hyperframes@{manifest['hyperframes']['version']}",
            "comfyui": manifest["comfyui"]["revision"],
            "flux": manifest["flux"]["revision"],
            "musetalk": manifest["musetalk"]["revision"],
        },
        "features": {
            "comfyui": with_comfyui,
            "musetalk": with_musetalk,
        },
        "actions": actions,
    }


def _resolve_executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise FileNotFoundError(f"Required executable is not available: {name}")
    return str(Path(resolved).resolve())


def _git_head(checkout: Path) -> str | None:
    if not (checkout / ".git").is_dir():
        return None
    try:
        result = subprocess.run(
            [_resolve_executable("git"), "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _ensure_git_checkout(repository: str, destination: Path, revision: str) -> None:
    current = _git_head(destination)
    if current == revision:
        return
    if current is None and destination.exists():
        shutil.rmtree(destination)

    git = _resolve_executable("git")
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [git, "clone", repository, str(destination)],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    else:
        subprocess.run(
            [git, "-C", str(destination), "fetch", "origin", revision],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    subprocess.run(
        [git, "-C", str(destination), "checkout", "--detach", revision],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    if _git_head(destination) != revision:
        raise RuntimeError(f"Git checkout did not reach pinned revision: {revision}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assert_file_integrity(
    path: Path,
    expected_size: int | None,
    expected_sha256: str | None,
) -> tuple[int, str]:
    actual_size, actual_sha256 = path.stat().st_size, _sha256(path)
    if expected_size is not None and actual_size != expected_size:
        raise RuntimeError(
            f"File integrity check failed: expected {expected_size} bytes, got {actual_size}"
        )
    if expected_sha256 is not None and actual_sha256.lower() != expected_sha256.lower():
        raise RuntimeError(
            f"File SHA-256 check failed: expected {expected_sha256}, got {actual_sha256}"
        )
    return actual_size, actual_sha256


def _matches_integrity(
    path: Path,
    expected_size: int | None,
    expected_sha256: str | None,
) -> bool:
    if not path.is_file():
        return False
    try:
        _assert_file_integrity(path, expected_size, expected_sha256)
    except (OSError, RuntimeError):
        return False
    return True


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _valid_flux_receipt(root: Path, manifest: dict[str, Any]) -> bool:
    flux = manifest["flux"]
    model = root / "ComfyUI" / "models" / "checkpoints" / flux["filename"]
    receipt = _read_json(root / "receipts" / "comfyui-flux.json")
    if receipt is None:
        return False
    if receipt.get("revision") != flux["revision"] or receipt.get("filename") != flux["filename"]:
        return False
    if not isinstance(receipt.get("sizeBytes"), int):
        return False
    digest = receipt.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or not all(
        character in "0123456789abcdefABCDEF" for character in digest
    ):
        return False
    if receipt.get("sizeBytes") != flux.get("sizeBytes", receipt.get("sizeBytes")):
        return False
    if receipt.get("sha256") != flux.get("sha256", receipt.get("sha256")):
        return False
    return _matches_integrity(model, receipt.get("sizeBytes"), receipt.get("sha256"))


def check_runtime(runtime_root: Path | None = None) -> dict[str, Any]:
    """Validate tool presence, pinned checkout, and installed artifact integrity."""
    root = Path(runtime_root) if runtime_root is not None else default_runtime_root()
    manifest = _manifest()
    kokoro_files = {
        item["filename"]: item for item in manifest["kokoro"]["model"]["files"]
    }
    kokoro_root = root / "models" / "kokoro"
    return {
        "runtimeRoot": str(root),
        "tools": {
            "git": shutil.which("git") is not None,
            "npm": shutil.which("npm") is not None,
            "uv": shutil.which("uv") is not None,
        },
        "installed": {
            "corePython": _venv_python(root / "core" / ".venv").is_file(),
            "kokoroModel": _matches_integrity(
                kokoro_root / "kokoro-v1.0.onnx",
                kokoro_files["kokoro-v1.0.onnx"].get("sizeBytes"),
                kokoro_files["kokoro-v1.0.onnx"].get("sha256"),
            ),
            "kokoroVoices": _matches_integrity(
                kokoro_root / "voices-v1.0.bin",
                kokoro_files["voices-v1.0.bin"].get("sizeBytes"),
                kokoro_files["voices-v1.0.bin"].get("sha256"),
            ),
            "comfyui": _git_head(root / "ComfyUI") == manifest["comfyui"]["revision"],
            "flux": _valid_flux_receipt(root, manifest),
        },
    }


def _download_public_file(
    url: str,
    destination: Path,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> tuple[int, str]:
    if (expected_size is not None or expected_sha256 is not None) and _matches_integrity(
        destination, expected_size, expected_sha256
    ):
        return _assert_file_integrity(destination, expected_size, expected_sha256)
    if destination.exists():
        destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.part")
    if partial.exists():
        partial.unlink()
    request = urllib.request.Request(url, headers={"User-Agent": "ENHE-runtime-setup/1.0"})
    last_error: OSError | RuntimeError | None = None
    for attempt in range(DOWNLOAD_ATTEMPTS):
        response_size = expected_size
        response_sha256 = expected_sha256
        try:
            with urllib.request.urlopen(
                request, timeout=DOWNLOAD_TIMEOUT_SECONDS
            ) as response, partial.open("wb") as output:
                headers = getattr(response, "headers", None)
                if headers is not None:
                    linked_size = headers.get("X-Linked-Size")
                    content_length = headers.get("Content-Length")
                    if response_size is None and (linked_size or content_length):
                        response_size = int(linked_size or content_length)
                    linked_etag = headers.get("X-Linked-ETag")
                    if response_sha256 is None and linked_etag:
                        candidate = linked_etag.strip().strip('"').removeprefix("sha256:")
                        if len(candidate) == 64 and all(
                            character in "0123456789abcdefABCDEF" for character in candidate
                        ):
                            response_sha256 = candidate
                shutil.copyfileobj(response, output)
            verified = _assert_file_integrity(partial, response_size, response_sha256)
            partial.replace(destination)
            return verified
        except (OSError, RuntimeError) as error:
            last_error = error
            if attempt + 1 < DOWNLOAD_ATTEMPTS:
                time.sleep(2**attempt)
        finally:
            if partial.exists():
                partial.unlink()
    if last_error is None:
        raise RuntimeError("Download failed without an error")
    raise last_error


def _receipt_expectations(action: dict[str, Any]) -> tuple[int | None, str | None]:
    expected_size = action.get("expectedSizeBytes")
    expected_sha256 = action.get("expectedSha256")
    receipt_path = action.get("receipt")
    if (expected_size is not None or expected_sha256 is not None) or not receipt_path:
        return expected_size, expected_sha256
    receipt = _read_json(Path(receipt_path))
    if receipt is None:
        return None, None
    destination = Path(action["destination"])
    if receipt.get("revision") != action.get("revision") or receipt.get("filename") != destination.name:
        return None, None
    size = receipt.get("sizeBytes")
    digest = receipt.get("sha256")
    if not isinstance(size, int) or not isinstance(digest, str) or len(digest) != 64:
        return None, None
    return size, digest


def _atomic_write_json(destination: Path, value: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.part")
    try:
        partial.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        partial.replace(destination)
    finally:
        if partial.exists():
            partial.unlink()


def _execute_action(action: dict[str, Any]) -> None:
    kind = action["kind"]
    if kind == "command":
        arguments = list(action["arguments"])
        arguments[0] = _resolve_executable(arguments[0])
        subprocess.run(
            arguments,
            cwd=action.get("cwd"),
            check=True,
            shell=False,
        )
        return
    if kind == "git-checkout":
        _ensure_git_checkout(
            action["repository"], Path(action["destination"]), action["revision"]
        )
        return
    if kind == "download":
        expected_size, expected_sha256 = _receipt_expectations(action)
        size, digest = _download_public_file(
            action["url"],
            Path(action["destination"]),
            expected_size=expected_size,
            expected_sha256=expected_sha256,
        )
        if action.get("receipt"):
            _atomic_write_json(
                Path(action["receipt"]),
                {
                    "revision": action["revision"],
                    "filename": Path(action["destination"]).name,
                    "sizeBytes": size,
                    "sha256": digest,
                },
            )
        return
    if kind == "receipt":
        source = Path(action["source"])
        if not source.is_file():
            raise RuntimeError(f"Cannot write receipt because the model is missing: {source}")
        destination = Path(action["destination"])
        expected_size = action.get("expectedSizeBytes")
        expected_sha256 = action.get("expectedSha256")
        existing = _read_json(destination)
        if existing is not None and existing.get("revision") == action["revision"]:
            expected_size = expected_size or existing.get("sizeBytes")
            expected_sha256 = expected_sha256 or existing.get("sha256")
        size, digest = _assert_file_integrity(
            source, expected_size, expected_sha256
        )
        receipt = {
            "revision": action["revision"],
            "filename": source.name,
            "sizeBytes": size,
            "sha256": digest,
        }
        _atomic_write_json(destination, receipt)
        return
    raise ValueError(f"Unsupported installation action: {kind}")


def _execute_scope(plan: dict[str, Any], scope: str) -> None:
    for action in plan["actions"]:
        if action["scope"] == scope:
            _execute_action(action)


def install_core(runtime_root: Path | None = None) -> dict[str, Any]:
    """Install the pinned core runtime after explicit caller authorization."""
    root = Path(runtime_root) if runtime_root is not None else default_runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    plan = build_install_plan(root)
    _execute_scope(plan, "core")
    return check_runtime(root)


def _disk_usage_path(path: Path) -> Path:
    candidate = path.resolve(strict=False)
    while not candidate.exists() and candidate.parent != candidate:
        candidate = candidate.parent
    return candidate


def install_comfyui(runtime_root: Path | None = None) -> dict[str, Any]:
    """Install the pinned ComfyUI/FLUX runtime when at least 25 GiB is free."""
    root = Path(runtime_root) if runtime_root is not None else default_runtime_root()
    free_bytes = shutil.disk_usage(_disk_usage_path(root)).free
    if free_bytes < MINIMUM_COMFYUI_FREE_BYTES:
        raise RuntimeError("ComfyUI installation requires at least 25 GiB of free disk space")
    root.mkdir(parents=True, exist_ok=True)
    plan = build_install_plan(root, with_comfyui=True)
    _execute_scope(plan, "comfyui")
    return check_runtime(root)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="inspect runtime readiness")
    modes.add_argument("--dry-run", action="store_true", help="print an installation plan")
    modes.add_argument("--install-core", action="store_true", help="install core dependencies")
    modes.add_argument(
        "--install-comfyui", action="store_true", help="install the large ComfyUI runtime"
    )
    parser.add_argument("--with-comfyui", action="store_true", help="include ComfyUI in dry-run")
    parser.add_argument("--runtime-root", type=Path, help="override the per-user runtime root")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.runtime_root if args.runtime_root is not None else default_runtime_root()
    if args.check:
        result = check_runtime(root)
    elif args.install_core:
        result = install_core(root)
    elif args.install_comfyui:
        result = install_comfyui(root)
    else:
        result = build_install_plan(root, with_comfyui=args.with_comfyui)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

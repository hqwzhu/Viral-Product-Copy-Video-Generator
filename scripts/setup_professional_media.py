#!/usr/bin/env python3
"""Plan, inspect, and explicitly install the pinned local media runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_REFERENCE = REPO_ROOT / "references" / "professional-media-runtime.json"
PYTHON_REQUIREMENTS = REPO_ROOT / "requirements-professional-media.txt"
NODE_RUNTIME = REPO_ROOT / "tools" / "hyperframes-runtime"
MINIMUM_COMFYUI_FREE_BYTES = 25 * 1024**3


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
    skip_if_exists: Path | None = None,
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
    if skip_if_exists is not None:
        action["skipIfExists"] = str(skip_if_exists)
    if packages is not None:
        action["packages"] = packages
    return action


def _download(
    action_id: str, scope: str, url: str, destination: Path
) -> dict[str, Any]:
    return {
        "id": action_id,
        "scope": scope,
        "kind": "download",
        "arguments": [],
        "url": url,
        "destination": str(destination),
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
            )
        )

    if with_comfyui:
        comfy = manifest["comfyui"]
        flux = manifest["flux"]
        comfy_dir = runtime_root / "ComfyUI"
        comfy_venv = comfy_dir / ".venv"
        comfy_python = _venv_python(comfy_venv)
        flux_file = comfy_dir / "models" / "checkpoints" / flux["filename"]
        cuda_packages = [
            f"{name}=={version}" for name, version in comfy["cudaPackages"].items()
        ]
        actions.extend(
            [
                _command(
                    "clone-comfyui",
                    "comfyui",
                    ["git", "clone", comfy["repository"], str(comfy_dir)],
                    skip_if_exists=comfy_dir / ".git",
                ),
                _command(
                    "checkout-comfyui-revision",
                    "comfyui",
                    ["git", "checkout", "--detach", comfy["revision"]],
                    cwd=comfy_dir,
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
                _download("download-flux-model", "comfyui", flux["url"], flux_file),
                {
                    "id": "write-comfyui-runtime-receipt",
                    "scope": "comfyui",
                    "kind": "receipt",
                    "arguments": [],
                    "source": str(flux_file),
                    "destination": str(runtime_root / "receipts" / "comfyui-flux.json"),
                    "revision": flux["revision"],
                },
            ]
        )

    if with_musetalk:
        musetalk = manifest["musetalk"]
        musetalk_dir = runtime_root / "MuseTalk"
        actions.extend(
            [
                _command(
                    "clone-musetalk",
                    "musetalk",
                    ["git", "clone", musetalk["repository"], str(musetalk_dir)],
                    skip_if_exists=musetalk_dir / ".git",
                ),
                _command(
                    "checkout-musetalk-revision",
                    "musetalk",
                    ["git", "checkout", "--detach", musetalk["revision"]],
                    cwd=musetalk_dir,
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


def check_runtime(runtime_root: Path | None = None) -> dict[str, Any]:
    """Return tool and installation presence only; never return environment data."""
    root = Path(runtime_root) if runtime_root is not None else default_runtime_root()
    return {
        "runtimeRoot": str(root),
        "tools": {
            "git": shutil.which("git") is not None,
            "npm": shutil.which("npm") is not None,
            "uv": shutil.which("uv") is not None,
        },
        "installed": {
            "corePython": _venv_python(root / "core" / ".venv").is_file(),
            "kokoroModel": (root / "models" / "kokoro" / "kokoro-v1.0.onnx").is_file(),
            "kokoroVoices": (root / "models" / "kokoro" / "voices-v1.0.bin").is_file(),
            "comfyui": (root / "ComfyUI" / ".git").is_dir(),
            "flux": (
                root
                / "ComfyUI"
                / "models"
                / "checkpoints"
                / _manifest()["flux"]["filename"]
            ).is_file(),
        },
    }


def _download_public_file(url: str, destination: Path) -> None:
    if destination.is_file():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.part")
    request = urllib.request.Request(url, headers={"User-Agent": "ENHE-runtime-setup/1.0"})
    try:
        with urllib.request.urlopen(request) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output)
        partial.replace(destination)
    finally:
        if partial.exists():
            partial.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _execute_action(action: dict[str, Any]) -> None:
    kind = action["kind"]
    if kind == "command":
        skip_path = action.get("skipIfExists")
        if skip_path and Path(skip_path).exists():
            return
        subprocess.run(
            action["arguments"],
            cwd=action.get("cwd"),
            check=True,
        )
        return
    if kind == "download":
        _download_public_file(action["url"], Path(action["destination"]))
        return
    if kind == "receipt":
        source = Path(action["source"])
        if not source.is_file():
            raise RuntimeError(f"Cannot write receipt because the model is missing: {source}")
        destination = Path(action["destination"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        receipt = {
            "revision": action["revision"],
            "filename": source.name,
            "sizeBytes": source.stat().st_size,
            "sha256": _sha256(source),
        }
        destination.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
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

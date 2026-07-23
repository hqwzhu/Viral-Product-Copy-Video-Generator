"""AI photographic scene and optional stock B-roll providers.

The providers deliberately use the small :mod:`urllib` standard-library client so
that their network boundary is explicit and easy to exercise with a loopback fake.
"""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping
from urllib import parse, request

from scripts.media_pipeline.contracts import Artifact, StageResult


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1"}
_DEFAULT_TIMEOUT_SECONDS = 600.0
_PEXELS_IMAGE_HOSTS = {"pexels.com", "www.pexels.com", "images.pexels.com"}


class _HttpFailure(RuntimeError):
    """Private marker used to keep network details out of diagnostics."""


class _RedirectDenied(_HttpFailure):
    """A 3xx response is never followed across a trust boundary."""


class _NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, _req, _fp, _code, _msg, _headers, _newurl):
        raise _RedirectDenied


def _open_no_redirect(req: request.Request, *, timeout: float):
    opener = request.build_opener(_NoRedirectHandler())
    return opener.open(req, timeout=timeout)


def _normalise_base_url(base_url: str, allow_cloud_media: bool) -> tuple[str, bool]:
    value = str(base_url).strip()
    parsed = parse.urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("base_url must use http or https and include a host")
    if parsed.username or parsed.password:
        raise ValueError("base_url must not contain credentials")
    host = parsed.hostname
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host.lower() in _LOOPBACK_NAMES
    if not loopback and allow_cloud_media is not True:
        allowed = False
    else:
        allowed = True
    # Preserve an optional path prefix while removing trailing slashes.  The
    # request helpers append endpoint paths without string-concatenating input.
    base = value.rstrip("/")
    return base, allowed


def _endpoint(base_url: str, path: str, query: Mapping[str, Any] | None = None) -> str:
    url = f"{base_url}/{path.lstrip('/')}"
    if query:
        url += "?" + parse.urlencode(query)
    return url


def _request_bytes(
    url: str,
    *,
    timeout: float,
    headers: Mapping[str, str] | None = None,
    payload: bytes | None = None,
) -> bytes:
    method = "POST" if payload is not None else "GET"
    body = payload
    req = request.Request(url, data=body, headers=dict(headers or {}), method=method)
    try:
        with _open_no_redirect(req, timeout=timeout) as response:
            return response.read()
    except _RedirectDenied:
        raise
    except Exception as exc:
        raise _HttpFailure from exc


def _request_json(
    url: str,
    *,
    timeout: float,
    headers: Mapping[str, str] | None = None,
    payload: bytes | None = None,
) -> Any:
    body = _request_bytes(url, timeout=timeout, headers=headers, payload=payload)
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JSON") from exc


def _failure(provider: str, code: str) -> StageResult:
    return StageResult(status="failed", provider=provider, error_code=code)


def _skipped(provider: str, code: str) -> StageResult:
    return StageResult(status="skipped", provider=provider, error_code=code)


def _load_workflow(workflow_path_or_dict: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(workflow_path_or_dict, Mapping):
        value = copy.deepcopy(dict(workflow_path_or_dict))
    else:
        value = json.loads(Path(workflow_path_or_dict).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not value:
        raise ValueError("workflow must be a non-empty object")
    for node in value.values():
        if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
            raise ValueError("workflow node is malformed")
    return value


def _workflow_revision(workflow: Mapping[str, Any]) -> str:
    serialized = json.dumps(workflow, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def _materialize_workflow(
    workflow: Mapping[str, Any], prompt: str, width: int, height: int, seed: int, filename_prefix: str
) -> dict[str, Any]:
    """Replace only request-bound fields in a copied API workflow."""

    materialized = copy.deepcopy(dict(workflow))
    text_nodes = []
    for node in materialized.values():
        class_type = node.get("class_type")
        inputs = node["inputs"]
        if class_type == "CLIPTextEncode" and isinstance(inputs.get("text"), str):
            text_nodes.append(inputs)
        elif class_type == "EmptyLatentImage":
            inputs["width"] = int(width)
            inputs["height"] = int(height)
        elif class_type == "KSampler":
            inputs["seed"] = int(seed)
        elif class_type == "SaveImage":
            inputs["filename_prefix"] = filename_prefix
    if text_nodes:
        text_nodes[0]["text"] = prompt
    return materialized


def _extract_image_ref(history: Any, prompt_id: str) -> dict[str, str] | None:
    if not isinstance(history, Mapping):
        return None
    record = history.get(prompt_id, history)
    if not isinstance(record, Mapping):
        return None
    outputs = record.get("outputs")
    if not isinstance(outputs, Mapping):
        return None
    for output in outputs.values():
        if not isinstance(output, Mapping):
            continue
        images = output.get("images")
        if not isinstance(images, list):
            continue
        for image in images:
            if not isinstance(image, Mapping) or not isinstance(image.get("filename"), str):
                continue
            filename = image["filename"].strip()
            if filename:
                return {
                    "filename": filename,
                    "subfolder": str(image.get("subfolder", "")),
                    "type": str(image.get("type", "output")),
                }
    return None


def _pexels_image_url_allowed(value: str) -> bool:
    """Allow only HTTPS URLs hosted by the official Pexels image domain."""

    try:
        parsed = parse.urlsplit(value)
        if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
            return False
        host = (parsed.hostname or "").lower().rstrip(".")
        if not host:
            return False
        # Literal IPs are never part of the allowlist, including private and
        # loopback addresses. Keeping the allowlist hostname-based also avoids
        # DNS rebinding to an arbitrary private endpoint.
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            return False
        if host not in _PEXELS_IMAGE_HOSTS:
            return False
        return parsed.port in (None, 443)
    except (TypeError, ValueError):
        return False


class ComfyUiFluxProvider:
    """Generate an image with a local ComfyUI FLUX.1-schnell API workflow."""

    provider_name = "comfyui_flux"

    def __init__(
        self,
        base_url: str,
        workflow_path_or_dict: str | Path | Mapping[str, Any],
        allow_cloud_media: bool = False,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url, self._network_allowed = _normalise_base_url(
            base_url, allow_cloud_media
        )
        self.allow_cloud_media = allow_cloud_media
        self.timeout_seconds = max(0.1, float(timeout_seconds))
        self.workflow = _load_workflow(workflow_path_or_dict)
        self.workflow_revision = _workflow_revision(self.workflow)

    def health(self) -> bool:
        if not self._network_allowed:
            return False
        try:
            value = _request_json(
                _endpoint(self.base_url, "/system_stats"),
                timeout=min(3.0, self.timeout_seconds),
            )
            if not isinstance(value, Mapping) or not value or "error" in value:
                return False
            system = value.get("system")
            if isinstance(system, Mapping) and system and "error" not in system:
                return True
            # ComfyUI deployments may expose device information alongside or
            # instead of system metadata; an actual list is still a structured
            # health payload, unlike an arbitrary non-empty JSON object.
            return isinstance(value.get("devices"), list)
        except (_HttpFailure, ValueError):
            return False

    def generate(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1080,
        seed: int = 7,
        output_dir: str | Path | None = None,
        *,
        temp: str | Path | None = None,
    ) -> StageResult:
        if not self._network_allowed:
            return _skipped(self.provider_name, "cloud_media_not_allowed")
        if not self.health():
            return _skipped(self.provider_name, "comfyui_unavailable")
        destination_dir = Path(output_dir if output_dir is not None else temp or Path.cwd())
        prefix = "ai-scene-" + uuid.uuid4().hex[:12]
        materialized = _materialize_workflow(
            self.workflow, str(prompt), int(width), int(height), int(seed), prefix
        )
        request_payload = json.dumps(
            {"prompt": materialized, "client_id": str(uuid.uuid4())},
            ensure_ascii=False,
        ).encode("utf-8")
        try:
            response = _request_json(
                _endpoint(self.base_url, "/prompt"),
                timeout=self.timeout_seconds,
                headers={"Content-Type": "application/json"},
                payload=request_payload,
            )
        except _RedirectDenied:
            return _failure(self.provider_name, "comfyui_redirect_denied")
        except _HttpFailure:
            return _failure(self.provider_name, "comfyui_prompt_failed")
        except ValueError:
            return _failure(self.provider_name, "comfyui_prompt_malformed")
        if (
            not isinstance(response, Mapping)
            or not isinstance(response.get("prompt_id"), str)
            or not response["prompt_id"].strip()
        ):
            return _failure(self.provider_name, "comfyui_prompt_malformed")
        prompt_id = response["prompt_id"]

        deadline = time.monotonic() + self.timeout_seconds
        image_ref = None
        while time.monotonic() < deadline:
            try:
                history = _request_json(
                    _endpoint(self.base_url, f"/history/{parse.quote(prompt_id, safe='')}"),
                    timeout=min(self.timeout_seconds, 30.0),
                )
            except _RedirectDenied:
                return _failure(self.provider_name, "comfyui_redirect_denied")
            except _HttpFailure:
                return _failure(self.provider_name, "comfyui_history_failed")
            except ValueError:
                return _failure(self.provider_name, "comfyui_history_malformed")
            if not isinstance(history, Mapping):
                return _failure(self.provider_name, "comfyui_history_malformed")
            if not history:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(0.25, remaining))
                continue
            # A history object with neither the requested id nor outputs is a
            # legitimate in-progress response; malformed output is not.
            record = history.get(prompt_id, history)
            if not isinstance(record, Mapping):
                return _failure(self.provider_name, "comfyui_history_malformed")
            if prompt_id not in history and "outputs" not in record and "status" not in record:
                return _failure(self.provider_name, "comfyui_history_malformed")
            if "outputs" in record and not isinstance(record.get("outputs"), Mapping):
                return _failure(self.provider_name, "comfyui_history_malformed")
            image_ref = _extract_image_ref(history, prompt_id)
            if image_ref is not None:
                break
            outputs = record.get("outputs")
            if isinstance(outputs, Mapping):
                return _failure(self.provider_name, "comfyui_image_missing")
            status = record.get("status")
            if isinstance(status, Mapping) and status.get("completed") is True:
                return _failure(self.provider_name, "comfyui_image_missing")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(0.25, remaining))
        if image_ref is None:
            return _failure(self.provider_name, "comfyui_timeout")
        try:
            image_bytes = _request_bytes(
                _endpoint(self.base_url, "/view", image_ref),
                timeout=min(self.timeout_seconds, 30.0),
            )
        except _RedirectDenied:
            return _failure(self.provider_name, "comfyui_redirect_denied")
        except _HttpFailure:
            return _failure(self.provider_name, "comfyui_image_download_failed")
        if len(image_bytes) <= len(_PNG_MAGIC) or not image_bytes.startswith(_PNG_MAGIC):
            return _failure(self.provider_name, "comfyui_image_invalid")
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{prefix}.png"
        partial = destination.with_name(destination.name + ".part")
        try:
            partial.write_bytes(image_bytes)
            if partial.stat().st_size <= len(_PNG_MAGIC) or partial.read_bytes()[:8] != _PNG_MAGIC:
                raise ValueError("invalid PNG")
            partial.replace(destination)
            artifact = Artifact.from_file(
                "ai_scene", destination, self.provider_name, "ai-generated", "Apache-2.0"
            )
            artifact = replace(
                artifact,
                metadata={
                    "aiGenerated": True,
                    "seed": int(seed),
                    "prompt": str(prompt),
                    "width": int(width),
                    "height": int(height),
                    "workflowRevision": self.workflow_revision,
                },
            )
            return StageResult.ready(self.provider_name, [artifact])
        except (OSError, ValueError):
            partial.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            return _failure(self.provider_name, "comfyui_image_write_failed")


class PexelsProvider:
    """Optional Pexels landscape image search/download provider."""

    provider_name = "pexels"

    def __init__(self, api_key: str, timeout_seconds: float = 15.0) -> None:
        self._api_key = str(api_key or "")
        self.timeout_seconds = max(0.1, float(timeout_seconds))

    def search(self, query: str, out_dir: str | Path, limit: int) -> StageResult:
        if not self._api_key:
            return _skipped(self.provider_name, "pexels_not_configured")
        if int(limit) <= 0:
            return _skipped(self.provider_name, "pexels_no_results")
        params = {"query": str(query), "per_page": max(1, int(limit))}
        url = _endpoint("https://api.pexels.com", "/v1/search", params)
        try:
            payload = _request_json(
                url,
                timeout=self.timeout_seconds,
                headers={"Authorization": self._api_key},
            )
        except _RedirectDenied:
            return _failure(self.provider_name, "pexels_redirect_denied")
        except _HttpFailure:
            return _failure(self.provider_name, "pexels_request_failed")
        except ValueError:
            return _failure(self.provider_name, "pexels_response_malformed")
        if not isinstance(payload, Mapping) or not isinstance(payload.get("photos"), list):
            return _failure(self.provider_name, "pexels_response_malformed")
        photos = [
            photo
            for photo in payload["photos"]
            if isinstance(photo, Mapping)
            and isinstance(photo.get("width"), (int, float))
            and isinstance(photo.get("height"), (int, float))
            and photo["width"] > photo["height"]
            and isinstance(photo.get("src"), Mapping)
            and isinstance(photo["src"].get("original"), str)
        ][: int(limit)]
        if not photos:
            return _skipped(self.provider_name, "pexels_no_results")
        image_dir = Path(out_dir) / "b-roll_辅助镜头"
        artifacts = []
        partial_paths: list[Path] = []
        try:
            for index, photo in enumerate(photos, start=1):
                source_url = str(photo["src"]["original"])
                if not _pexels_image_url_allowed(source_url):
                    raise _HttpFailure
                image_bytes = _request_bytes(source_url, timeout=self.timeout_seconds)
                if not image_bytes:
                    raise _HttpFailure
                destination = image_dir / f"b-roll-{index:02d}.jpg"
                partial = destination.with_name(destination.name + ".part")
                partial_paths.append(partial)
                image_dir.mkdir(parents=True, exist_ok=True)
                partial.write_bytes(image_bytes)
                partial.replace(destination)
                artifact = Artifact.from_file(
                    "b_roll_image", destination, self.provider_name, "pexels", "Pexels"
                )
                artifacts.append(
                    replace(
                        artifact,
                        metadata={
                            "photographer": str(photo.get("photographer", "")),
                            "pexelsUrl": str(photo.get("url", "")),
                            "originalUrl": source_url,
                            "orientation": "landscape",
                        },
                    )
                )
        except _RedirectDenied:
            for artifact in artifacts:
                Path(artifact.path).unlink(missing_ok=True)
            for partial in partial_paths:
                partial.unlink(missing_ok=True)
            return _failure(self.provider_name, "pexels_redirect_denied")
        except (OSError, ValueError, _HttpFailure):
            for artifact in artifacts:
                Path(artifact.path).unlink(missing_ok=True)
            for partial in partial_paths:
                partial.unlink(missing_ok=True)
            return _failure(self.provider_name, "pexels_request_failed")
        return StageResult.ready(self.provider_name, artifacts)


__all__ = ["ComfyUiFluxProvider", "PexelsProvider"]

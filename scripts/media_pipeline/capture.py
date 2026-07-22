import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.media_pipeline.contracts import Artifact, StageResult
from scripts.media_pipeline.security import MediaSecurityError, validate_capture_shot

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - exercised in environments without Playwright
    sync_playwright = None


_DEFAULT_VIEWPORT = (1440, 900)
_FALLBACK_SELECTORS = ("main", "[role=main]", "body")
_SAFE_SHOT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def build_default_capture_plan(source_url: str) -> dict[str, Any]:
    return {
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
    }


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _validate_plan(
    plan: Mapping[str, Any], allow_localhost: bool
) -> tuple[str, tuple[dict[str, Any], ...]]:
    if not isinstance(plan, Mapping):
        raise MediaSecurityError("Capture plan must be a mapping")
    source_url = plan.get("sourceUrl")
    shots = plan.get("shots")
    if not isinstance(source_url, str) or not source_url:
        raise MediaSecurityError("Capture plan sourceUrl is required")
    if (
        not isinstance(shots, Sequence)
        or isinstance(shots, (str, bytes))
        or not shots
    ):
        raise MediaSecurityError("Capture plan shots must be a non-empty sequence")

    validated = []
    shot_ids = set()
    for shot in shots:
        if not isinstance(shot, Mapping):
            raise MediaSecurityError("Capture shot must be a mapping")
        validate_capture_shot(source_url, shot, allow_localhost=allow_localhost)

        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not _SAFE_SHOT_ID.fullmatch(shot_id):
            raise MediaSecurityError("Capture shot id must be a safe slug")
        if shot_id in shot_ids:
            raise MediaSecurityError("Capture shot ids must be unique")
        shot_ids.add(shot_id)

        selector = shot.get("selector")
        if not isinstance(selector, str) or not selector.strip():
            raise MediaSecurityError("Capture shot selector is required")
        viewport = shot.get("viewport")
        if (
            not isinstance(viewport, Sequence)
            or isinstance(viewport, (str, bytes))
            or len(viewport) != 2
            or not all(_positive_int(item) for item in viewport)
        ):
            raise MediaSecurityError(
                "Capture shot viewport must contain two positive integers"
            )
        duration = shot.get("duration")
        if not _positive_int(duration):
            raise MediaSecurityError("Capture shot duration must be a positive integer")
        validated.append(dict(shot))

    return source_url, tuple(validated)


def _close_quietly(resource: Any) -> None:
    if resource is None:
        return
    try:
        resource.close()
    except Exception:
        pass


def playwright_chromium_available() -> bool:
    if sync_playwright is None:
        return False
    playwright = None
    browser = None
    try:
        playwright = sync_playwright().start()
        executable = Path(playwright.chromium.executable_path)
        if not executable.is_file():
            return False
        browser = playwright.chromium.launch(headless=True)
        return True
    except Exception:
        return False
    finally:
        _close_quietly(browser)
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass


def _resolve_locator(page: Any, requested_selector: str) -> tuple[Any, str]:
    for selector in (requested_selector, *_FALLBACK_SELECTORS):
        try:
            locator = page.locator(selector).first
            if locator.count() and locator.is_visible():
                return locator, selector
        except Exception:
            continue
    raise RuntimeError("No visible capture selector was found")


def _validate_final_url(
    source_url: str, final_url: str, allow_localhost: bool
) -> None:
    validate_capture_shot(
        source_url,
        {"url": final_url, "action": "none"},
        allow_localhost=allow_localhost,
    )


class PlaywrightCaptureProvider:
    def __init__(self, allow_localhost: bool = False):
        self.allow_localhost = allow_localhost

    def capture(
        self, plan: Mapping[str, Any], out_dir: str | Path
    ) -> StageResult:
        source_url, shots = _validate_plan(plan, self.allow_localhost)

        phase = "prepare_output"
        playwright = None
        browser = None
        context = None
        page = None
        video = None
        artifacts = []
        try:
            output_dir = Path(out_dir).resolve()
            video_dir = output_dir / "interaction-video"
            output_dir.mkdir(parents=True, exist_ok=True)
            video_dir.mkdir(parents=True, exist_ok=True)
            if sync_playwright is None:
                raise RuntimeError("Playwright is unavailable")

            phase = "start_playwright"
            playwright = sync_playwright().start()
            phase = "launch_browser"
            browser = playwright.chromium.launch(headless=True)
            phase = "create_context"
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                record_video_dir=str(video_dir),
                record_video_size={"width": 1440, "height": 900},
            )
            page = context.new_page()
            video = page.video

            phase = "navigate_source"
            page.goto(source_url, wait_until="domcontentloaded")
            _validate_final_url(source_url, page.url, self.allow_localhost)

            for shot in shots:
                shot_id = shot["id"]
                target_url = shot.get("url", source_url)
                viewport = list(shot["viewport"])
                phase = f"capture_{shot_id}"

                page.set_viewport_size(
                    {"width": viewport[0], "height": viewport[1]}
                )
                if page.url != target_url:
                    page.goto(target_url, wait_until="domcontentloaded")
                    _validate_final_url(source_url, page.url, self.allow_localhost)

                requested_selector = shot["selector"]
                locator, resolved_selector = _resolve_locator(
                    page, requested_selector
                )
                locator.scroll_into_view_if_needed()

                action = shot.get("action") or "none"
                if action == "scroll":
                    page.mouse.wheel(0, max(350, viewport[1] // 3))
                    page.wait_for_timeout(350)
                elif action == "click":
                    locator.click()
                    page.wait_for_timeout(350)

                _validate_final_url(source_url, page.url, self.allow_localhost)
                image_path = output_dir / f"{shot_id}.png"
                locator.screenshot(path=str(image_path))
                artifact = Artifact.from_file(
                    "product_capture_image",
                    image_path,
                    provider="playwright",
                    source="product_page",
                    license_id="",
                )
                artifacts.append(
                    replace(
                        artifact,
                        metadata={
                            "shotId": shot_id,
                            "requestedSelector": requested_selector,
                            "resolvedSelector": resolved_selector,
                            "selectorFallback": resolved_selector
                            != requested_selector,
                            "finalUrl": page.url,
                            "viewport": viewport,
                            "action": action,
                            "duration": shot["duration"],
                        },
                    )
                )

            final_url = page.url
            _validate_final_url(source_url, final_url, self.allow_localhost)
            phase = "finalize_video"
            page.close()
            page = None
            context.close()
            context = None
            video_path = Path(video.path())
            video_artifact = Artifact.from_file(
                "product_capture_video",
                video_path,
                provider="playwright",
                source="product_page",
                license_id="",
            )
            artifacts.append(
                replace(
                    video_artifact,
                    metadata={
                        "finalUrl": final_url,
                        "viewport": list(_DEFAULT_VIEWPORT),
                        "shotIds": [shot["id"] for shot in shots],
                    },
                )
            )
            return StageResult.ready(
                "playwright",
                artifacts,
                diagnostics={
                    "captureCount": len(shots),
                    "videoCount": 1,
                },
            )
        except MediaSecurityError:
            raise
        except Exception as exc:
            return StageResult(
                status="failed",
                provider="playwright",
                error_code=f"{phase}_failed",
                diagnostics={
                    "phase": phase,
                    "exceptionType": type(exc).__name__,
                },
            )
        finally:
            _close_quietly(page)
            _close_quietly(context)
            _close_quietly(browser)
            if playwright is not None:
                try:
                    playwright.stop()
                except Exception:
                    pass

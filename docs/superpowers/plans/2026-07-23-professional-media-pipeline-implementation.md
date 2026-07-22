# Professional Media Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the default template-only media path with a locally generated, voiced professional product-demo pipeline that produces real product captures, AI photographic scenes, advanced motion video, commercial covers/detail images, bilingual output directories, and truthful quality evidence.

**Architecture:** Keep Python as the orchestrator and add a focused `scripts/media_pipeline` package. Playwright, local HyperFrames/Kokoro, ComfyUI/FLUX.1-schnell, Pillow, and FFmpeg communicate through small process or HTTP adapters; the existing Skill and publish pack stay compatible through thin entry-point changes. Expensive stages write hashed, atomic stage results so a failed run resumes safely, while one quality evaluator independently proves `professional_ready`.

**Tech Stack:** Python 3.14 core runtime, Python 3.12 isolated ComfyUI runtime, `unittest`, Playwright 1.58.0, Pillow 12.3.0, HyperFrames 0.7.68, GSAP 3.13.0, Kokoro ONNX 0.4.7 with its Apache-2.0 model release, FFmpeg/FFprobe 8.1.1, ComfyUI pinned at `f6d30bce9a862d56d9184dd65341621a8905ea3e`, FLUX.1-schnell FP8 pinned at Hugging Face revision `7d679837b018bfeb28eca55734b335efcd0e7100`.

---

## Scope check

The approved specification contains several media stages, but they are not independent products: every stage contributes artifacts to one manifest, one publish pack, and one quality verdict. They therefore remain in one implementation plan. Optional MuseTalk/HeyGen presenters are isolated behind a provider boundary and land after the complete product-demonstration path, so presenter risk cannot delay the required professional result.

## File map

### New core files

- `scripts/media_pipeline/__init__.py`: public package exports and media-quality constants.
- `scripts/media_pipeline/paths.py`: bilingual default root, run IDs, directory creation, and legacy lookup.
- `scripts/media_pipeline/contracts.py`: `Artifact`, `StageResult`, `MediaJob`, JSON serialization, hashing, and atomic writes.
- `scripts/media_pipeline/security.py`: capture-origin checks, denied routes, cloud allowlists, portrait authorization, and secret redaction.
- `scripts/media_pipeline/capture.py`: automatic capture plan plus Playwright screenshot and interaction-video capture.
- `scripts/media_pipeline/voiceover.py`: narration selection, Kokoro invocation, SAPI fallback, and timing segments.
- `scripts/media_pipeline/scenes.py`: user/capture selection, ComfyUI FLUX API adapter, and optional Pexels B-roll.
- `scripts/media_pipeline/visuals.py`: commercial cover/detail composition and contact-sheet output.
- `scripts/media_pipeline/video.py`: HyperFrames project materialization, strict render, FFmpeg normalization, and ffprobe inspection.
- `scripts/media_pipeline/quality.py`: artifact-based media-quality checks and final level selection.
- `scripts/media_pipeline/presenters.py`: optional MuseTalk command adapter and fail-closed HeyGen boundary.
- `scripts/media_pipeline/orchestrator.py`: resumable stage orchestration, manifest assembly, and publish-pack attachment.
- `scripts/professional_media_pipeline.py`: direct CLI for one professional media run.
- `scripts/setup_professional_media.py`: pinned dependency health check and installation.
- `scripts/test_professional_media_pipeline.py`: isolated unit, integration, security, and end-to-end tests.

### New runtime and template files

- `requirements-professional-media.txt`: pinned core Python media dependencies.
- `references/professional-media-runtime.json`: repository, model, package, license, and revision pins.
- `references/comfyui/flux1-schnell-api.json`: local ComfyUI API workflow.
- `references/hyperframes-professional/index.html`: offline composition root.
- `references/hyperframes-professional/style.css`: branded scene, caption, pointer, and transition styling.
- `references/hyperframes-professional/composition.js`: data-driven DOM and GSAP timeline construction.
- `references/professional-media-fixture/product.html`: deterministic product page used by capture tests.
- `tools/hyperframes-runtime/package.json`: local HyperFrames and GSAP pins.
- `tools/hyperframes-runtime/package-lock.json`: reproducible Node dependency graph.

### Existing files changed surgically

- `scripts/render_video.py`: retain draft CLI and delegate explicit professional runs.
- `scripts/media_asset_pack.py`: retain draft cards and accept professional assets without regenerating them.
- `scripts/run_promotion_workflow.py`: invoke the professional orchestrator by default and keep the legacy draft branch.
- `scripts/promotion_cycle_runner.py`: forward media options.
- `scripts/product_batch_runner.py`: create product runs under `runs_运行记录` and forward media options.
- `scripts/final_capability_runner.py`: forward and summarize media quality without changing publication evidence.
- `scripts/real_run_playbook.py`: document/forward professional media options.
- `scripts/skill_entry.py`: bilingual default output root and public media flags.
- `scripts/promotion_manager.py`: route generated content and publish packs through `RunPaths` when a run layout is supplied.
- `scripts/test_promotion_manager.py`: compatibility assertions only; new media behavior stays in the new focused test file.
- `SKILL.md`, `README.md`, `README.zh-CN.md`, `README.en.md`: installation, usage, quality, security, and output documentation.

## Task 1: Pin and bootstrap the professional media runtime

**Files:**
- Create: `requirements-professional-media.txt`
- Create: `references/professional-media-runtime.json`
- Create: `tools/hyperframes-runtime/package.json`
- Create: `scripts/setup_professional_media.py`
- Create: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write the failing runtime-plan test**

```python
class RuntimeSetupTest(unittest.TestCase):
    def test_runtime_plan_is_pinned_and_never_contains_secrets(self) -> None:
        module = load_script_module(SETUP_PROFESSIONAL_MEDIA)
        plan = module.build_install_plan(Path("C:/runtime"), with_comfyui=True, with_musetalk=False)
        encoded = json.dumps(plan, ensure_ascii=False)
        self.assertIn("hyperframes@0.7.68", encoded)
        self.assertIn("f6d30bce9a862d56d9184dd65341621a8905ea3e", encoded)
        self.assertIn("7d679837b018bfeb28eca55734b335efcd0e7100", encoded)
        self.assertNotIn("HF_TOKEN", encoded)
        self.assertNotIn("apiKey", encoded)
```

- [ ] **Step 2: Run the test and verify the missing setup module fails**

Run: `python -m unittest scripts.test_professional_media_pipeline.RuntimeSetupTest.test_runtime_plan_is_pinned_and_never_contains_secrets -v`

Expected: `ERROR` with `FileNotFoundError` for `scripts/setup_professional_media.py`.

- [ ] **Step 3: Add the exact dependency pins**

`requirements-professional-media.txt`:

```text
kokoro-onnx==0.4.7
soundfile==0.14.0
playwright==1.58.0
Pillow==12.3.0
psutil==7.2.2
```

`tools/hyperframes-runtime/package.json`:

```json
{
  "name": "enhe-professional-media-runtime",
  "private": true,
  "version": "1.0.0",
  "dependencies": {
    "gsap": "3.13.0",
    "hyperframes": "0.7.68"
  }
}
```

`references/professional-media-runtime.json`:

```json
{
  "python": "3.12",
  "hyperframes": {"version": "0.7.68", "license": "Apache-2.0"},
  "kokoro": {
    "package": "kokoro-onnx==0.4.7",
    "license": "MIT",
    "modelLicense": "Apache-2.0",
    "modelUrl": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voicesUrl": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
  },
  "comfyui": {
    "repository": "https://github.com/Comfy-Org/ComfyUI.git",
    "commit": "f6d30bce9a862d56d9184dd65341621a8905ea3e",
    "license": "GPL-3.0-only",
    "torch": "2.11.0+cu128",
    "torchvision": "0.26.0+cu128",
    "torchaudio": "2.11.0+cu128"
  },
  "flux": {
    "repository": "Comfy-Org/flux1-schnell",
    "revision": "7d679837b018bfeb28eca55734b335efcd0e7100",
    "filename": "flux1-schnell-fp8.safetensors",
    "license": "Apache-2.0"
  },
  "musetalk": {
    "repository": "https://github.com/TMElyralab/MuseTalk.git",
    "commit": "0a89dec45a0192b824e3cf4daf96c239440c5ed8",
    "license": "MIT",
    "enabledByDefault": false
  }
}
```

- [ ] **Step 4: Implement a dry-run-first installer**

The installer exposes `build_install_plan()`, `check_runtime()`, `install_core()`, and `install_comfyui()`. It uses argument arrays and never prints environment values:

```python
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references" / "professional-media-runtime.json"


def default_runtime_root() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")
    return base / "ENHE" / "professional-media"


def build_install_plan(runtime_root: Path, with_comfyui: bool, with_musetalk: bool) -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plan = [
        {"action": "command", "argv": [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements-professional-media.txt")]},
        {"action": "command", "argv": ["npm", "install", "--prefix", str(ROOT / "tools" / "hyperframes-runtime")]},
        {"action": "command", "argv": [sys.executable, "-m", "playwright", "install", "chromium"]},
        {"action": "download", "url": manifest["kokoro"]["modelUrl"], "destination": str(runtime_root / "kokoro-v1.0.onnx")},
        {"action": "download", "url": manifest["kokoro"]["voicesUrl"], "destination": str(runtime_root / "voices-v1.0.bin")},
    ]
    if with_comfyui:
        plan.extend(
            [
                {"action": "command", "argv": ["git", "clone", manifest["comfyui"]["repository"], str(runtime_root / "ComfyUI")]},
                {"action": "command", "argv": ["git", "-C", str(runtime_root / "ComfyUI"), "checkout", manifest["comfyui"]["commit"]]},
                {"action": "command", "argv": ["uv", "venv", "--python", manifest["python"], str(runtime_root / "comfyui-venv")]},
                {"action": "download", "url": "https://huggingface.co/Comfy-Org/flux1-schnell/resolve/7d679837b018bfeb28eca55734b335efcd0e7100/flux1-schnell-fp8.safetensors?download=true", "destination": str(runtime_root / "ComfyUI" / "models" / "checkpoints" / "flux1-schnell-fp8.safetensors")},
            ]
        )
    if with_musetalk:
        plan.append({"action": "command", "argv": ["git", "clone", manifest["musetalk"]["repository"], str(runtime_root / "MuseTalk")]})
    return plan
```

`install_comfyui()` additionally installs the pinned CUDA packages from `https://download.pytorch.org/whl/cu128`, installs the pinned ComfyUI requirements, downloads the commit-pinned `flux1-schnell-fp8.safetensors` into `ComfyUI/models/checkpoints`, and writes a local runtime receipt containing revision, file size, and SHA-256. It refuses installation when free disk space is below 25 GiB.

- [ ] **Step 5: Generate the lockfile and run installer tests**

Run:

```powershell
npm install --prefix tools/hyperframes-runtime --package-lock-only
python -m unittest scripts.test_professional_media_pipeline.RuntimeSetupTest -v
python scripts/setup_professional_media.py --check
python scripts/setup_professional_media.py --dry-run --with-comfyui
```

Expected: all tests pass; `--check` reports present/missing booleans; `--dry-run` prints pinned commands without credentials.

- [ ] **Step 6: Commit the bootstrap**

```powershell
git add requirements-professional-media.txt references/professional-media-runtime.json tools/hyperframes-runtime/package.json tools/hyperframes-runtime/package-lock.json scripts/setup_professional_media.py scripts/test_professional_media_pipeline.py
git commit -m "build: pin professional media runtime"
```

## Task 2: Add bilingual paths and typed media contracts

**Files:**
- Create: `scripts/media_pipeline/__init__.py`
- Create: `scripts/media_pipeline/paths.py`
- Create: `scripts/media_pipeline/contracts.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing path and contract tests**

```python
class PathContractTest(unittest.TestCase):
    def test_default_run_paths_use_one_bilingual_tree(self) -> None:
        paths = new_run_paths(Path("C:/work/promotion-output_推广输出"), "ENHE API", now="20260723-120000")
        self.assertEqual(paths.root.name, "20260723-120000-enhe-api")
        self.assertEqual(paths.captures.name, "product-captures_产品录屏")
        self.assertEqual(paths.reports.name, "reports_报告")
        self.assertNotIn("promotion-output/product-batch-runs", str(paths.root).replace("\\", "/"))

    def test_stage_result_hashes_artifacts_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "capture.png"
            source.write_bytes(b"capture")
            artifact = Artifact.from_file("product_capture_image", source, "playwright", "user-authorized")
            result = StageResult.ready("playwright", [artifact])
            self.assertEqual(StageResult.from_dict(result.to_dict()), result)
            self.assertEqual(len(artifact.sha256), 64)
```

- [ ] **Step 2: Verify the package import fails**

Run: `python -m unittest scripts.test_professional_media_pipeline.PathContractTest -v`

Expected: `ERROR` because `media_pipeline.paths` and `media_pipeline.contracts` do not exist.

- [ ] **Step 3: Implement the single path owner**

```python
DEFAULT_OUTPUT_ROOT = Path("promotion-output_推广输出")
RUNS_DIR = "runs_运行记录"


@dataclass(frozen=True)
class RunPaths:
    root: Path
    source_assets: Path
    captures: Path
    generated_content: Path
    voiceovers: Path
    b_roll: Path
    ai_scenes: Path
    videos: Path
    covers: Path
    detail_images: Path
    publish_packs: Path
    reports: Path

    def create(self) -> "RunPaths":
        for value in fields(self):
            Path(getattr(self, value.name)).mkdir(parents=True, exist_ok=True)
        return self


def new_run_paths(output_root: Path, product: str, now: str | None = None) -> RunPaths:
    timestamp = now or datetime.now().strftime("%Y%m%d-%H%M%S")
    root = output_root / RUNS_DIR / f"{timestamp}-{slugify(product)}"
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
```

Add `find_existing(relative_new, relative_legacy)` so readers prefer the bilingual path and fall back to the old tree without copying files.

- [ ] **Step 4: Implement contracts and atomic JSON writes**

```python
@dataclass(frozen=True)
class Artifact:
    type: str
    path: str
    sha256: str
    source: str
    license: str
    provider: str
    contains_user_data: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, artifact_type: str, path: Path, provider: str, source: str, license_id: str = "") -> "Artifact":
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return cls(artifact_type, str(path.resolve()), digest, source, license_id, provider)


@dataclass(frozen=True)
class StageResult:
    status: Literal["ready", "degraded", "failed", "skipped"]
    provider: str
    artifacts: tuple[Artifact, ...] = ()
    warnings: tuple[str, ...] = ()
    error_code: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ready(cls, provider: str, artifacts: Sequence[Artifact], diagnostics: dict[str, Any] | None = None) -> "StageResult":
        return cls("ready", provider, tuple(artifacts), diagnostics=diagnostics or {})


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
```

Define `MediaJob` with the approved fields and exact `to_dict()`/`from_dict()` methods. Export the four media-quality constants from `__init__.py`.

- [ ] **Step 5: Run tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.PathContractTest -v`

Expected: two tests pass.

```powershell
git add scripts/media_pipeline scripts/test_professional_media_pipeline.py
git commit -m "feat: add bilingual media paths and contracts"
```

## Task 3: Enforce security, provenance, and resumability

**Files:**
- Create: `scripts/media_pipeline/security.py`
- Modify: `scripts/media_pipeline/contracts.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing security and resume tests**

```python
class MediaSecurityTest(unittest.TestCase):
    def test_capture_plan_rejects_cross_origin_and_private_routes(self) -> None:
        with self.assertRaises(MediaSecurityError):
            validate_capture_shot("https://enhe.test/product", {"url": "https://evil.test/x", "selector": "main"})
        with self.assertRaises(MediaSecurityError):
            validate_capture_shot("https://enhe.test/product", {"url": "https://enhe.test/admin", "selector": "main"})

    def test_cloud_upload_requires_flag_and_allowlisted_file(self) -> None:
        allowed = Path("C:/run/ai-scenes_AI场景图/scene.png")
        self.assertFalse(cloud_file_allowed(allowed, False, [allowed]))
        self.assertTrue(cloud_file_allowed(allowed, True, [allowed]))
        self.assertFalse(cloud_file_allowed(Path("C:/Users/HU/AppData/Chrome/Cookies"), True, [allowed]))

    def test_stage_resume_rejects_modified_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            artifact_path = Path(temp) / "scene.png"
            artifact_path.write_bytes(b"first")
            result = StageResult.ready("local", [Artifact.from_file("ai_scene", artifact_path, "local", "generated")])
            artifact_path.write_bytes(b"changed")
            self.assertFalse(stage_result_is_valid(result))
```

- [ ] **Step 2: Run and verify missing security functions fail**

Run: `python -m unittest scripts.test_professional_media_pipeline.MediaSecurityTest -v`

Expected: import errors for the new security functions.

- [ ] **Step 3: Implement the explicit deny rules**

```python
DENIED_ROUTE_PARTS = ("/account", "/admin", "/billing", "/checkout", "/payment")
SECRET_KEY_PATTERN = re.compile(r"(api[_-]?key|token|secret|cookie|authorization)", re.IGNORECASE)


def validate_capture_shot(source_url: str, shot: dict[str, Any], allow_localhost: bool = False) -> None:
    source = urlsplit(source_url)
    target = urlsplit(str(shot.get("url") or source_url))
    if (source.scheme, source.netloc) != (target.scheme, target.netloc):
        raise MediaSecurityError("capture_cross_origin")
    if not allow_localhost and target.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise MediaSecurityError("capture_localhost_denied")
    if any(part in target.path.lower() for part in DENIED_ROUTE_PARTS):
        raise MediaSecurityError("capture_private_route")
    if str(shot.get("action") or "none") not in {"none", "click", "scroll"}:
        raise MediaSecurityError("capture_action_denied")


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SECRET_KEY_PATTERN.search(str(key)) else redact_secrets(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value
```

`cloud_file_allowed()` resolves every path, requires `allow_cloud_media=True`, requires membership in the resolved allowlist, and rejects any path containing browser-profile directory names.

- [ ] **Step 4: Add hash-based stage validation**

```python
def stage_result_is_valid(result: StageResult) -> bool:
    if result.status not in {"ready", "degraded"} or not result.artifacts:
        return False
    for artifact in result.artifacts:
        path = Path(artifact.path)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != artifact.sha256:
            return False
    return True
```

- [ ] **Step 5: Run tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.MediaSecurityTest -v`

Expected: three tests pass.

```powershell
git add scripts/media_pipeline/security.py scripts/media_pipeline/contracts.py scripts/test_professional_media_pipeline.py
git commit -m "feat: secure and resume media stages"
```

## Task 4: Capture real product screenshots and interaction video

**Files:**
- Create: `scripts/media_pipeline/capture.py`
- Create: `references/professional-media-fixture/product.html`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Add a deterministic product fixture and failing capture test**

The fixture contains `#hero`, `#workflow`, `#features`, `#proof`, and `#cta` sections with fixed heights, ENHE colors, and a CSS-only product dashboard.

```python
class ProductCaptureTest(unittest.TestCase):
    def test_playwright_capture_produces_three_unique_product_images_and_video(self) -> None:
        if not playwright_chromium_available():
            self.skipTest("Playwright Chromium is unavailable")
        with serve_fixture(PRODUCT_FIXTURE) as url, tempfile.TemporaryDirectory() as temp:
            plan = build_default_capture_plan(url)
            result = PlaywrightCaptureProvider(allow_localhost=True).capture(plan, Path(temp))
            images = [item for item in result.artifacts if item.type == "product_capture_image"]
            videos = [item for item in result.artifacts if item.type == "product_capture_video"]
            self.assertEqual(result.status, "ready")
            self.assertGreaterEqual(len({item.sha256 for item in images}), 3)
            self.assertGreaterEqual(len(videos), 1)
            self.assertTrue(all(Path(item.path).stat().st_size > 1000 for item in images + videos))
```

- [ ] **Step 2: Verify the provider is missing**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProductCaptureTest -v`

Expected: import error for `PlaywrightCaptureProvider`.

- [ ] **Step 3: Implement the automatic capture plan**

```python
def build_default_capture_plan(url: str) -> dict[str, Any]:
    return {
        "sourceUrl": url,
        "shots": [
            {"id": "hero", "url": url, "selector": "#hero", "action": "none", "viewport": [1440, 900], "duration": 3},
            {"id": "workflow", "url": url, "selector": "#workflow", "action": "scroll", "viewport": [1440, 900], "duration": 4},
            {"id": "features", "url": url, "selector": "#features", "action": "scroll", "viewport": [1440, 900], "duration": 4},
            {"id": "proof", "url": url, "selector": "#proof", "action": "scroll", "viewport": [1440, 900], "duration": 3},
            {"id": "cta", "url": url, "selector": "#cta", "action": "scroll", "viewport": [1440, 900], "duration": 3}
        ]
    }
```

Selectors missing on a real site fall back to `main`, `[role=main]`, then `body`, while the result records the fallback. Private paths and cross-origin targets fail before a browser is launched.

- [ ] **Step 4: Implement Playwright capture**

Create and close the recording context explicitly:

```python
video_dir = out_dir / "interaction-video"
video_dir.mkdir(parents=True, exist_ok=True)
context = browser.new_context(
    viewport={"width": 1440, "height": 900},
    record_video_dir=str(video_dir),
    record_video_size={"width": 1440, "height": 900},
)
page = context.new_page()
page.goto(plan["sourceUrl"], wait_until="domcontentloaded")
for shot in plan["shots"]:
    locator = resolve_capture_locator(page, shot["selector"])
    locator.scroll_into_view_if_needed()
    locator.screenshot(path=str(out_dir / f"{shot['id']}.png"))
    page.mouse.wheel(0, 520)
    page.wait_for_timeout(350)
video = page.video
context.close()
recorded_video = Path(video.path())
```

Record selector, final URL, viewport, and shot ID in artifact metadata.

- [ ] **Step 5: Run the capture test and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProductCaptureTest -v`

Expected: capture test passes with at least three unique PNG hashes and one non-empty WebM.

```powershell
git add scripts/media_pipeline/capture.py references/professional-media-fixture/product.html scripts/test_professional_media_pipeline.py
git commit -m "feat: capture real product interactions"
```

## Task 5: Generate professional local voiceover with Kokoro

**Files:**
- Create: `scripts/media_pipeline/voiceover.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing voice-selection and integration tests**

```python
class VoiceoverTest(unittest.TestCase):
    def test_kokoro_voice_selection_is_local_and_bilingual(self) -> None:
        self.assertEqual(voice_for_language("zh-CN"), ("zf_xiaobei", "zh"))
        self.assertEqual(voice_for_language("en"), ("af_heart", "en-us"))

    def test_kokoro_generates_nonempty_wav_when_installed(self) -> None:
        if not professional_tts_available():
            self.skipTest("Kokoro runtime is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            result = KokoroVoiceoverProvider().generate("把产品网页变成推广素材。", "zh-CN", Path(temp))
            self.assertEqual(result.status, "ready")
            self.assertGreater(Path(result.artifacts[0].path).stat().st_size, 4096)
            self.assertGreater(result.diagnostics["durationSeconds"], 0)
```

- [ ] **Step 2: Verify the new module is missing**

Run: `python -m unittest scripts.test_professional_media_pipeline.VoiceoverTest.test_kokoro_voice_selection_is_local_and_bilingual -v`

Expected: import error.

- [ ] **Step 3: Implement language selection and pinned model paths**

```python
VOICE_BY_LANGUAGE = {
    "zh-CN": ("zf_xiaobei", "zh"),
    "en": ("af_heart", "en-us"),
}


def voice_for_language(language: str) -> tuple[str, str]:
    return VOICE_BY_LANGUAGE.get(language, VOICE_BY_LANGUAGE["en"])
```

Resolve `kokoro-v1.0.onnx` and `voices-v1.0.bin` below the pinned local runtime root; do not fall back to an unpinned global model.

- [ ] **Step 4: Implement Kokoro and SAPI providers**

`KokoroVoiceoverProvider.generate()` imports `kokoro_onnx.Kokoro`, calls `Kokoro(model_path, voices_path).create(text, voice, speed=1.0, lang=lang)`, writes samples with `soundfile.write()`, verifies RIFF/WAVE bytes, obtains duration from ffprobe, and creates narration segments by distributing sentence lengths across the measured duration. `SapiVoiceoverProvider` reuses the existing PowerShell SAPI logic but returns `status="degraded"`, provider `windows_sapi`, and warning `review_voice_only`.

- [ ] **Step 5: Install core voice dependencies and run tests**

Run:

```powershell
python scripts/setup_professional_media.py --install-core
python -m unittest scripts.test_professional_media_pipeline.VoiceoverTest -v
```

Expected: both tests pass and the generated WAV is non-empty.

- [ ] **Step 6: Commit**

```powershell
git add scripts/media_pipeline/voiceover.py scripts/test_professional_media_pipeline.py
git commit -m "feat: generate local Kokoro voiceovers"
```

## Task 6: Generate AI photographic scenes and optional B-roll

**Files:**
- Create: `scripts/media_pipeline/scenes.py`
- Create: `references/comfyui/flux1-schnell-api.json`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing provider tests with a local fake HTTP server**

```python
class SceneProviderTest(unittest.TestCase):
    def test_comfyui_provider_submits_pinned_workflow_and_downloads_result(self) -> None:
        with fake_comfyui_server(PNG_BYTES) as base_url, tempfile.TemporaryDirectory() as temp:
            provider = ComfyUiFluxProvider(base_url, FLUX_WORKFLOW)
            result = provider.generate("premium SaaS workspace, cinematic light", 1080, 1080, 7, Path(temp))
            self.assertEqual(result.status, "ready")
            self.assertEqual(result.artifacts[0].source, "ai-generated")
            self.assertEqual(result.artifacts[0].license, "Apache-2.0")
            self.assertTrue(result.artifacts[0].metadata["aiGenerated"])

    def test_pexels_requires_key_but_never_reports_it(self) -> None:
        result = PexelsProvider(api_key="").search("software workflow", Path("C:/out"), 2)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "pexels_not_configured")
        self.assertNotIn("api_key", json.dumps(result.to_dict()))
```

- [ ] **Step 2: Run and verify imports fail**

Run: `python -m unittest scripts.test_professional_media_pipeline.SceneProviderTest -v`

Expected: import error for `media_pipeline.scenes`.

- [ ] **Step 3: Add the exact ComfyUI API workflow**

The JSON uses `CheckpointLoaderSimple` with `flux1-schnell-fp8.safetensors`, `CLIPTextEncode`, `EmptyLatentImage`, `KSampler` with `steps=4`, `cfg=1.0`, `sampler_name=euler`, `scheduler=simple`, `VAEDecode`, and `SaveImage`. Replace only prompt, seed, width, height, and filename prefix before submission.

- [ ] **Step 4: Implement ComfyUI health, submit, poll, and download**

```python
class ComfyUiFluxProvider:
    def health(self) -> bool:
        return read_json_url(f"{self.base_url}/system_stats", timeout=3) is not None

    def generate(self, prompt: str, width: int, height: int, seed: int, out_dir: Path) -> StageResult:
        if not self.health():
            return StageResult("skipped", "comfyui_flux", error_code="comfyui_unavailable")
        workflow = materialize_flux_workflow(self.workflow_path, prompt, width, height, seed)
        submitted = post_json(f"{self.base_url}/prompt", {"prompt": workflow, "client_id": str(uuid.uuid4())})
        history = poll_history(self.base_url, submitted["prompt_id"], timeout_seconds=600)
        image_ref = first_saved_image(history)
        target = out_dir / f"ai-product-scene-{seed}.png"
        target.write_bytes(download_comfyui_image(self.base_url, image_ref))
        artifact = Artifact.from_file("ai_scene", target, "comfyui_flux", "ai-generated", "Apache-2.0")
        return StageResult.ready("comfyui_flux", [replace(artifact, metadata={"aiGenerated": True, "seed": seed, "prompt": prompt})])
```

All HTTP calls target the configured loopback base URL by default. A non-loopback ComfyUI URL requires `allow_cloud_media` and goes through the cloud file policy.

- [ ] **Step 5: Implement Pexels metadata-preserving search**

Call `https://api.pexels.com/v1/search`, select landscape images, download to `b-roll_辅助镜头`, and record photographer, Pexels URL, original image URL, and `Pexels` license label. Never include the `Authorization` header in diagnostics.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.SceneProviderTest -v`

Expected: fake ComfyUI and unconfigured Pexels tests pass.

```powershell
git add scripts/media_pipeline/scenes.py references/comfyui/flux1-schnell-api.json scripts/test_professional_media_pipeline.py
git commit -m "feat: add AI scenes and B-roll providers"
```

## Task 7: Compose commercial covers, detail images, and contact sheets

**Files:**
- Create: `scripts/media_pipeline/visuals.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write a failing commercial-visual test**

```python
class CommercialVisualTest(unittest.TestCase):
    def test_compositor_uses_ai_scene_and_exact_product_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            background = make_test_image(root / "ai.png", (1200, 1200), "#203040")
            capture = make_test_image(root / "capture.png", (800, 500), "#ff3366")
            logo = make_test_image(root / "logo.png", (200, 100), "#ffffff")
            result = CommercialVisualCompositor().render(
                platform="xiaohongshu",
                title="把产品网页变成推广素材",
                subtitle="真实录屏 · 有声视频 · 商业视觉",
                background=background,
                product_capture=capture,
                logo=logo,
                out_dir=root / "out",
            )
            self.assertEqual(result.status, "ready")
            self.assertEqual(Image.open(result.artifacts[0].path).size, (1080, 1440))
            self.assertTrue(any(item.type == "contact_sheet" for item in result.artifacts))
            self.assertTrue(all(item.metadata["containsProductCapture"] for item in result.artifacts if item.type in {"cover_image", "detail_image"}))
```

- [ ] **Step 2: Verify the compositor is missing**

Run: `python -m unittest scripts.test_professional_media_pipeline.CommercialVisualTest -v`

Expected: import error.

- [ ] **Step 3: Implement the two-layer commercial composition**

Use the approved platform dimensions, `ImageOps.fit()` for the AI background, a dark gradient for text contrast, a rounded elevated product frame, exact unmodified screenshot paste, exact logo paste, and local CJK fonts from the existing font resolver. Do not draw a synthetic interface.

```python
PLATFORM_SIZES = {
    "youtube": (1920, 1080),
    "zhihu": (1200, 628),
    "xiaohongshu": (1080, 1440),
    "douyin": (1080, 1920),
    "github": (1280, 640),
}


def place_product_capture(canvas: Image.Image, capture: Image.Image, box: tuple[int, int, int, int]) -> None:
    fitted = ImageOps.contain(capture.convert("RGB"), (box[2] - box[0], box[3] - box[1]))
    x = box[0] + (box[2] - box[0] - fitted.width) // 2
    y = box[1] + (box[3] - box[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))
```

Create one cover, two to four platform-specific detail images, and one labeled contact sheet. Each artifact records `containsProductCapture`, `hasBrand`, `usesAiScene`, dimensions, and safe-margin results.

- [ ] **Step 4: Run tests and inspect the contact sheet**

Run: `python -m unittest scripts.test_professional_media_pipeline.CommercialVisualTest -v`

Expected: test passes; generated images have the expected dimensions and metadata.

- [ ] **Step 5: Commit**

```powershell
git add scripts/media_pipeline/visuals.py scripts/test_professional_media_pipeline.py
git commit -m "feat: compose commercial product visuals"
```

## Task 8: Render advanced HyperFrames product-demo video

**Files:**
- Create: `references/hyperframes-professional/index.html`
- Create: `references/hyperframes-professional/style.css`
- Create: `references/hyperframes-professional/composition.js`
- Create: `scripts/media_pipeline/video.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing project and ffprobe tests**

```python
class ProfessionalVideoTest(unittest.TestCase):
    def test_project_contains_five_shots_three_motion_types_and_local_gsap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            data = sample_composition_data(Path(temp))
            project = materialize_hyperframes_project(data, Path(temp) / "project")
            html = (project / "index.html").read_text(encoding="utf-8")
            script = (project / "composition.js").read_text(encoding="utf-8")
            self.assertNotIn("cdn.jsdelivr.net", html)
            self.assertGreaterEqual(len(data["shots"]), 5)
            self.assertIn("zoomPan", script)
            self.assertIn("productHighlight", script)
            self.assertIn("sceneTransition", script)

    def test_professional_render_has_h264_aac_and_non_silent_audio(self) -> None:
        if not professional_render_available():
            self.skipTest("HyperFrames/Kokoro/FFmpeg runtime unavailable")
        with tempfile.TemporaryDirectory() as temp:
            result = render_fixture_professional_video(Path(temp))
            probe = result.diagnostics["probe"]
            self.assertEqual(probe["videoCodec"], "h264")
            self.assertEqual(probe["audioCodec"], "aac")
            self.assertTrue(probe["nonSilent"])
            self.assertGreaterEqual(probe["shortEdge"], 1080)
```

- [ ] **Step 2: Verify the video module and templates are missing**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalVideoTest.test_project_contains_five_shots_three_motion_types_and_local_gsap -v`

Expected: import or file-not-found error.

- [ ] **Step 3: Build an offline, data-driven HyperFrames composition**

`index.html` declares `data-composition-id="root"`, `data-width`, `data-height`, `data-duration`, loads local `vendor/gsap.min.js`, and loads `composition.js`. `composition.js` reads `composition-data.json`, creates timed `.clip` elements for images/videos/audio/captions, and registers a paused timeline:

```javascript
const data = await fetch("./composition-data.json").then((response) => response.json());
const root = document.querySelector("#root");
const timeline = gsap.timeline({ paused: true });
const motionTypes = ["zoomPan", "productHighlight", "sceneTransition"];

for (const shot of data.shots) {
  const frame = document.createElement("section");
  frame.className = `clip shot ${shot.kind}`;
  frame.dataset.start = String(shot.start);
  frame.dataset.duration = String(shot.duration);
  frame.innerHTML = `<img src="${shot.src}" alt=""><div class="product-highlight"></div>`;
  root.appendChild(frame);
  timeline.fromTo(frame, { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1, duration: 0.45 }, shot.start);
  timeline.to(frame.querySelector("img"), { scale: 1.06, x: shot.panX, y: shot.panY, duration: shot.duration - 0.5 }, shot.start + 0.25);
  timeline.fromTo(frame.querySelector(".product-highlight"), { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.35 }, shot.start + 0.8);
  timeline.to(frame, { opacity: 0, duration: 0.35 }, shot.start + shot.duration - 0.35);
}

window.__timelines = window.__timelines || {};
window.__timelines.root = timeline;
```

Add a pointer path, brand intro/outro, and timed captions. CSS implements a glass product frame, gradient overlays, readable safe areas, and portrait/landscape variables.

- [ ] **Step 4: Implement project materialization and strict render**

Copy the templates, composition JSON, selected assets, and local `gsap.min.js` into a run-specific project. Run:

```python
command = [
    str(hyperframes_executable()),
    "render",
    str(project_dir),
    "--output",
    str(raw_video),
    "--quality",
    "high",
    "--workers",
    "1",
    "--low-memory-mode",
    "--strict",
    "--no-best-effort",
    "--resolution",
    resolution,
]
```

Then run FFmpeg `loudnorm=I=-16:LRA=11:TP=-1.5`, encode H.264/AAC, and inspect with ffprobe plus `volumedetect`. Return probe fields for codecs, streams, duration, dimensions, short edge, mean volume, max volume, and `nonSilent` where mean volume is greater than `-50 dB`.

- [ ] **Step 5: Run both video tests**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalVideoTest -v`

Expected: both tests pass; output contains H.264 video, AAC audio, short edge 1080, and non-silent audio.

- [ ] **Step 6: Commit**

```powershell
git add references/hyperframes-professional scripts/media_pipeline/video.py scripts/test_professional_media_pipeline.py
git commit -m "feat: render advanced product demo video"
```

## Task 9: Prove media quality from artifacts

**Files:**
- Create: `scripts/media_pipeline/quality.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write table-driven failing quality tests**

```python
class MediaQualityTest(unittest.TestCase):
    def test_professional_requires_every_video_and_visual_gate(self) -> None:
        evidence = complete_professional_evidence()
        report = evaluate_media_quality(evidence, target="professional")
        self.assertEqual(report["status"], "professional_ready")
        self.assertEqual(report["blockers"], [])

    def test_missing_ai_scene_downgrades_to_standard(self) -> None:
        evidence = complete_professional_evidence()
        evidence["aiScenes"] = []
        report = evaluate_media_quality(evidence, target="professional")
        self.assertEqual(report["status"], "standard_ready")
        self.assertIn("ai_photographic_scene_missing", report["blockers"])

    def test_missing_capture_or_visual_family_is_partial(self) -> None:
        evidence = complete_professional_evidence()
        evidence["productCaptures"] = []
        report = evaluate_media_quality(evidence, target="professional")
        self.assertEqual(report["status"], "partial_ready")
```

- [ ] **Step 2: Verify quality import fails**

Run: `python -m unittest scripts.test_professional_media_pipeline.MediaQualityTest -v`

Expected: import error.

- [ ] **Step 3: Implement explicit named checks**

```python
PROFESSIONAL_CHECKS = {
    "non_silent_voice": lambda e: bool(e["probe"].get("nonSilent")),
    "five_distinct_shots": lambda e: len(set(e["shotIds"])) >= 5,
    "three_product_captures": lambda e: len(set(e["productCaptureHashes"])) >= 3,
    "two_supporting_scenes": lambda e: len(set(e["supportingSceneHashes"])) >= 2,
    "three_motion_types": lambda e: {"zoomPan", "productHighlight", "sceneTransition"}.issubset(set(e["motionTypes"])),
    "captions_synced": lambda e: bool(e["captionsSynced"]),
    "short_edge_1080": lambda e: int(e["probe"].get("shortEdge", 0)) >= 1080,
    "h264_aac": lambda e: e["probe"].get("videoCodec") == "h264" and e["probe"].get("audioCodec") == "aac",
    "ai_photographic_scene": lambda e: any(item.get("aiGenerated") for item in e["aiScenes"]),
    "commercial_cover": lambda e: all(item.get("containsProductCapture") and item.get("hasBrand") for item in e["covers"]),
    "commercial_details": lambda e: bool(e["detailImages"]) and all(item.get("containsProductCapture") for item in e["detailImages"]),
    "contact_sheet": lambda e: bool(e["contactSheets"]),
}
```

Required artifact-family absence returns `partial_ready`. Otherwise any failed professional check returns `standard_ready`. SAPI or FFmpeg-only fallback caps the result at `standard_ready`. A template-only result returns `draft_ready`.

- [ ] **Step 4: Run tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.MediaQualityTest -v`

Expected: all quality cases pass.

```powershell
git add scripts/media_pipeline/quality.py scripts/test_professional_media_pipeline.py
git commit -m "feat: verify professional media quality"
```

## Task 10: Orchestrate resumable professional runs and update publish packs

**Files:**
- Create: `scripts/media_pipeline/orchestrator.py`
- Create: `scripts/professional_media_pipeline.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write a failing offline end-to-end test with fake providers**

```python
class ProfessionalPipelineTest(unittest.TestCase):
    def test_pipeline_writes_manifest_quality_and_compatible_publish_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = new_run_paths(Path(temp), "ENHE Product", now="20260723-120000").create()
            content, publish_pack = write_pipeline_inputs(paths)
            result = run_professional_pipeline(
                sample_job(paths, content, publish_pack),
                providers=fake_professional_providers(paths),
            )
            self.assertEqual(result["mediaQuality"]["status"], "professional_ready")
            self.assertTrue((paths.reports / "media-manifest.json").exists())
            self.assertTrue((paths.reports / "media-quality-report.json").exists())
            updated = json.loads(publish_pack.read_text(encoding="utf-8"))
            self.assertIn("video", updated[0])
            self.assertIn("cover", updated[0])
            self.assertIn("detailImages", updated[0])
            self.assertEqual(updated[0]["mediaQuality"]["status"], "professional_ready")
```

- [ ] **Step 2: Verify the orchestrator is missing**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalPipelineTest -v`

Expected: import error.

- [ ] **Step 3: Implement resumable stage execution**

```python
def run_stage(name: str, reports_dir: Path, producer: Callable[[], StageResult]) -> StageResult:
    result_path = reports_dir / "stages" / f"{name}.json"
    if result_path.exists():
        existing = StageResult.from_dict(json.loads(result_path.read_text(encoding="utf-8")))
        if stage_result_is_valid(existing):
            return existing
    result = producer()
    atomic_write_json(result_path, redact_secrets(result.to_dict()))
    return result
```

Execute capture, voiceover, AI/B-roll, visuals, video, manifest, and quality in dependency order. GPU-heavy AI and presenter stages never overlap. Product-demo video remains the default when presenter mode is `none`.

- [ ] **Step 4: Write the manifest and compatible publish-pack update**

Collect every artifact once by `(type, sha256)`, record provider and provenance, write `media-manifest.json`, evaluate quality, then attach:

```python
pack_item["video"] = video_record
pack_item["cover"] = cover_record
pack_item["detailImages"] = detail_records
pack_item["assets"] = [video_record, cover_record, *detail_records]
pack_item["mediaQuality"] = {
    "status": quality_report["status"],
    "report": str(quality_report_path),
    "target": job.quality_target,
}
```

Do not modify `published`, metrics, orders, revenue, or overall evidence status fields.

- [ ] **Step 5: Implement the direct CLI**

Required flags: `--product-url`, `--product-name`, `--content-json`, `--publish-pack`, `--run-dir`, `--language`, `--platforms`, `--brand-logo`, `--quality-target`, `--comfyui-url`, `--presenter`, `--presenter-asset`, `--portrait-authorized`, and `--allow-cloud-media`. Default target is `professional`; default presenter is `none`; cloud media is false.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalPipelineTest -v`

Expected: end-to-end fake-provider test passes and publication evidence remains untouched.

```powershell
git add scripts/media_pipeline/orchestrator.py scripts/professional_media_pipeline.py scripts/test_professional_media_pipeline.py
git commit -m "feat: orchestrate professional media runs"
```

## Task 11: Integrate the default Skill workflow and bilingual run root

**Files:**
- Modify: `scripts/render_video.py`
- Modify: `scripts/media_asset_pack.py`
- Modify: `scripts/run_promotion_workflow.py`
- Modify: `scripts/promotion_cycle_runner.py`
- Modify: `scripts/product_batch_runner.py`
- Modify: `scripts/final_capability_runner.py`
- Modify: `scripts/real_run_playbook.py`
- Modify: `scripts/skill_entry.py`
- Modify: `scripts/promotion_manager.py`
- Modify: `scripts/test_promotion_manager.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing CLI propagation and compatibility tests**

```python
class WorkflowIntegrationTest(unittest.TestCase):
    def test_skill_entry_defaults_to_bilingual_root_and_professional_media(self) -> None:
        module = load_script_module(SKILL_ENTRY)
        with patched_argv(["skill_entry.py", "--link", "https://example.com/product", "--link-mode", "product"]):
            args = module.parse_args()
        self.assertEqual(args.out_dir, "./promotion-output_推广输出")
        self.assertEqual(args.media_quality, "professional")
        self.assertEqual(args.presenter, "none")
        self.assertFalse(args.allow_cloud_media)

    def test_product_batch_run_uses_bilingual_runs_directory(self) -> None:
        run_dir = product_run_dir(Path("C:/output"), 1, "ENHE API", now="20260723-120000")
        self.assertEqual(run_dir, Path("C:/output/runs_运行记录/20260723-120000-001-enhe-api"))

    def test_draft_renderer_remains_callable(self) -> None:
        self.assertEqual(run_existing_draft_renderer(), 0)
```

- [ ] **Step 2: Run targeted tests and verify defaults fail**

Run: `python -m unittest scripts.test_professional_media_pipeline.WorkflowIntegrationTest -v`

Expected: assertions fail on `./promotion-output`, missing media flags, and legacy batch path.

- [ ] **Step 3: Add and forward the public flags**

At every high-level parser add the same names and choices:

```python
content.add_argument("--media-quality", choices=["draft", "standard", "professional"], default="professional")
content.add_argument("--brand-logo", default="")
content.add_argument("--comfyui-url", default="http://127.0.0.1:8188")
content.add_argument("--presenter", choices=["none", "musetalk", "heygen"], default="none")
content.add_argument("--presenter-asset", default="")
content.add_argument("--portrait-authorized", action="store_true")
content.add_argument("--allow-cloud-media", action="store_true")
```

Forward a flag only from parsed values; never read or forward credential values. Change only the high-level default output root to `./promotion-output_推广输出`.

- [ ] **Step 4: Replace the default batch directory and route generated media**

```python
def product_run_dir(output_root: Path, index: int, product_id: str, now: str | None = None) -> Path:
    timestamp = now or datetime.now().strftime("%Y%m%d-%H%M%S")
    return output_root / RUNS_DIR / f"{timestamp}-{index:03d}-{safe_id(product_id)}"
```

`run_promotion_workflow.py` invokes `professional_media_pipeline.py` once after content and publish-pack generation when `media_quality == "professional"`. The draft branch retains `render_video_artifacts()` and `run_media_asset_pack()` so old direct tests and low-resource review behavior remain valid:

```python
if args.media_quality == "professional":
    media_assets = run_professional_media(args, product, out_dir, steps)
    videos = media_assets.get("videos", [])
else:
    videos = render_video_artifacts(args, product, out_dir, steps)
    media_assets = run_media_asset_pack(args, product, out_dir, videos, steps)
```

`promotion_manager.py` adds `--generated-content-dir` and `--publish-pack-dir`. The workflow passes `RunPaths.generated_content` and `RunPaths.publish_packs`; the manager resolves them exactly once:

```python
generated_content_dir = Path(args.generated_content_dir) if args.generated_content_dir else report_dir(out_dir) / "generated-content"
publish_pack_dir = Path(args.publish_pack_dir) if args.publish_pack_dir else report_dir(out_dir) / "publish-packs"
generated_content_dir.mkdir(parents=True, exist_ok=True)
publish_pack_dir.mkdir(parents=True, exist_ok=True)
```

Other reporting paths remain unchanged within the bilingual run root for compatibility.

- [ ] **Step 5: Keep wrappers compatible**

`render_video.py --media-quality draft` remains the current deterministic renderer. `render_video.py --media-quality professional --media-job "$runDir\reports_报告\media-job.json"` delegates to `professional_media_pipeline.py`. `media_asset_pack.py --professional-manifest "$runDir\reports_报告\media-manifest.json"` attaches existing professional artifacts and never redraws them as cards.

- [ ] **Step 6: Run targeted and existing media regressions**

Run:

```powershell
python -m unittest scripts.test_professional_media_pipeline.WorkflowIntegrationTest -v
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_media_asset_pack_generates_required_assets_and_updates_publish_pack -v
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_video_renderer_creates_mp4_when_ffmpeg_exists -v
python -m unittest scripts.test_promotion_manager.PromotionManagerScriptTest.test_video_renderer_muxes_voiceover_audio_file -v
```

Expected: all tests pass; direct draft behavior remains unchanged.

- [ ] **Step 7: Commit**

```powershell
git add scripts/render_video.py scripts/media_asset_pack.py scripts/run_promotion_workflow.py scripts/promotion_cycle_runner.py scripts/product_batch_runner.py scripts/final_capability_runner.py scripts/real_run_playbook.py scripts/skill_entry.py scripts/promotion_manager.py scripts/test_promotion_manager.py scripts/test_professional_media_pipeline.py
git commit -m "feat: make professional media the default workflow"
```

## Task 12: Add optional presenter boundaries without weakening the default result

**Files:**
- Create: `scripts/media_pipeline/presenters.py`
- Modify: `scripts/media_pipeline/orchestrator.py`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing authorization and fallback tests**

```python
class PresenterProviderTest(unittest.TestCase):
    def test_presenter_requires_portrait_authorization(self) -> None:
        result = MuseTalkProvider(Path("C:/MuseTalk"), Path("C:/python.exe")).generate(
            Path("C:/portrait.png"), Path("C:/voice.wav"), Path("C:/out"), authorized=False
        )
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "portrait_authorization_required")

    def test_presenter_failure_does_not_downgrade_complete_product_demo(self) -> None:
        evidence = complete_professional_evidence()
        evidence["presenter"] = {"status": "failed", "errorCode": "musetalk_runtime_missing"}
        self.assertEqual(evaluate_media_quality(evidence, "professional")["status"], "professional_ready")

    def test_heygen_is_fail_closed_without_cloud_permission(self) -> None:
        result = HeyGenProvider().generate(Path("C:/portrait.png"), Path("C:/voice.wav"), Path("C:/out"), authorized=True, allow_cloud_media=False)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error_code, "cloud_media_not_allowed")
```

- [ ] **Step 2: Verify providers are missing**

Run: `python -m unittest scripts.test_professional_media_pipeline.PresenterProviderTest -v`

Expected: import error.

- [ ] **Step 3: Implement the MuseTalk command adapter**

Write an inference YAML containing only the allowlisted portrait and voiceover paths, then run the pinned local checkout with:

```python
command = [
    str(self.python),
    "-m",
    "scripts.inference",
    "--inference_config",
    str(config_path),
    "--result_dir",
    str(out_dir),
    "--unet_model_path",
    str(self.root / "models" / "musetalkV15" / "unet.pth"),
    "--unet_config",
    str(self.root / "models" / "musetalkV15" / "musetalk.json"),
    "--version",
    "v15",
    "--ffmpeg_path",
    str(Path(shutil.which("ffmpeg")).parent),
]
```

The adapter returns `skipped` when authorization, runtime, model, portrait, voice, VRAM, or free-memory checks fail. It never downloads test portraits because upstream test data is non-commercial.

- [ ] **Step 4: Implement HeyGen as a disabled-by-default boundary**

The provider requires portrait authorization, `allow_cloud_media`, an allowlisted portrait and voice file, and an explicit configured client injected by the caller. Without all five it returns a named `skipped` result. No HeyGen CLI installation, telemetry, upload, or network call occurs implicitly.

- [ ] **Step 5: Integrate presenter output as one optional shot**

Insert at most one presenter clip into the storyboard. If the presenter stage is skipped or failed, regenerate the shot list from product captures and supporting scenes and keep the product-demo quality decision independent.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.PresenterProviderTest -v`

Expected: all authorization and fallback tests pass.

```powershell
git add scripts/media_pipeline/presenters.py scripts/media_pipeline/orchestrator.py scripts/test_professional_media_pipeline.py
git commit -m "feat: add optional presenter adapters"
```

## Task 13: Document, install, and synchronize the Skill

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `README.en.md`
- Modify: `scripts/test_professional_media_pipeline.py`

- [ ] **Step 1: Write failing documentation contract tests**

```python
class ProfessionalMediaDocsTest(unittest.TestCase):
    def test_docs_explain_install_run_quality_and_cloud_boundary_in_both_languages(self) -> None:
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for text in (chinese, english, skill):
            self.assertIn("professional_ready", text)
            self.assertIn("--media-quality professional", text)
            self.assertIn("--allow-cloud-media", text)
            self.assertIn("promotion-output_推广输出", text)
```

- [ ] **Step 2: Run and verify documentation assertions fail**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalMediaDocsTest -v`

Expected: missing professional media commands and bilingual root assertions fail.

- [ ] **Step 3: Add exact setup and run commands in Chinese and English**

Document:

```powershell
python scripts/setup_professional_media.py --install-core
python scripts/setup_professional_media.py --install-comfyui
python scripts/skill_entry.py --link "https://www.enhe-tech.com.cn/promotion-manager" --link-mode product --media-quality professional --brand-logo "E:\AiProject\01.网站相关资料\LOGO\enhe_logo_final_exact_package\enhe_icon_gradient_transparent.png"
```

Explain outputs, status meanings, local-only defaults, AI source provenance, presenter authorization, Pexels configuration, ComfyUI lifecycle, low-memory behavior, and the difference between `mediaQuality.status` and real publishing/effect evidence.

- [ ] **Step 4: Update Skill instructions and synchronize the installed copy**

Add the new arguments and artifact locations to `SKILL.md`. Run the existing guarded sync path:

```powershell
python scripts/self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC --out-dir ".\promotion-output_推广输出"
```

Expected: the audit reports the repository and `C:\Users\HU\.codex\skills\viral-product-copy-video-generator` copies synchronized without exposing secrets.

- [ ] **Step 5: Run docs tests and commit**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalMediaDocsTest -v`

Expected: documentation contract passes.

```powershell
git add SKILL.md README.md README.zh-CN.md README.en.md scripts/test_professional_media_pipeline.py
git commit -m "docs: explain professional media workflow"
```

## Task 14: Install heavy runtime and pass deterministic end-to-end acceptance

**Files:**
- Modify only if a verified compatibility defect is discovered: files owned by Tasks 1-13
- Generate but do not commit: `%LOCALAPPDATA%\ENHE\professional-media\**`
- Generate but do not commit: `promotion-output_推广输出\runs_运行记录\**`

- [ ] **Step 1: Close nonessential memory-heavy applications and run health checks**

Run:

```powershell
python scripts/setup_professional_media.py --check
npx --yes hyperframes@0.7.68 doctor --json
nvidia-smi
```

Expected: FFmpeg, FFprobe, Chrome, Node, and disk checks pass; record free RAM and VRAM. Do not start ComfyUI and MuseTalk together.

- [ ] **Step 2: Install the pinned ComfyUI/FLUX runtime**

Run: `python scripts/setup_professional_media.py --install-comfyui`

Expected: exact Git commit is checked out, Python 3.12 venv exists, CUDA packages match the runtime manifest, the model receipt contains revision/size/SHA-256, and the model license is Apache-2.0.

- [ ] **Step 3: Start the local sidecar and prove one AI scene**

Run the setup script's printed argument-array equivalent of:

```powershell
& "$env:LOCALAPPDATA\ENHE\professional-media\comfyui-venv\Scripts\python.exe" "$env:LOCALAPPDATA\ENHE\professional-media\ComfyUI\main.py" --listen 127.0.0.1 --port 8188 --lowvram --disable-auto-launch
```

Then run: `python -m unittest scripts.test_professional_media_pipeline.SceneProviderRealSmokeTest -v`

Expected: one 1024px AI photographic scene is generated locally and manifest metadata says `aiGenerated=true`, provider `comfyui_flux`, license `Apache-2.0`.

- [ ] **Step 4: Run the deterministic local end-to-end fixture**

Run: `python -m unittest scripts.test_professional_media_pipeline.ProfessionalMediaEndToEndTest -v`

Expected: one bilingual run contains product captures, voiceover, AI scene, supporting scenes, professional MP4, covers, detail images, contact sheet, publish pack, manifest, and quality report; no cloud request is made.

- [ ] **Step 5: Run the focused suite and full regression suite**

Run:

```powershell
python -m unittest scripts.test_professional_media_pipeline -v
python scripts/test_promotion_manager.py
python scripts/test_mediacrawler_sidecar.py
```

Expected: focused professional tests pass; existing promotion and Sidecar regressions pass. Fix only failures caused by this implementation and rerun the failing command before rerunning the full suite.

- [ ] **Step 6: Commit any compatibility fixes separately**

If no compatibility fix was needed, do not create an empty commit. If a fix was needed:

```powershell
git add scripts/media_pipeline scripts/professional_media_pipeline.py scripts/render_video.py scripts/media_asset_pack.py scripts/run_promotion_workflow.py scripts/promotion_cycle_runner.py scripts/product_batch_runner.py scripts/final_capability_runner.py scripts/real_run_playbook.py scripts/skill_entry.py scripts/promotion_manager.py scripts/test_professional_media_pipeline.py scripts/test_promotion_manager.py
git commit -m "fix: preserve professional media compatibility"
```

## Task 15: Generate and audit one real ENHE professional sample

**Files:**
- Generate but do not commit: `promotion-output_推广输出\runs_运行记录\*\**`
- Modify only when acceptance evidence exposes an implementation defect: files owned by Tasks 1-14

- [ ] **Step 1: Select one public ENHE product page and run only that product**

Use the current public ENHE product URL selected from the repository/site evidence and run:

```powershell
python scripts/skill_entry.py --link "https://www.enhe-tech.com.cn/promotion-manager" --link-mode product --media-quality professional --brand-logo "E:\AiProject\01.网站相关资料\LOGO\enhe_logo_final_exact_package\enhe_icon_gradient_transparent.png" --skip-publish-queue
```

Expected: exactly one product run is created under `promotion-output_推广输出\runs_运行记录`; no live publication occurs.

- [ ] **Step 2: Inspect technical video evidence**

Run ffprobe and FFmpeg volume detection against the generated MP4. Verify H.264, AAC, duration 20-60 seconds unless platform content gives a documented override, short edge at least 1080, non-silent audio, five distinct shots, three distinct product captures, two supporting scenes, and the three required motion categories.

- [ ] **Step 3: Inspect commercial visuals**

Open the contact sheet and individual cover/detail images. Verify exact ENHE logo/product UI, correct Chinese text, photographic AI scene, readable hierarchy, no pure information cards, correct platform dimensions, and no invented product capability.

- [ ] **Step 4: Audit every goal requirement against authoritative files**

Confirm:

```text
1. Professional voiced MP4: media-quality report + ffprobe + visual inspection
2. AI commercial cover/details: manifest + image dimensions + contact-sheet inspection
3. Previous real-run outputs removed: exact old target paths do not exist
4. Bilingual output layout: new run tree exists; no new default legacy root was created
5. Skill/open-source upgrade: runtime receipt, pinned manifest, installed Skill sync audit
6. Privacy: cloud disabled, no Cookie/profile/token paths or values in reports
7. Publishing truth: overall workflow still reports unpublished/waiting evidence
```

- [ ] **Step 5: Fix and rerun any failed acceptance requirement**

Change only the component responsible for the failed evidence. Add a regression test reproducing the defect, run it red, implement the fix, rerun it green, rerun the real sample, and commit the focused fix.

- [ ] **Step 6: Record final evidence and absolute paths**

Report the exact run directory, MP4, contact sheet, cover/detail directory, `media-manifest.json`, `media-quality-report.json`, and Skill sync audit. Do not claim completion until every requirement in Step 4 has direct passing evidence.

## Plan self-review

The plan was checked against the approved design before handoff:

- Bilingual directory creation and legacy reads: Tasks 2, 10, 11, and 15.
- Media job, capture plan, stage results, hashes, atomic writes, provenance: Tasks 2, 3, 4, 6, and 10.
- Playwright product screenshots and interaction video: Task 4.
- Kokoro Chinese/English voiceover and truthful SAPI fallback: Task 5.
- Local ComfyUI/FLUX photographic AI scene, Pexels provenance, cloud-off default: Tasks 1, 3, 6, and 14.
- HyperFrames motion, captions, transitions, FFmpeg loudness, and ffprobe evidence: Task 8.
- Commercial covers, detail images, exact product/logo composition, and contact sheet: Task 7.
- Professional quality thresholds and honest downgrade states: Task 9.
- Resumability, provider failure handling, and publish-pack compatibility: Tasks 3, 9, and 10.
- Optional MuseTalk/HeyGen authorization and fail-closed behavior: Task 12.
- Skill/README installation and bilingual usage documentation: Task 13.
- Low-memory/GPU serialization, runtime installation, deterministic tests, and real ENHE smoke evidence: Tasks 1, 8, 14, and 15.
- No automatic publishing, no Hosted Worker enablement, no payment changes, and no unsupported traffic/revenue claims: Tasks 10, 11, 13, and 15.

No unresolved placeholder, duplicate task, or conflicting field name remains. The plan uses `media_quality` for CLI arguments and `mediaQuality` for JSON, while publication/evidence statuses remain separate. The only intentionally optional path is the presenter; the required professional result is satisfied by the real product demonstration plus AI photographic scene path.

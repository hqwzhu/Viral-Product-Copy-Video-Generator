from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.media_pipeline.contracts import Artifact, StageResult
from scripts.setup_professional_media import default_runtime_root


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_REFERENCE = REPO_ROOT / "references" / "professional-media-runtime.json"
VOICE_BY_LANGUAGE = {
    "zh-CN": ("zf_xiaobei", "zh"),
    "en": ("af_heart", "en-us"),
}
_ENGLISH_VOICE = VOICE_BY_LANGUAGE["en"]


def voice_for_language(language: str) -> tuple[str, str]:
    return VOICE_BY_LANGUAGE.get(language, _ENGLISH_VOICE)


def _runtime_python(root: Path) -> Path:
    if os.name == "nt":
        return root / "core" / ".venv" / "Scripts" / "python.exe"
    return root / "core" / ".venv" / "bin" / "python"


def _runtime_assets(root: Path) -> tuple[tuple[Path, int, str], ...]:
    manifest = json.loads(RUNTIME_REFERENCE.read_text(encoding="utf-8"))
    model_root = root / "models" / "kokoro"
    return tuple(
        (
            model_root / item["filename"],
            item["sizeBytes"],
            item["sha256"],
        )
        for item in manifest["kokoro"]["model"]["files"]
    )


def _matches_integrity(path: Path, size: int, sha256: str) -> bool:
    try:
        if not path.is_file() or path.stat().st_size != size:
            return False
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest().lower() == sha256.lower()
    except OSError:
        return False


def professional_tts_available(runtime_root: str | Path | None = None) -> bool:
    try:
        root = (
            Path(runtime_root)
            if runtime_root is not None
            else default_runtime_root()
        )
        if not all(_matches_integrity(*asset) for asset in _runtime_assets(root)):
            return False
        python = _runtime_python(root)
        if not python.is_file() or shutil.which("ffprobe") is None:
            return False
        subprocess.run(
            [str(python), "-c", "import kokoro_onnx, soundfile"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
            timeout=30,
        )
        return True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return False


def _synthesize_kokoro(
    runtime_root: Path,
    text: str,
    voice: str,
    lang: str,
    destination: Path,
) -> None:
    model, voices = (asset[0] for asset in _runtime_assets(runtime_root))
    # Keep the worker request ASCII-only so Windows' stdin code page cannot
    # turn user text into surrogate characters before json.loads decodes it.
    payload = json.dumps({"text": text, "voice": voice, "lang": lang})
    subprocess.run(
        [
            str(_runtime_python(runtime_root)),
            "-m",
            "scripts.media_pipeline.voiceover",
            "--kokoro-worker",
            str(model),
            str(voices),
            str(destination),
        ],
        cwd=REPO_ROOT,
        input=payload,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        shell=False,
        timeout=300,
    )


def _run_kokoro_worker(model: Path, voices: Path, destination: Path) -> None:
    from kokoro_onnx import Kokoro
    import soundfile

    request = json.loads(sys.stdin.read())
    kokoro = Kokoro(str(model), str(voices))
    # phonemizer's espeak backend names Mandarin Chinese "cmn"; the public
    # contract intentionally keeps the compact "zh" language value.
    api_lang = "cmn" if request["lang"] == "zh" else request["lang"]
    samples, sample_rate = kokoro.create(
        request["text"], request["voice"], speed=1.0, lang=api_lang
    )
    soundfile.write(
        str(destination), samples, sample_rate, format="WAV", subtype="PCM_16"
    )


def _synthesize_windows_sapi(text: str, destination: Path) -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        raise FileNotFoundError("PowerShell is unavailable")
    destination.parent.mkdir(parents=True, exist_ok=True)
    script = """
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Speech
$text = [Console]::In.ReadToEnd()
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $synth.Rate = 0
  $synth.Volume = 100
  $synth.SetOutputToWaveFile($env:ENHE_SAPI_WAV)
  $synth.Speak($text)
} finally {
  $synth.Dispose()
}
""".strip()
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    environment = os.environ.copy()
    environment["ENHE_SAPI_WAV"] = str(destination)
    subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        input=text,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        shell=False,
        timeout=120,
    )


def _validate_wav(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= 44:
        raise RuntimeError("Voiceover WAV is missing or empty")
    with path.open("rb") as audio:
        header = audio.read(12)
    if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        raise RuntimeError("Voiceover output is not a valid WAV")


def _audio_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is unavailable")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=30,
    )
    duration = float(result.stdout.strip())
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError("Voiceover duration is not positive")
    return duration


def _sentence_segments(text: str, duration: float) -> list[dict[str, Any]]:
    sentences = [part.strip() for part in re.split(r"[。！？.!?]+", text) if part.strip()]
    if not sentences:
        return []
    weights = [len(re.sub(r"\s+", "", sentence)) or 1 for sentence in sentences]
    total = sum(weights)
    segments = []
    start = 0.0
    for index, (sentence, weight) in enumerate(zip(sentences, weights)):
        end = duration if index == len(sentences) - 1 else start + duration * weight / total
        segments.append({"text": sentence, "start": start, "end": end})
        start = end
    return segments


def _artifact(
    path: Path,
    provider: str,
    license_id: str,
    metadata: dict[str, str],
) -> Artifact:
    artifact = Artifact.from_file(
        "voiceover_audio",
        path,
        provider=provider,
        source="generated",
        license_id=license_id,
    )
    return replace(artifact, metadata=metadata)


def _diagnostics(
    text: str,
    duration: float,
    voice: str,
    language: str,
    lang: str,
) -> dict[str, Any]:
    return {
        "durationSeconds": duration,
        "segments": _sentence_segments(text, duration),
        "voice": voice,
        "language": language,
        "lang": lang,
    }


def _segments_are_valid(segments: list[dict[str, Any]], duration: float) -> bool:
    if not segments or not math.isfinite(duration) or duration <= 0:
        return False
    previous_end = 0.0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or not str(segment.get("text", "")).strip():
            return False
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            return False
        if (
            not math.isfinite(start)
            or not math.isfinite(end)
            or start < 0
            or start > end
            or end > duration
            or (index == 0 and not math.isclose(start, 0.0, abs_tol=1e-6))
            or (index > 0 and not math.isclose(start, previous_end, abs_tol=1e-6))
        ):
            return False
        previous_end = end
    return math.isclose(previous_end, duration, rel_tol=1e-6, abs_tol=1e-6)


def _has_readable_text(text: str) -> bool:
    return any(character.isalnum() or character.isalpha() for character in text)


class KokoroVoiceoverProvider:
    def __init__(self, runtime_root: str | Path | None = None) -> None:
        self.runtime_root = (
            Path(runtime_root)
            if runtime_root is not None
            else default_runtime_root()
        )

    def generate(self, text: str, language: str, output_dir: str | Path) -> StageResult:
        normalized = text.strip()
        if not normalized:
            return StageResult(
                status="failed",
                provider="kokoro_onnx",
                error_code="empty_voiceover_text",
            )
        if not _has_readable_text(normalized):
            return StageResult(
                status="failed",
                provider="kokoro_onnx",
                error_code="unreadable_voiceover_text",
            )
        if not professional_tts_available(self.runtime_root):
            return StageResult(
                status="failed",
                provider="kokoro_onnx",
                error_code="tts_runtime_unavailable",
            )
        voice, lang = voice_for_language(language)
        destination = Path(output_dir) / "voiceover.wav"
        partial = destination.with_name("voiceover.part.wav")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            partial.unlink(missing_ok=True)
            _synthesize_kokoro(
                self.runtime_root, normalized, voice, lang, partial
            )
            _validate_wav(partial)
            duration = _audio_duration(partial)
            partial.replace(destination)
            metadata = {"voice": voice, "language": language, "lang": lang}
            diagnostics = _diagnostics(normalized, duration, voice, language, lang)
            if not _segments_are_valid(diagnostics["segments"], duration):
                raise RuntimeError("Voiceover segments are invalid")
            artifact = _artifact(destination, "kokoro_onnx", "Apache-2.0", metadata)
            return StageResult.ready(
                "kokoro_onnx",
                (artifact,),
                diagnostics,
            )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            partial.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            return StageResult(
                status="failed",
                provider="kokoro_onnx",
                error_code="tts_generation_failed",
            )


class SapiVoiceoverProvider:
    def generate(self, text: str, language: str, output_dir: str | Path) -> StageResult:
        normalized = text.strip()
        if not normalized:
            return StageResult(
                status="failed",
                provider="windows_sapi",
                error_code="empty_voiceover_text",
            )
        if not _has_readable_text(normalized):
            return StageResult(
                status="failed",
                provider="windows_sapi",
                error_code="unreadable_voiceover_text",
            )
        if shutil.which("powershell") is None and shutil.which("pwsh") is None:
            return StageResult(
                status="failed",
                provider="windows_sapi",
                error_code="sapi_unavailable",
            )
        destination = Path(output_dir) / "voiceover-sapi.wav"
        partial = destination.with_name("voiceover-sapi.part.wav")
        voice, lang = "windows_default", voice_for_language(language)[1]
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            partial.unlink(missing_ok=True)
            _synthesize_windows_sapi(normalized, partial)
            _validate_wav(partial)
            duration = _audio_duration(partial)
            partial.replace(destination)
            metadata = {"voice": voice, "language": language, "lang": lang}
            diagnostics = _diagnostics(normalized, duration, voice, language, lang)
            if not _segments_are_valid(diagnostics["segments"], duration):
                raise RuntimeError("Voiceover segments are invalid")
            artifact = _artifact(destination, "windows_sapi", "", metadata)
            return StageResult(
                status="degraded",
                provider="windows_sapi",
                artifacts=(artifact,),
                warnings=("review_voice_only",),
                diagnostics=diagnostics,
            )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            partial.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            return StageResult(
                status="failed",
                provider="windows_sapi",
                error_code="sapi_generation_failed",
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kokoro-worker",
        nargs=3,
        metavar=("MODEL", "VOICES", "DESTINATION"),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.kokoro_worker:
        model, voices, destination = map(Path, args.kokoro_worker)
        _run_kokoro_worker(model, voices, destination)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

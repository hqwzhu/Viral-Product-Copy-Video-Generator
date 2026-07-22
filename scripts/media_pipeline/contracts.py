import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def atomic_write_json(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary.replace(destination)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))

    @classmethod
    def from_file(
        cls,
        artifact_type: str,
        path: str | Path,
        provider: str,
        source: str,
        license_id: str = "",
    ) -> "Artifact":
        resolved = Path(path).resolve()
        with resolved.open("rb") as handle:
            sha256 = hashlib.file_digest(handle, "sha256").hexdigest()
        return cls(
            type=artifact_type,
            path=str(resolved),
            sha256=sha256,
            source=source,
            license=license_id,
            provider=provider,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "path": self.path,
            "sha256": self.sha256,
            "source": self.source,
            "license": self.license,
            "provider": self.provider,
            "containsUserData": self.contains_user_data,
            "metadata": _thaw_json(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Artifact":
        return cls(
            type=value["type"],
            path=value["path"],
            sha256=value["sha256"],
            source=value["source"],
            license=value["license"],
            provider=value["provider"],
            contains_user_data=value["containsUserData"],
            metadata=dict(value["metadata"]),
        )


@dataclass(frozen=True)
class StageResult:
    status: Literal["ready", "degraded", "failed", "skipped"]
    provider: str
    artifacts: tuple[Artifact, ...] = ()
    warnings: tuple[str, ...] = ()
    error_code: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "diagnostics", _freeze_json(self.diagnostics))

    @classmethod
    def ready(
        cls,
        provider: str,
        artifacts: tuple[Artifact, ...] | list[Artifact],
        diagnostics: dict[str, Any] | None = None,
    ) -> "StageResult":
        return cls(
            status="ready",
            provider=provider,
            artifacts=tuple(artifacts),
            diagnostics=dict(diagnostics or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider": self.provider,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "warnings": list(self.warnings),
            "errorCode": self.error_code,
            "diagnostics": _thaw_json(self.diagnostics),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "StageResult":
        return cls(
            status=value["status"],
            provider=value["provider"],
            artifacts=tuple(
                Artifact.from_dict(artifact) for artifact in value["artifacts"]
            ),
            warnings=tuple(value["warnings"]),
            error_code=value["errorCode"],
            diagnostics=dict(value["diagnostics"]),
        )


@dataclass(frozen=True)
class MediaJob:
    run_id: str
    product_name: str
    source_url: str
    language: str
    target_platforms: tuple[str, ...]
    quality_target: str
    aspect_ratios: tuple[str, ...]
    duration_range: tuple[int, int]
    providers: dict[str, str]
    allow_cloud_media: bool
    product_data_path: str
    brand_assets: tuple[str, ...]
    generated_content_path: str
    capture_plan_path: str
    presenter: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_platforms", tuple(self.target_platforms))
        object.__setattr__(self, "aspect_ratios", tuple(self.aspect_ratios))
        object.__setattr__(self, "duration_range", tuple(self.duration_range))
        object.__setattr__(self, "providers", _freeze_json(self.providers))
        object.__setattr__(self, "brand_assets", tuple(self.brand_assets))

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "productName": self.product_name,
            "sourceUrl": self.source_url,
            "language": self.language,
            "targetPlatforms": list(self.target_platforms),
            "qualityTarget": self.quality_target,
            "aspectRatios": list(self.aspect_ratios),
            "durationRange": list(self.duration_range),
            "providers": _thaw_json(self.providers),
            "allowCloudMedia": self.allow_cloud_media,
            "productDataPath": self.product_data_path,
            "brandAssets": list(self.brand_assets),
            "generatedContentPath": self.generated_content_path,
            "capturePlanPath": self.capture_plan_path,
            "presenter": self.presenter,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MediaJob":
        return cls(
            run_id=value["runId"],
            product_name=value["productName"],
            source_url=value["sourceUrl"],
            language=value["language"],
            target_platforms=tuple(value["targetPlatforms"]),
            quality_target=value["qualityTarget"],
            aspect_ratios=tuple(value["aspectRatios"]),
            duration_range=tuple(value["durationRange"]),
            providers=dict(value["providers"]),
            allow_cloud_media=value["allowCloudMedia"],
            product_data_path=value["productDataPath"],
            brand_assets=tuple(value["brandAssets"]),
            generated_content_path=value["generatedContentPath"],
            capture_plan_path=value["capturePlanPath"],
            presenter=value["presenter"],
        )

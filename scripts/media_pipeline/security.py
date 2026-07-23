import ipaddress
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


class MediaSecurityError(ValueError):
    pass


DENIED_ROUTE_PARTS = (
    "/account",
    "/admin",
    "/billing",
    "/checkout",
    "/payment",
)
SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|token|secret|cookie|authorization)", re.I
)

_DEFAULT_PORTS = {"http": 80, "https": 443}
_MAX_PATH_DECODE_PASSES = 8
_NONSTANDARD_IPV4_PATTERN = re.compile(
    r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*",
    re.I,
)
_URL_CONTROL_PATTERN = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_SENSITIVE_PATH_NAMES = {
    "cookie",
    "cookies",
    "user data",
    "login data",
    "web data",
    "local state",
    "chrome",
    "edge",
    "bravesoftware",
    "firefox",
    "mozilla",
    "default",
}
_SENSITIVE_PATH_WORDS = {
    "cookie",
    "cookies",
    "token",
    "credential",
    "credentials",
    "password",
    "authorization",
}


def _parsed_origin(url: str) -> tuple[str, str, int, str]:
    if not isinstance(url, str) or "\\" in url or _URL_CONTROL_PATTERN.search(url):
        raise MediaSecurityError("Ambiguous capture URL")
    parsed = urlsplit(url)
    scheme = parsed.scheme.casefold()
    if scheme not in _DEFAULT_PORTS or not parsed.hostname:
        raise MediaSecurityError("Capture URLs must use HTTP or HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise MediaSecurityError("Capture URLs cannot contain user information")
    hostname = parsed.hostname.casefold().rstrip(".")
    if not hostname:
        raise MediaSecurityError("Capture URL hostname is required")
    if "%" in hostname or not hostname.isascii():
        raise MediaSecurityError("Capture URL hostname must be canonical ASCII")
    port = parsed.port if parsed.port is not None else _DEFAULT_PORTS[scheme]
    return scheme, hostname, port, parsed.path


def _is_loopback(hostname: str) -> bool:
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if _NONSTANDARD_IPV4_PATTERN.fullmatch(hostname):
            raise MediaSecurityError("Non-canonical numeric IP address")
        return False
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        return address.is_loopback or address.ipv4_mapped.is_loopback
    return address.is_loopback


def _normalized_capture_path(path: str) -> str:
    current = path
    for _ in range(_MAX_PATH_DECODE_PASSES):
        if "\\" in current or _URL_CONTROL_PATTERN.search(current):
            raise MediaSecurityError("Ambiguous capture path")
        decoded = unquote(current)
        if decoded == current:
            return current.casefold()
        current = decoded

    if "\\" in current or _URL_CONTROL_PATTERN.search(current):
        raise MediaSecurityError("Ambiguous capture path")
    if unquote(current) != current:
        raise MediaSecurityError("Capture path exceeds decode limit")
    return current.casefold()


def validate_capture_shot(
    source_url: str,
    shot: Mapping[str, Any],
    allow_localhost: bool = False,
) -> None:
    try:
        if not isinstance(shot, Mapping):
            raise MediaSecurityError("Capture shot must be a mapping")
        action = shot.get("action")
        if action not in (None, "none", "click", "scroll"):
            raise MediaSecurityError("Unsupported capture action")

        target_url = shot.get("url", source_url)
        source = _parsed_origin(source_url)
        target = _parsed_origin(target_url)
        if source[:3] != target[:3]:
            raise MediaSecurityError("Capture target must use the source origin")
        source_is_loopback = _is_loopback(source[1])
        target_is_loopback = _is_loopback(target[1])
        if allow_localhost is not True and (
            source_is_loopback or target_is_loopback
        ):
            raise MediaSecurityError("Localhost capture requires explicit permission")

        for path in (source[3], target[3]):
            normalized_path = _normalized_capture_path(path)
            if any(part in normalized_path for part in DENIED_ROUTE_PARTS):
                raise MediaSecurityError("Private routes cannot be captured")
    except MediaSecurityError:
        raise
    except Exception as exc:
        raise MediaSecurityError("Invalid capture request") from exc


def _normalized_path_part(part: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", unquote(part).casefold()).split())


def _path_is_sensitive(path: Path) -> bool:
    for part in path.parts:
        normalized = _normalized_path_part(part)
        words = set(normalized.split())
        padded = f" {normalized} "
        if any(f" {name} " in padded for name in _SENSITIVE_PATH_NAMES):
            return True
        if words & _SENSITIVE_PATH_WORDS:
            return True
        if re.search(r"(?:^| )profile [0-9]+(?: |$)", normalized):
            return True
    return False


def cloud_file_allowed(
    path: str | Path,
    allow_cloud_media: bool,
    allowlist: list[str | Path] | tuple[str | Path, ...],
) -> bool:
    if allow_cloud_media is not True:
        return False
    try:
        candidate = Path(path).resolve(strict=False)
        allowed = {Path(item).resolve(strict=False) for item in allowlist}
        return candidate in allowed and not _path_is_sensitive(candidate)
    except (OSError, TypeError, ValueError):
        return False


def redact_secrets(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: (
                "[REDACTED]"
                if SECRET_KEY_PATTERN.search(str(key))
                else redact_secrets(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_secrets(item) for item in value]
    return value

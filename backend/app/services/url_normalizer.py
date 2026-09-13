"""URL validation and normalization — ported from Phase 1."""
import re
import ipaddress
from urllib.parse import urlparse, urlunparse, unquote
from posixpath import normpath
from dataclasses import dataclass

import idna

from app.config import get_settings


@dataclass
class URLValidationResult:
    is_valid: bool
    original_url: str
    normalized_url: str | None = None
    error: str | None = None


def validate_url(url: str) -> URLValidationResult:
    """Validate and normalize a raw URL string."""
    if not url or not isinstance(url, str) or not url.strip():
        return URLValidationResult(False, str(url) if url else "", error="empty_url")

    url = url.strip()
    max_len = get_settings().max_url_length

    if len(url) > max_len:
        return URLValidationResult(False, url, error="url_too_long")

    # Add scheme if missing
    if not re.match(r"^https?://", url, re.IGNORECASE):
        if url.startswith("//"):
            url = "http:" + url
        elif "://" not in url:
            url = "http://" + url
        else:
            return URLValidationResult(False, url, error="unsupported_scheme")

    try:
        parsed = urlparse(url)
    except Exception:
        return URLValidationResult(False, url, error="parse_error")

    if not parsed.hostname:
        return URLValidationResult(False, url, error="no_hostname")

    if parsed.scheme.lower() not in ("http", "https"):
        return URLValidationResult(False, url, error="unsupported_scheme")

    try:
        normalized = normalize_url(url)
    except Exception as e:
        return URLValidationResult(False, url, error=f"normalization_error: {e}")

    return URLValidationResult(True, url, normalized_url=normalized)


def normalize_url(url: str) -> str:
    """
    Normalize a URL:
    - Lowercase scheme and hostname
    - Decode percent-encoding in path
    - Resolve /../ in path
    - Strip trailing slash (keep root /)
    - Strip default port
    - Handle punycode/IDN
    """
    url = url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        if url.startswith("//"):
            url = "http:" + url
        elif "://" not in url:
            url = "http://" + url

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = _normalize_hostname(parsed.hostname or "")

    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None
    netloc = hostname
    if port:
        netloc = f"{hostname}:{port}"
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        netloc = f"{userinfo}@{netloc}"

    path = unquote(parsed.path) if parsed.path else "/"
    path = normpath(path)
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))


def _normalize_hostname(hostname: str) -> str:
    if not hostname:
        return hostname
    try:
        ipaddress.ip_address(hostname)
        return hostname
    except ValueError:
        pass
    try:
        if hostname.startswith("xn--") or ".xn--" in hostname:
            hostname = idna.decode(hostname)
    except (idna.core.InvalidCodepoint, UnicodeError, UnicodeDecodeError):
        pass
    return hostname.lower()


def batch_validate_and_normalize(urls: list[str]) -> list[URLValidationResult]:
    """Validate and normalize a list of URLs."""
    return [validate_url(u) for u in urls]

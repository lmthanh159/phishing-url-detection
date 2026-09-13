"""Tests for URL normalizer service."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.services.url_normalizer import validate_url, normalize_url


class TestValidation:
    def test_empty(self):
        assert not validate_url("").is_valid
        assert validate_url("").error == "empty_url"

    def test_none(self):
        assert not validate_url(None).is_valid

    def test_whitespace(self):
        assert not validate_url("   ").is_valid

    def test_valid_http(self):
        r = validate_url("http://example.com")
        assert r.is_valid and r.normalized_url

    def test_valid_https(self):
        assert validate_url("https://example.com/login").is_valid

    def test_missing_scheme(self):
        r = validate_url("example.com/path")
        assert r.is_valid
        assert r.normalized_url.startswith("http://")

    def test_ftp_rejected(self):
        r = validate_url("ftp://example.com")
        assert not r.is_valid
        assert r.error == "unsupported_scheme"

    def test_too_long(self):
        r = validate_url("http://example.com/" + "a" * 10000)
        assert not r.is_valid
        assert r.error == "url_too_long"

    def test_ip_url(self):
        assert validate_url("http://192.168.1.1/login").is_valid

    def test_punycode(self):
        assert validate_url("http://xn--pple-43d.com").is_valid


class TestNormalization:
    def test_lowercase(self):
        assert normalize_url("HTTP://Example.COM/login/") == "http://example.com/login"

    def test_resolve_dotdot(self):
        assert normalize_url("http://example.com/a/../login") == "http://example.com/login"

    def test_decode_percent(self):
        assert normalize_url("http://example.com/%6c%6f%67%69%6e") == "http://example.com/login"

    def test_strip_port_80(self):
        assert ":80" not in normalize_url("http://example.com:80/path")

    def test_strip_port_443(self):
        assert ":443" not in normalize_url("https://example.com:443/path")

    def test_keep_non_default_port(self):
        assert ":8080" in normalize_url("http://example.com:8080/path")

    def test_strip_trailing_slash(self):
        assert normalize_url("http://example.com/path/") == "http://example.com/path"

    def test_keep_root(self):
        assert normalize_url("http://example.com/") == "http://example.com/"

    def test_at_symbol_preserved(self):
        r = normalize_url("http://user@example.com/path")
        assert "user@" in r

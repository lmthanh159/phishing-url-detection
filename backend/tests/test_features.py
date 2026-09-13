"""Tests for feature extractor service."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.services.feature_extractor import extract_features, extract_features_final


class TestV1Features:
    def test_https_detection(self):
        f = extract_features("https://example.com")
        assert f["has_https"] == 1
        f2 = extract_features("http://example.com")
        assert f2["has_https"] == 0

    def test_ip_detection(self):
        f = extract_features("http://192.168.1.1/login")
        assert f["has_ip_address"] == 1

    def test_login_keyword(self):
        f = extract_features("http://example.com/user-login")
        assert f["has_login_keyword"] == 1

    def test_no_keyword(self):
        f = extract_features("http://example.com/about")
        assert f["has_login_keyword"] == 0

    def test_subdomain_count(self):
        f = extract_features("http://a.b.c.example.com")
        assert f["subdomain_count"] == 3

    def test_brand_in_url(self):
        f = extract_features("http://paypal-login.example.com")
        assert f["contains_brand_token"] == 1
        assert f["brand_not_in_registered_domain"] == 1

    def test_suspicious_tld(self):
        f = extract_features("http://example.xyz/login")
        assert f["is_suspicious_tld"] == 1

    def test_shortener(self):
        f = extract_features("http://bit.ly/abc123")
        assert f["has_url_shortener"] == 1

    def test_entropy_positive(self):
        f = extract_features("http://a8x2kf9m.example.com/p?q=1")
        assert f["url_entropy"] > 0


class TestV2Features:
    def test_token_count(self):
        f = extract_features("http://secure-login-paypal.example.com/update")
        assert f["token_count"] >= 4

    def test_path_depth(self):
        f = extract_features("http://example.com/a/b/c/login")
        assert f["path_depth"] == 4

    def test_brand_distance_typosquatting(self):
        f = extract_features("http://paypa1.com/login")
        assert f["brand_levenshtein_min_distance"] < 30

    def test_interaction_http_login(self):
        f = extract_features("http://example.com/login")
        assert f["http_and_login_keyword"] == 1

    def test_interaction_https_no_flag(self):
        f = extract_features("https://example.com/login")
        assert f["http_and_login_keyword"] == 0


class TestFinalFS:
    def test_final_output_count(self):
        # Should match feature_schema.json — but we test with known list
        f = extract_features("http://example.com")
        assert len(f) >= 37  # V1 (37) + V2 extras

    def test_final_fs_subset(self):
        all_f = extract_features("http://example.com")
        # brand_levenshtein_min_distance should exist (the one V2 feature kept)
        assert "brand_levenshtein_min_distance" in all_f

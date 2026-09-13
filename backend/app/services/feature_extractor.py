"""Feature extraction from normalized URLs — ported from Phase 1."""
import re
import math
import string
import ipaddress
from urllib.parse import urlparse
from collections import Counter

import numpy as np
import pandas as pd
import tldextract
from rapidfuzz import fuzz

from app.config import (
    get_brand_list, get_brand_official_domains,
    BRAND_SIMILARITY_THRESHOLD, BRAND_MIN_TOKEN_LENGTH,
    SUSPICIOUS_TLDS, URL_SHORTENERS, SUSPICIOUS_KEYWORDS,
    get_feature_schema,
)

_VOWELS = set("aeiou")
_CONSONANTS = set("bcdfghjklmnpqrstvwxyz")
_SPECIAL_CHARS = set(string.punctuation) - set(".-_/~")
_TOKEN_SPLIT_RE = re.compile(r"[.\-_/?&=]+")
_IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$|^\[?[0-9a-fA-F:]+\]?$")
_ENCODED_RE = re.compile(r"%[0-9a-fA-F]{2}")
_DOUBLE_SLASH_RE = re.compile(r"//.*//")
_TLD_EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


# ── Helpers ──

def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _is_gibberish_token(token: str) -> bool:
    if len(token) < 4:
        return False
    alpha = [c for c in token.lower() if c.isalpha()]
    if len(alpha) < 3:
        return len(token) >= 5
    ratio = sum(1 for c in alpha if c in _VOWELS) / len(alpha)
    if ratio < 0.1 or ratio > 0.8:
        return True
    transitions = sum(
        1 for i in range(len(token) - 1)
        if token[i].isdigit() != token[i + 1].isdigit()
        and token[i].isalnum() and token[i + 1].isalnum()
    )
    return transitions >= 3


def _randomness_score(s: str) -> float:
    if not s or len(s) < 2:
        return 0.0
    def cc(c):
        if c.isdigit(): return 0
        if c.islower(): return 1
        if c.isupper(): return 2
        return 3
    transitions = sum(1 for i in range(len(s) - 1) if cc(s[i]) != cc(s[i + 1]))
    return round((transitions / (len(s) - 1)) * 0.6 + (len(set(s)) / len(s)) * 0.4, 4)


def _brand_distance(
    registered_domain: str,
    subdomain_parts: list[str],
    all_tokens: list[str],
) -> tuple[int, float, int, str | None]:
    reg_lower = registered_domain.lower()
    brand_official = get_brand_official_domains()
    for brand, officials in brand_official.items():
        if reg_lower in [d.lower() for d in officials]:
            return (100, 0.0, 0, None)

    reg_stem = reg_lower.split(".")[0] if "." in reg_lower else reg_lower
    candidates = list(dict.fromkeys(
        [reg_stem] + [p.lower() for p in subdomain_parts]
        + [t.lower() for t in all_tokens if len(t) >= BRAND_MIN_TOKEN_LENGTH]
    ))

    best_dist, best_sim, best_brand = 100, 0.0, None
    brand_list = get_brand_list()
    for token in candidates:
        if len(token) < BRAND_MIN_TOKEN_LENGTH:
            continue
        for brand in brand_list:
            if token == brand:
                continue
            if abs(len(token) - len(brand)) > 3:
                continue
            sim = fuzz.ratio(token, brand)
            if sim > best_sim:
                best_sim, best_dist, best_brand = sim, 100 - sim, brand

    return (
        best_dist,
        round(best_sim, 2),
        int(best_sim >= BRAND_SIMILARITY_THRESHOLD and best_brand is not None),
        best_brand,
    )


def _parse_url(url: str) -> dict:
    parsed = urlparse(url)
    ext = _TLD_EXTRACT(url)
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    registered_domain = (
        ext.top_domain_under_public_suffix
        if hasattr(ext, "top_domain_under_public_suffix")
        else ext.registered_domain
    ) or ""
    subdomain = ext.subdomain or ""
    subdomain_parts = [p for p in subdomain.split(".") if p]
    url_body = url.split("://", 1)[-1] if "://" in url else url
    tokens = [t for t in _TOKEN_SPLIT_RE.split(url_body) if t]
    path_tokens = [t for t in path.split("/") if t]
    return dict(
        url=url, scheme=(parsed.scheme or "").lower(), hostname=hostname,
        path=path, query=parsed.query or "", registered_domain=registered_domain,
        subdomain=subdomain, subdomain_parts=subdomain_parts,
        subdomain_count=len(subdomain_parts), tld=ext.suffix or "",
        tokens=tokens, path_tokens=path_tokens, port=parsed.port,
    )


# ── Main extraction ──

def extract_features(url: str) -> dict:
    """Extract all V1+V2 features from a normalized URL."""
    p = _parse_url(url)
    url_str, hostname, path, query = p["url"], p["hostname"], p["path"], p["query"]
    scheme, reg_dom, tld = p["scheme"], p["registered_domain"], p["tld"]
    url_lower = url_str.lower()
    url_len = len(url_str)

    num_digits = sum(c.isdigit() for c in url_str)
    num_letters = sum(c.isalpha() for c in url_str)
    num_special = sum(1 for c in url_str if c in _SPECIAL_CHARS)

    has_ip = 0
    try:
        ipaddress.ip_address(hostname)
        has_ip = 1
    except ValueError:
        if _IP_RE.match(hostname):
            has_ip = 1

    keyword_flags = {}
    for key, variants in SUSPICIOUS_KEYWORDS.items():
        keyword_flags[f"has_{key}_keyword"] = int(any(v in url_lower for v in variants))

    contains_brand, brand_not_in_reg = 0, 0
    for brand in get_brand_list():
        if brand in url_lower:
            contains_brand = 1
            if brand not in reg_dom.lower():
                brand_not_in_reg = 1
            break

    # V1 features
    v1 = {
        "url_length": url_len, "domain_length": len(hostname),
        "path_length": len(path), "query_length": len(query),
        "num_dots": url_str.count("."), "num_hyphens": url_str.count("-"),
        "num_underscores": url_str.count("_"), "num_slashes": url_str.count("/"),
        "num_digits": num_digits, "num_letters": num_letters,
        "num_special_chars": num_special,
        "digit_ratio": round(num_digits / url_len, 4) if url_len else 0,
        "special_char_ratio": round(num_special / url_len, 4) if url_len else 0,
        "subdomain_count": p["subdomain_count"],
        "registered_domain_length": len(reg_dom),
        "tld_length": len(tld),
        "is_suspicious_tld": int(tld.lower() in SUSPICIOUS_TLDS),
        "has_https": int(scheme == "https"),
        "has_ip_address": has_ip,
        "has_at_symbol": int("@" in url_str),
        "has_port": int(p["port"] is not None and p["port"] not in (80, 443)),
        "has_encoded_chars": int(bool(_ENCODED_RE.search(url_str))),
        "has_double_slash_redirect": int(bool(_DOUBLE_SLASH_RE.search(url_str))),
        "has_url_shortener": int(reg_dom.lower() in URL_SHORTENERS or hostname.lower() in URL_SHORTENERS),
        **keyword_flags,
        "url_entropy": round(_entropy(url_str), 4),
        "domain_entropy": round(_entropy(hostname), 4),
        "path_entropy": round(_entropy(path), 4),
        "contains_brand_token": contains_brand,
        "brand_not_in_registered_domain": brand_not_in_reg,
    }

    # V2 features
    tokens = p["tokens"]
    token_lengths = [len(t) for t in tokens] if tokens else [0]
    domain_alpha = [c.lower() for c in hostname if c.isalpha()]
    vowels = sum(1 for c in domain_alpha if c in _VOWELS)
    consonants = sum(1 for c in domain_alpha if c in _CONSONANTS)
    brand_lev, brand_sim, has_typo, _ = _brand_distance(
        reg_dom, p["subdomain_parts"], tokens
    )
    is_http = 1 - v1["has_https"]

    v2 = {
        "token_count": len(tokens),
        "avg_token_length": round(np.mean(token_lengths), 4),
        "max_token_length": max(token_lengths),
        "num_gibberish_tokens": sum(1 for t in tokens if _is_gibberish_token(t)),
        "vowel_consonant_ratio": round(vowels / consonants, 4) if consonants > 0 else 0.0,
        "path_depth": len(p["path_tokens"]),
        "num_path_tokens": len(p["path_tokens"]),
        "brand_levenshtein_min_distance": brand_lev,
        "brand_similarity_max_score": brand_sim,
        "has_typosquatting_pattern": has_typo,
        "randomness_score": _randomness_score(hostname),
        "http_and_login_keyword": int(is_http and v1["has_login_keyword"]),
        "http_and_brand_token": int(is_http and v1["contains_brand_token"]),
        "http_and_many_subdomains": int(is_http and p["subdomain_count"] >= 3),
        "http_and_suspicious_keyword": int(is_http and any(
            v1.get(f"has_{k}_keyword", 0) for k in SUSPICIOUS_KEYWORDS)),
    }

    return {**v1, **v2}


def extract_features_final(url: str, feature_names: list[str] | None = None) -> dict:
    """Extract only the Final FS features (ordered by feature_names)."""
    if feature_names is None:
        feature_names = get_feature_schema()["feature_names"]
    all_features = extract_features(url)
    return {name: all_features[name] for name in feature_names}


def extract_features_batch(urls: list[str], feature_names: list[str] | None = None) -> pd.DataFrame:
    """Extract features for a batch of URLs → DataFrame (N × n_features)."""
    if feature_names is None:
        feature_names = get_feature_schema()["feature_names"]
    rows = [extract_features_final(url, feature_names) for url in urls]
    return pd.DataFrame(rows, columns=feature_names)

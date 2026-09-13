"""SHAP explanation — local per-URL + cached global importance."""
import time
from typing import Any

import numpy as np
import pandas as pd
import shap

from app.config import get_feature_schema, SUSPICIOUS_KEYWORDS

# ── Human-readable feature explanations ──
_FEATURE_EXPLANATIONS = {
    "has_login_keyword": ("URL contains login-related keywords", "URL does not contain login keywords"),
    "has_verify_keyword": ("URL contains verification-related keywords", None),
    "has_account_keyword": ("URL contains account-related keywords", None),
    "has_secure_keyword": ("URL contains security-related keywords used in social engineering", None),
    "has_bank_keyword": ("URL contains banking-related keywords", None),
    "has_update_keyword": ("URL contains update/renewal keywords", None),
    "has_payment_keyword": ("URL contains payment-related keywords", None),
    "has_free_keyword": ("URL contains free/reward/prize keywords", None),
    "has_https": (None, "URL does not use HTTPS"),
    "has_ip_address": ("URL uses an IP address instead of a domain name", None),
    "has_at_symbol": ("URL contains @ symbol which can be used to mislead", None),
    "has_port": ("URL specifies a non-standard port", None),
    "has_encoded_chars": ("URL contains percent-encoded characters", None),
    "has_double_slash_redirect": ("URL contains suspicious double-slash redirect pattern", None),
    "has_url_shortener": ("URL uses a known URL shortening service", None),
    "url_length": ("URL is unusually long", "URL length is normal"),
    "domain_length": ("Domain name is unusually long", "Domain length is normal"),
    "subdomain_count": ("URL has many subdomains, which can indicate domain spoofing", None),
    "contains_brand_token": ("URL contains a well-known brand name", None),
    "brand_not_in_registered_domain": (
        "A brand name appears in the URL but not in the registered domain", None
    ),
    "brand_levenshtein_min_distance": (
        "URL contains a token very similar to a known brand (possible typosquatting)", None
    ),
    "has_typosquatting_pattern": ("URL contains a typosquatting pattern", None),
    "is_suspicious_tld": ("URL uses a TLD commonly associated with abuse", None),
    "num_gibberish_tokens": ("URL contains gibberish or randomly-generated tokens", None),
    "url_entropy": ("URL has high character entropy, suggesting randomized content", None),
    "domain_entropy": ("Domain has high character entropy", None),
    "special_char_ratio": ("URL has high ratio of special characters", None),
    "path_depth": ("URL has unusually deep path structure", None),
    "http_and_login_keyword": ("URL combines HTTP (no encryption) with login keywords", None),
    "http_and_brand_token": ("URL combines HTTP with a brand name", None),
    "http_and_many_subdomains": ("URL combines HTTP with multiple subdomains", None),
}


def explain_single(
    feature_dict: dict,
    explainer: shap.TreeExplainer,
    feature_names: list[str] | None = None,
    top_k: int = 6,
) -> dict:
    """Generate local SHAP explanation for a single URL."""
    if feature_names is None:
        feature_names = get_feature_schema()["feature_names"]

    x = np.array([[feature_dict.get(f, 0) for f in feature_names]])

    start = time.perf_counter()
    shap_vals = explainer.shap_values(x)
    latency_ms = (time.perf_counter() - start) * 1000

    # Handle binary classification output
    if isinstance(shap_vals, list):
        sv = shap_vals[1][0]  # positive class, single sample
    else:
        sv = shap_vals[0]

    # Base value
    if isinstance(explainer.expected_value, (list, np.ndarray)):
        base_value = float(explainer.expected_value[1])
    else:
        base_value = float(explainer.expected_value)

    # Rank features by |SHAP|
    impacts = sorted(
        zip(feature_names, sv, [feature_dict.get(f, 0) for f in feature_names]),
        key=lambda x: abs(x[1]),
        reverse=True,
    )

    top_features = []
    for fname, shap_val, fval in impacts[:top_k]:
        top_features.append({
            "feature": fname,
            "value": fval,
            "shap_value": round(float(shap_val), 4),
            "direction": "increases_risk" if shap_val > 0 else "decreases_risk",
        })

    # Human-readable reasons
    reasons = _generate_reasons(top_features, feature_dict)

    # Waterfall data (all features, sorted by impact)
    waterfall_features = [f for f, _, _ in impacts]
    waterfall_values = [round(float(s), 4) for _, s, _ in impacts]
    cumulative = [base_value]
    for v in waterfall_values:
        cumulative.append(round(cumulative[-1] + v, 4))

    # All SHAP values
    all_shap = {f: round(float(s), 4) for f, s in zip(feature_names, sv)}

    return {
        "type": "shap",
        "model_output": "raw",
        "note": "SHAP values explain the underlying LightGBM decision before probability calibration",
        "base_value": round(base_value, 4),
        "top_features": top_features,
        "reasons": reasons,
        "waterfall_data": {
            "features": waterfall_features,
            "values": waterfall_values,
            "cumulative": cumulative,
        },
        "all_shap_values": all_shap,
        "latency_ms": round(latency_ms, 2),
    }


def get_global_importance(global_importance_df: pd.DataFrame) -> list[dict]:
    """Return cached global feature importance as list of dicts."""
    return global_importance_df.to_dict("records")


def _generate_reasons(top_features: list[dict], feature_dict: dict) -> list[str]:
    """Convert top SHAP features into human-readable explanations."""
    reasons = []
    for feat in top_features:
        fname = feat["feature"]
        fval = feat["value"]
        direction = feat["direction"]

        if direction != "increases_risk":
            continue

        if fname in _FEATURE_EXPLANATIONS:
            pos_reason, neg_reason = _FEATURE_EXPLANATIONS[fname]
            if fval == 1 and pos_reason:
                reasons.append(pos_reason)
            elif fval == 0 and neg_reason:
                reasons.append(neg_reason)
            elif pos_reason and fname in (
                "url_length", "domain_length", "subdomain_count",
                "url_entropy", "domain_entropy", "num_gibberish_tokens",
                "special_char_ratio", "path_depth",
                "brand_levenshtein_min_distance",
            ):
                reasons.append(pos_reason)
        else:
            reasons.append(f"Feature '{fname}' contributes to elevated risk (value={fval})")

    return reasons[:6]

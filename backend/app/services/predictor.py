"""Model inference — calibrated prediction + risk mapping."""
import time

import numpy as np
import pandas as pd

from app.config import RISK_LEVEL_BANDS, get_feature_schema


def predict_single(
    feature_dict: dict,
    calibrated_model,
    feature_names: list[str] | None = None,
    threshold: float = 0.5,
) -> dict:
    """Single URL prediction → risk_score, prediction, risk_level."""
    if feature_names is None:
        feature_names = get_feature_schema()["feature_names"]

    # Build feature vector in correct order
    x = np.array([[feature_dict[f] for f in feature_names]])

    start = time.perf_counter()
    risk_score = float(calibrated_model.predict_proba(x)[:, 1][0])
    inference_ms = (time.perf_counter() - start) * 1000

    prediction = "phishing" if risk_score >= threshold else "legitimate"
    risk_level = map_risk_level(risk_score)

    return {
        "risk_score": round(risk_score, 4),
        "prediction": prediction,
        "risk_level": risk_level,
        "threshold": threshold,
        "inference_time_ms": round(inference_ms, 3),
    }


def predict_batch(
    feature_df: pd.DataFrame,
    calibrated_model,
    threshold: float = 0.5,
) -> list[dict]:
    """Vectorized batch prediction → list of results."""
    start = time.perf_counter()
    risk_scores = calibrated_model.predict_proba(feature_df.values)[:, 1]
    total_ms = (time.perf_counter() - start) * 1000

    results = []
    for score in risk_scores:
        score = float(score)
        results.append({
            "risk_score": round(score, 4),
            "prediction": "phishing" if score >= threshold else "legitimate",
            "risk_level": map_risk_level(score),
        })

    return results, round(total_ms, 3)


def map_risk_level(score: float) -> str:
    """Map calibrated probability to risk level string."""
    for low, high, level in RISK_LEVEL_BANDS:
        if low <= score < high:
            return level
    return "critical"


def get_risk_color(level: str) -> dict:
    """Get color scheme for a risk level."""
    colors = {
        "low": {"bg": "#10B981", "bgLight": "#ECFDF5", "text": "#065F46", "label": "LOW"},
        "medium": {"bg": "#F59E0B", "bgLight": "#FFFBEB", "text": "#92400E", "label": "MEDIUM"},
        "high": {"bg": "#F97316", "bgLight": "#FFF7ED", "text": "#9A3412", "label": "HIGH"},
        "critical": {"bg": "#EF4444", "bgLight": "#FEF2F2", "text": "#991B1B", "label": "CRITICAL"},
    }
    return colors.get(level, colors["low"])


def get_risk_bands() -> list[dict]:
    """Return risk bands for frontend gauge rendering."""
    return [
        {"min": low, "max": high, "level": level, **get_risk_color(level)}
        for low, high, level in RISK_LEVEL_BANDS
    ]

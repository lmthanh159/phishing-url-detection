"""Privacy-aware prediction logger — logs url_hash, NOT raw URL."""
import hashlib
import json
import logging
import time
from pathlib import Path

from app.config import get_settings, get_model_metadata

logger = logging.getLogger("prediction_logger")


def _get_log_path() -> Path:
    log_dir = Path(get_settings().log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "predictions.jsonl"


def log_prediction(
    url: str,
    risk_score: float,
    prediction: str,
    inference_time_ms: float,
):
    """Log a prediction event (privacy-aware: URL hashed)."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url_hash": hashlib.sha256(url.encode()).hexdigest(),
        "risk_score": risk_score,
        "prediction": prediction,
        "inference_time_ms": inference_time_ms,
        "model_version": get_model_metadata().get("model_version", "unknown"),
    }

    try:
        with open(_get_log_path(), "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Failed to log prediction: {e}")


def log_batch_predictions(
    urls: list[str],
    results: list[dict],
    total_time_ms: float,
):
    """Log batch prediction events."""
    for url, result in zip(urls, results):
        log_prediction(
            url=url,
            risk_score=result.get("risk_score", 0),
            prediction=result.get("prediction", "unknown"),
            inference_time_ms=total_time_ms / len(urls) if urls else 0,
        )

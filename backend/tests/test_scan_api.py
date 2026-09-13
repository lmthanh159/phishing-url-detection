"""Integration tests for scan and model API endpoints."""
import io
import json
import sys
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limiter import _requests, clear_rate_limits


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_scan_logs_prediction_without_raw_url(client):
    clear_rate_limits()
    log_path = Path("logs/predictions.jsonl")
    before = log_path.stat().st_size if log_path.exists() else 0

    raw_url = "http://paypa1-login.xyz/verify"
    response = client.post("/api/scan", json={"url": raw_url})

    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == "phishing"
    assert 0 <= data["model_score"] <= 1
    assert "feature_contributions" in data["explanation"]

    assert log_path.exists()
    assert log_path.stat().st_size > before
    entry = json.loads(log_path.read_text().splitlines()[-1])
    assert len(entry["url_hash"]) == 64
    assert raw_url not in json.dumps(entry)


def test_batch_invalid_url_returns_422(client):
    clear_rate_limits()
    csv = b"url\nhttps://google.com\nftp://x.com\n"

    response = client.post(
        "/api/scan/batch",
        files={"file": ("urls.csv", io.BytesIO(csv), "text/csv")},
    )

    assert response.status_code == 422
    assert "Invalid URL at row 3" in response.json()["detail"]


def test_batch_scan_returns_model_score(client):
    clear_rate_limits()
    csv = b"url\nhttps://google.com\nhttp://paypa1-login.xyz/verify\n"

    response = client.post(
        "/api/scan/batch",
        files={"file": ("urls.csv", io.BytesIO(csv), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert all(0 <= item["model_score"] <= 1 for item in data["results"])


def test_single_scan_rate_limit_returns_retry_after(client):
    clear_rate_limits()
    _requests[("single_scan", "testclient")] = deque([time.monotonic()] * 60)

    response = client.post("/api/scan", json={"url": "https://google.com"})

    assert response.status_code == 429
    assert response.headers["Retry-After"]


def test_model_unavailable_returns_503(client):
    clear_rate_limits()
    saved = client.app.state.calibrated_model
    client.app.state.calibrated_model = None
    try:
        response = client.post("/api/scan", json={"url": "https://google.com"})
    finally:
        client.app.state.calibrated_model = saved

    assert response.status_code == 503
    assert response.json() == {"detail": "Model not available"}


def test_model_info_contract(client):
    response = client.get("/api/model-info")

    assert response.status_code == 200
    data = response.json()
    assert data["n_features"] == 37
    assert len(data["global_feature_importance"]) == 37
    assert "importance" in data["global_feature_importance"][0]

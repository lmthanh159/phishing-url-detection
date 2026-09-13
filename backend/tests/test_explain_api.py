"""Integration tests for explain endpoint and schemas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.middleware.rate_limiter import clear_rate_limits
from app.schemas.explain import FeatureContribution


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_explain_returns_full_shap_details(client):
    clear_rate_limits()

    response = client.post("/api/explain", json={"url": "http://paypa1-login.xyz/verify"})

    assert response.status_code == 200
    explanation = response.json()["explanation"]
    assert explanation["type"] == "shap"
    assert explanation["model_output"] == "raw"
    assert len(explanation["feature_contributions"]) == 37
    assert len(explanation["waterfall_data"]["features"]) == 37
    assert len(explanation["waterfall_data"]["cumulative"]) == 38
    assert explanation["latency_ms"] >= 0


def test_feature_contribution_direction_is_constrained():
    with pytest.raises(ValidationError):
        FeatureContribution(
            feature="url_length",
            value=1,
            shap_value=0.1,
            direction="bad_direction",
        )

"""Request/response schemas for explain endpoint."""
from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=8192, examples=["https://example.com/login"])


class FeatureContribution(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str      # "increases_risk" | "decreases_risk"


class WaterfallData(BaseModel):
    features: list[str]
    values: list[float]
    cumulative: list[float]


class ExplanationResponse(BaseModel):
    type: str = "shap"
    model_output: str = "raw"
    note: str = "SHAP values explain the underlying LightGBM decision before probability calibration"
    base_value: float
    top_features: list[FeatureContribution]
    reasons: list[str]
    waterfall_data: WaterfallData


class ExplainFullResponse(BaseModel):
    url: str
    normalized_url: str
    risk_score: float
    prediction: str
    risk_level: str
    explanation: ExplanationResponse

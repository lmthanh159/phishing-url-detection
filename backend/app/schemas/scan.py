"""Request/response schemas for scan endpoints."""
from pydantic import BaseModel, Field
from app.schemas.explain import ExplanationResponse


class ScanRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=8192, examples=["https://example.com/login"])


class ScanResponse(BaseModel):
    url: str
    normalized_url: str
    prediction: str                         # "phishing" | "legitimate"
    risk_score: float = Field(ge=0, le=1)
    model_score: float | None = Field(default=None, ge=0, le=1)
    risk_level: str                         # "low" | "medium" | "high" | "critical"
    threshold: float
    explanation: ExplanationResponse
    inference_time_ms: float
    model_version: str


class BatchResultItem(BaseModel):
    url: str
    prediction: str
    risk_score: float = Field(ge=0, le=1)
    model_score: float | None = Field(default=None, ge=0, le=1)
    risk_level: str


class BatchSummary(BaseModel):
    risk_distribution: dict[str, int]
    avg_inference_time_ms: float
    total_time_ms: float


class BatchScanResponse(BaseModel):
    total: int
    phishing: int
    legitimate: int
    results: list[BatchResultItem]
    summary: BatchSummary

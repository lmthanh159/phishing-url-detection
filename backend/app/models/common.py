"""Common backend models shared by services and routers."""
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PredictionResult:
    risk_score: float
    prediction: str
    risk_level: RiskLevel | str
    threshold: float
    inference_time_ms: float

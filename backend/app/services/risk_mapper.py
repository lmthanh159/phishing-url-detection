"""Risk score mapping helpers."""
from app.config import RISK_LEVEL_BANDS
from app.models.common import RiskLevel


def map_risk_level(score: float) -> RiskLevel:
    """Map calibrated probability to a risk level."""
    for low, high, level in RISK_LEVEL_BANDS:
        if low <= score < high:
            return RiskLevel(level)
    return RiskLevel.CRITICAL


def get_risk_color(level: RiskLevel | str) -> dict:
    """Get color metadata for a risk level."""
    level_value = level.value if isinstance(level, RiskLevel) else level
    colors = {
        "low": {"bg": "#10B981", "bgLight": "#ECFDF5", "text": "#065F46", "label": "LOW"},
        "medium": {"bg": "#F59E0B", "bgLight": "#FFFBEB", "text": "#92400E", "label": "MEDIUM"},
        "high": {"bg": "#F97316", "bgLight": "#FFF7ED", "text": "#9A3412", "label": "HIGH"},
        "critical": {"bg": "#EF4444", "bgLight": "#FEF2F2", "text": "#991B1B", "label": "CRITICAL"},
    }
    return colors.get(level_value, colors["low"])


def get_risk_bands() -> list[dict]:
    """Return risk bands for frontend gauge rendering."""
    return [
        {"min": low, "max": high, "level": level, **get_risk_color(level)}
        for low, high, level in RISK_LEVEL_BANDS
    ]

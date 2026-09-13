"""Model info and health check endpoints."""
import time

from fastapi import APIRouter, Request, HTTPException

from app.config import get_model_metadata, get_threshold_config, get_feature_schema
from app.services.risk_mapper import get_risk_bands
from app.services.explainer import get_global_importance

router = APIRouter(prefix="/api", tags=["model"])


@router.get("/model-info")
async def model_info(request: Request):
    """Return model metadata, metrics, and global feature importance."""
    model_loaded = (
        getattr(request.app.state, "calibrated_model", None) is not None
        and getattr(request.app.state, "model", None) is not None
    )
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not available")

    metadata = getattr(request.app.state, "metadata", None) or get_model_metadata()
    threshold_config = getattr(request.app.state, "threshold_config", None) or get_threshold_config()
    feature_schema = getattr(request.app.state, "feature_schema", None) or get_feature_schema()

    global_importance = get_global_importance(request.app.state.global_importance)

    return {
        "model_name": metadata.get("model_name"),
        "model_version": metadata.get("model_version"),
        "feature_set": feature_schema.get("feature_set"),
        "n_features": feature_schema.get("n_features"),
        "calibration_method": metadata.get("calibration_method"),
        "threshold": threshold_config.get("threshold"),
        "data_sources": metadata.get("data_sources", []),
        "final_test_metrics": metadata.get("final_test_metrics", {}),
        "risk_bands": get_risk_bands(),
        "global_feature_importance": global_importance,
    }


@router.get("/health")
async def health_check(request: Request):
    """Health check — model loaded, uptime."""
    model_loaded = (
        hasattr(request.app.state, "calibrated_model")
        and request.app.state.calibrated_model is not None
    )
    metadata = (getattr(request.app.state, "metadata", None) or get_model_metadata()) if model_loaded else {}

    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "model_version": metadata.get("model_version", "unknown"),
        "uptime_seconds": round(time.time() - request.app.state.start_time, 1)
            if hasattr(request.app.state, "start_time") else 0,
    }

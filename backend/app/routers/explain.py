"""Explain endpoint — detailed SHAP explanation for a single URL."""
from fastapi import APIRouter, Request, HTTPException

from app.config import get_feature_schema, get_threshold_config
from app.schemas.explain import ExplainRequest, ExplainFullResponse
from app.services.url_normalizer import validate_url
from app.services.feature_extractor import extract_features_final
from app.services.predictor import predict_single
from app.services.explainer import explain_single

router = APIRouter(prefix="/api", tags=["explain"])


def _require_explain_ready(request: Request) -> None:
    if getattr(request.app.state, "calibrated_model", None) is None:
        raise HTTPException(status_code=503, detail="Model not available")
    if getattr(request.app.state, "explainer", None) is None:
        raise HTTPException(status_code=503, detail="Model not available")


def _feature_names(request: Request) -> list[str]:
    schema = getattr(request.app.state, "feature_schema", None) or get_feature_schema()
    return schema["feature_names"]


def _threshold(request: Request) -> float:
    threshold_config = getattr(request.app.state, "threshold_config", None) or get_threshold_config()
    return threshold_config["threshold"]


@router.post("/explain", response_model=ExplainFullResponse)
async def explain_url(body: ExplainRequest, request: Request):
    """Get detailed SHAP explanation for a URL."""
    _require_explain_ready(request)

    # Validate & normalize
    result = validate_url(body.url)
    if not result.is_valid:
        raise HTTPException(status_code=422, detail=f"Invalid URL: {result.error}")

    normalized = result.normalized_url

    # Extract features
    feature_names = _feature_names(request)
    features = extract_features_final(normalized, feature_names)

    # Predict
    threshold = _threshold(request)
    pred = predict_single(
        features,
        request.app.state.calibrated_model,
        request.app.state.model,
        feature_names,
        threshold,
    )

    # Explain
    explanation = explain_single(features, request.app.state.explainer, feature_names)

    return ExplainFullResponse(
        url=body.url,
        normalized_url=normalized,
        risk_score=pred["risk_score"],
        model_score=pred["model_score"],
        prediction=pred["prediction"],
        risk_level=pred["risk_level"],
        explanation=explanation,
    )

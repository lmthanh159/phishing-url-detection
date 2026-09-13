"""Scan endpoints — single URL and batch CSV."""
import io
import time

import pandas as pd
from fastapi import APIRouter, Request, UploadFile, File, HTTPException

from app.config import get_settings, get_feature_schema, get_threshold_config, get_model_metadata
from app.schemas.scan import ScanRequest, ScanResponse, BatchScanResponse, BatchResultItem, BatchSummary
from app.services.url_normalizer import validate_url
from app.services.feature_extractor import extract_features_final, extract_features_batch
from app.services.predictor import predict_single, predict_batch, map_risk_level
from app.services.explainer import explain_single

router = APIRouter(prefix="/api", tags=["scan"])


@router.post("/scan", response_model=ScanResponse)
async def scan_url(body: ScanRequest, request: Request):
    """Scan a single URL — returns prediction + SHAP explanation."""
    total_start = time.perf_counter()

    # Validate & normalize
    result = validate_url(body.url)
    if not result.is_valid:
        raise HTTPException(status_code=422, detail=f"Invalid URL: {result.error}")

    normalized = result.normalized_url

    # Extract features
    feature_names = get_feature_schema()["feature_names"]
    features = extract_features_final(normalized, feature_names)

    # Predict
    threshold = get_threshold_config()["threshold"]
    pred = predict_single(features, request.app.state.calibrated_model, feature_names, threshold)

    # Explain (SHAP on base model)
    explanation = explain_single(features, request.app.state.explainer, feature_names)

    total_ms = (time.perf_counter() - total_start) * 1000

    return ScanResponse(
        url=body.url,
        normalized_url=normalized,
        prediction=pred["prediction"],
        risk_score=pred["risk_score"],
        risk_level=pred["risk_level"],
        threshold=pred["threshold"],
        explanation=explanation,
        inference_time_ms=round(total_ms, 3),
        model_version=get_model_metadata().get("model_version", "unknown"),
    )


@router.post("/scan/batch", response_model=BatchScanResponse)
async def scan_batch(request: Request, file: UploadFile = File(...)):
    """Batch scan from CSV upload — vectorized inference, no SHAP."""
    settings = get_settings()
    total_start = time.perf_counter()

    # Validate file
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only CSV files accepted")

    contents = await file.read()
    if len(contents) > settings.max_batch_file_mb * 1024 * 1024:
        raise HTTPException(status_code=422, detail=f"File exceeds {settings.max_batch_file_mb}MB limit")

    # Parse CSV
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=422, detail="Cannot parse CSV file")

    # Validate columns
    col_map = {c.lower(): c for c in df.columns}
    url_col = col_map.get("url")
    if url_col is None:
        raise HTTPException(status_code=422, detail="CSV must have 'url' column")

    urls = df[url_col].dropna().astype(str).tolist()
    if len(urls) > settings.max_batch_size:
        raise HTTPException(status_code=422, detail=f"Max {settings.max_batch_size} URLs per batch")
    if len(urls) == 0:
        raise HTTPException(status_code=422, detail="CSV contains no URLs")

    # Validate & normalize URLs
    valid_urls = []
    valid_originals = []
    for url in urls:
        r = validate_url(url)
        if r.is_valid:
            valid_urls.append(r.normalized_url)
            valid_originals.append(url)

    if len(valid_urls) == 0:
        raise HTTPException(status_code=422, detail="No valid URLs found in CSV")

    # Batch feature extraction
    feature_names = get_feature_schema()["feature_names"]
    feature_df = extract_features_batch(valid_urls, feature_names)

    # Vectorized prediction
    threshold = get_threshold_config()["threshold"]
    predictions, pred_ms = predict_batch(feature_df, request.app.state.calibrated_model, threshold)

    # Build results
    results = []
    risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    n_phishing = 0

    for orig_url, pred in zip(valid_originals, predictions):
        results.append(BatchResultItem(
            url=orig_url,
            prediction=pred["prediction"],
            risk_score=pred["risk_score"],
            risk_level=pred["risk_level"],
        ))
        risk_dist[pred["risk_level"]] += 1
        if pred["prediction"] == "phishing":
            n_phishing += 1

    total_ms = (time.perf_counter() - total_start) * 1000

    return BatchScanResponse(
        total=len(results),
        phishing=n_phishing,
        legitimate=len(results) - n_phishing,
        results=results,
        summary=BatchSummary(
            risk_distribution=risk_dist,
            avg_inference_time_ms=round(pred_ms / len(results), 3) if results else 0,
            total_time_ms=round(total_ms, 3),
        ),
    )

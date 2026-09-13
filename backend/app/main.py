"""FastAPI application — Phishing URL Detection API."""
import json
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
import shap
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all artifacts at startup."""
    settings = get_settings()
    model_dir = Path(settings.model_dir)

    logger.info(f"Loading artifacts from {model_dir}")
    start = time.time()

    try:
        app.state.model = joblib.load(model_dir / "model.joblib")
        app.state.calibrated_model = joblib.load(model_dir / "calibrated_model.joblib")

        with open(model_dir / "model_metadata.json") as f:
            metadata = json.load(f)

        # SHAP TreeExplainer on base model (NOT calibrated)
        app.state.explainer = shap.TreeExplainer(app.state.model)

        app.state.global_importance = pd.read_csv(model_dir / "global_feature_importance.csv")

        app.state.start_time = time.time()

        elapsed = time.time() - start
        logger.info(
            f"✓ Model loaded: {metadata.get('model_name')} "
            f"v{metadata.get('model_version')} "
            f"({metadata.get('n_features')} features) "
            f"in {elapsed:.1f}s"
        )
    except Exception as e:
        logger.error(f"✗ Failed to load artifacts: {e}")
        app.state.model = None
        app.state.calibrated_model = None
        app.state.explainer = None
        app.state.global_importance = pd.DataFrame()
        app.state.start_time = time.time()

    yield

    logger.info("Shutting down")


# ── App ──
app = FastAPI(
    title="Phishing URL Detection API",
    description="Explainable ML-based phishing URL detection with SHAP explanations",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (fallback for dev without proxy) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
from app.routers import scan, explain, model_info  # noqa: E402

app.include_router(scan.router)
app.include_router(explain.router)
app.include_router(model_info.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Phishing URL Detection API", "docs": "/docs"}

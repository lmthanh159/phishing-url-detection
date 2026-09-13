# Phishing URL Detection

Explainable phishing URL detection app built with FastAPI, Vue 3, LightGBM, and SHAP.

The project provides a REST API for single URL and batch CSV scanning, plus a frontend dashboard for interactive analysis, model information, risk distribution, and feature-level explanations.

## Features

- Single URL phishing detection with risk score and risk level.
- Batch CSV scanning for up to 1,000 URLs per file.
- SHAP-based explanation for individual predictions.
- Model metadata, threshold, risk bands, and global feature importance endpoint.
- Vue 3 frontend with scan history, batch results, dashboard charts, and explanation views.
- Docker Compose setup for running frontend and backend together.

## Tech Stack

- Backend: FastAPI, Uvicorn, Pydantic, LightGBM, SHAP, scikit-learn, pandas, NumPy.
- Frontend: Vue 3, Vite, Vue Router, Pinia, ECharts, Tailwind CSS.
- Model: LightGBM binary classifier with sigmoid calibration.
- Runtime target: Python 3.12.10, Node.js 20+.

## Project Structure

```text
.
+-- artifacts/                  # Trained model and metadata artifacts
+-- backend/                    # FastAPI backend
|   +-- app/
|   |   +-- routers/            # API endpoints
|   |   +-- schemas/            # Request/response models
|   |   +-- services/           # Normalization, feature extraction, prediction, explanation
|   |   +-- middleware/         # Logging and rate limiting
|   +-- tests/                  # Backend tests
|   +-- Dockerfile
|   +-- requirements.txt
+-- frontend/                   # Vue/Vite frontend
|   +-- src/
|   |   +-- api/
|   |   +-- components/
|   |   +-- stores/
|   |   +-- views/
|   +-- Dockerfile
|   +-- nginx.conf
|   +-- package.json
+-- architecture.md             # Architecture and work package notes
+-- docker-compose.yml
```

## Required Artifacts

The backend expects these files in `artifacts/`:

```text
model.joblib
calibrated_model.joblib
feature_schema.json
threshold_config.json
model_metadata.json
global_feature_importance.csv
brand_list.json
shared_infra_domains.json
```

By default, the backend loads artifacts from the root `artifacts/` directory. You can override this with `MODEL_DIR`.

## Quick Start With Docker

From the repository root:

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost`

The Compose setup serves the frontend on port `80`. The frontend Nginx container proxies `/api/*` requests to the backend container.
The backend container is not published to the host by default; run the backend locally or add a `ports` mapping if you want to open Swagger docs from the host.

## Backend Local Setup

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected startup log:

```text
Model loaded: LightGBM vlightgbm_20260810_081812 (37 features)
```

Backend URLs:

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`
- Model info: `http://localhost:8000/api/model-info`

## Frontend Local Setup

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

During development, Vite proxies `/api` to `http://localhost:8000`.

## API Examples

Single URL scan:

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.google.com"}'
```

Example response shape:

```json
{
  "url": "https://www.google.com",
  "normalized_url": "https://www.google.com/",
  "prediction": "legitimate",
  "risk_score": 0.0,
  "risk_level": "low",
  "threshold": 0.5146681331630758,
  "explanation": {
    "type": "shap",
    "top_features": [],
    "waterfall_data": {}
  },
  "inference_time_ms": 8.887,
  "model_version": "lightgbm_20260810_081812"
}
```

Detailed explanation:

```bash
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.google.com"}'
```

Batch scan CSV:

```bash
curl -X POST http://localhost:8000/api/scan/batch \
  -F "file=@urls.csv"
```

The CSV must contain a `url` column:

```csv
url
https://www.google.com
http://paypa1-secure.login-verify.xyz/account/update
```

## Testing

Run backend tests:

```bash
cd backend
python -m pytest
```

Run frontend production build:

```bash
cd frontend
npm run build
```

## Configuration

Backend settings are defined in `backend/app/config.py`.

Important values:

- `MODEL_DIR`: artifact directory. Defaults to `artifacts/` at the repository root.
- `max_url_length`: maximum accepted URL length.
- `max_batch_size`: maximum number of URLs in one batch CSV.
- `max_batch_file_mb`: maximum CSV upload size.

URL normalization defaults missing schemes to `https://`.

## Model Metadata

Current artifact metadata:

- Model: `LightGBM`
- Version: `lightgbm_20260810_081812`
- Features: `37`
- Calibration: `sigmoid`
- Threshold strategy: `max_f1`
- Threshold: `0.5146681331630758`
- Data sources: `phiusiil`, `phishtank`, `tranco`

Final test metrics recorded in `artifacts/model_metadata.json`:

| Metric | Value |
| --- | ---: |
| Precision | 0.9908 |
| Recall | 0.9791 |
| F1 | 0.9849 |
| ROC AUC | 0.9971 |
| PR AUC | 0.9973 |
| Brier | 0.0108 |

## Notes And Limitations

- This is an ML-assisted detection tool, not a definitive security verdict.
- SHAP explanations are generated from the base LightGBM model, while prediction scores come from the calibrated model.
- Model behavior depends heavily on the training data and feature distribution. Benign URLs with login-like paths or sensitive keywords may still require additional review.
- Keep `scikit-learn==1.6.1` aligned with the serialized artifacts unless the model artifacts are regenerated.

## Development Hygiene

Ignored local files include:

- Python virtual environments
- Node modules
- Build outputs
- Logs
- Python and test caches

Before pushing:

```bash
cd backend
python -m pytest

cd ../frontend
npm run build
```

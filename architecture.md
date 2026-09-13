# Phishing URL Detection — Phase 2 Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                         │
│                   Vue 3 + Vite + TailwindCSS                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/JSON (/api/*)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ URL      │  │ Feature  │  │ Calibrated│  │ SHAP         │  │
│  │ Normaliz.│→ │ Extractor│→ │ Model     │→ │ Explainer    │  │
│  └──────────┘  └──────────┘  └───────────┘  └──────────────┘  │
│                                    │                            │
│                         artifacts/ (read-only mount)            │
└─────────────────────────────────────────────────────────────────┘
```

**Key principle:** Frontend và backend chạy ổn định ở cả development (demo) lẫn
production (Docker), cùng source code, không cần config flag để switch.

---

## 2. Tech Stack

### Backend

| Component         | Technology                  | Version   | Lý do                                                 |
| ----------------- | --------------------------- | --------- | ----------------------------------------------------- |
| Framework         | FastAPI                     | ≥0.115    | Async, auto OpenAPI docs, Pydantic v2 native          |
| Python            | Python                      | 3.11+     | Khớp với Colab environment                            |
| Validation        | Pydantic                    | ≥2.0      | Required by FastAPI latest                            |
| ML Inference      | scikit-learn                | ≥1.5      | CalibratedClassifierCV, pipeline utilities             |
| ML Inference      | LightGBM                   | ≥4.5      | TreeSHAP native support                              |
| XAI               | SHAP                        | ≥0.46     | TreeExplainer, compatible với LightGBM 4.x            |
| URL parsing       | tldextract                  | ≥5.0      | Registered domain extraction                          |
| URL parsing       | idna                        | ≥3.0      | Punycode/IDN handling                                 |
| Brand matching    | rapidfuzz                   | ≥3.0      | Levenshtein distance                                  |
| Server            | Uvicorn                     | ≥0.30     | ASGI server                                           |
| Containerization  | Docker + docker-compose     | —         | Reproducible deployment                               |

### Frontend

| Component      | Technology                       | Version   | Lý do                                                |
| -------------- | -------------------------------- | --------- | ---------------------------------------------------- |
| Framework      | Vue 3 (Composition API)          | ≥3.4      | Reactive, Suspense stable                            |
| Build tool     | Vite                             | ≥6.0      | HMR nhanh, TailwindCSS v4 plugin support             |
| Styling        | TailwindCSS + @tailwindcss/vite  | ≥4.1      | CSS-first config, không cần PostCSS                  |
| Charts         | ECharts + vue-echarts            | echarts ≥6.0, vue-echarts ≥8.0 | SHAP visualization, Vue 3.3+ required |
| HTTP client    | Axios                            | ≥1.7      | Interceptors, error handling                         |
| Router         | Vue Router                       | ≥4.4      | SPA navigation                                       |
| State          | Pinia + persistedstate plugin    | pinia ≥2.2, plugin ≥4.0 | Lightweight store, persist qua localStorage |
| Icons          | lucide-vue-next                  | ≥0.400    | Icons cho Vue 3                                      |
| Notifications  | vue3-toastify                    | ≥0.2      | Non-blocking alerts, actively maintained             |

---

## 3. Backend Architecture

### 3.1 Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, CORS fallback
│   ├── config.py                # Settings (paths, thresholds, brand list)
│   ├── routers/
│   │   ├── scan.py              # POST /api/scan, /api/scan/batch
│   │   ├── explain.py           # POST /api/explain
│   │   └── model_info.py        # GET  /api/model-info, /api/health
│   ├── services/
│   │   ├── url_normalizer.py    # Validate + normalize (from Phase 1)
│   │   ├── feature_extractor.py # Extract features (from Phase 1)
│   │   ├── predictor.py         # Load model, predict, calibrate, threshold
│   │   ├── explainer.py         # SHAP local + global (cached)
│   │   └── risk_mapper.py       # Score → risk level + human-readable reasons
│   ├── schemas/
│   │   ├── scan.py              # ScanRequest, ScanResponse, BatchScanRequest
│   │   └── explain.py           # ExplainRequest, ExplainResponse
│   ├── models/                  # Pydantic models (not ML models)
│   │   └── common.py            # RiskLevel enum, FeatureVector, etc.
│   └── middleware/
│       ├── rate_limiter.py      # Rate limiting
│       └── request_logger.py    # Privacy-aware prediction logging
├── tests/
│   ├── test_normalizer.py
│   ├── test_features.py
│   ├── test_scan_api.py
│   └── test_explain_api.py
├── Dockerfile
└── requirements.txt
```

> **Note:** Backend không chứa `artifacts/`. Artifacts nằm ở project root,
> referenced qua `MODEL_DIR` environment variable hoặc relative path.

### 3.2 API Endpoints

#### `POST /api/scan` — Single URL Scan

```json
// Request
{
  "url": "https://paypa1-login.example.com/verify"
}

// Response
{
  "url": "https://paypa1-login.example.com/verify",
  "normalized_url": "https://paypa1-login.example.com/verify",
  "prediction": "phishing",
  "risk_score": 0.9423,
  "risk_level": "critical",
  "threshold": 0.515,
  "explanation": {
    "type": "shap",
    "model_output": "raw",
    "note": "SHAP values explain the underlying LightGBM decision before probability calibration",
    "top_features": [
      {"feature": "brand_levenshtein_min_distance", "value": 12, "shap_value": 2.34, "direction": "increases_risk"},
      {"feature": "has_login_keyword", "value": 1, "shap_value": 1.87, "direction": "increases_risk"},
      {"feature": "domain_length", "value": 32, "shap_value": 1.12, "direction": "increases_risk"}
    ],
    "reasons": [
      "URL contains a token very similar to a known brand (possible typosquatting)",
      "URL contains login-related keywords",
      "Unusual domain length"
    ]
  },
  "inference_time_ms": 12.3,
  "model_version": "lightgbm_20260815_143022"
}
```

#### `POST /api/scan/batch` — Batch Scan (CSV upload)

```json
// Request: multipart/form-data with CSV file
// CSV format: one column "url", max 1000 rows

// Response
{
  "total": 150,
  "phishing": 23,
  "legitimate": 127,
  "results": [
    {
      "url": "...",
      "prediction": "phishing",
      "risk_score": 0.94,
      "risk_level": "critical"
    },
    {
      "url": "...",
      "prediction": "legitimate",
      "risk_score": 0.12,
      "risk_level": "low"
    }
  ],
  "summary": {
    "risk_distribution": {"critical": 10, "high": 8, "medium": 5, "low": 127},
    "avg_inference_time_ms": 8.5,
    "total_time_ms": 1275
  }
}
```

> **Batch không bao gồm SHAP explanation.** Batch tập trung vào vectorized inference
> (predict_proba trên matrix N×37). SHAP chỉ được tính khi user click "Detail"
> trên từng URL, gọi `POST /api/explain`.
> Nếu benchmark cho thấy top 3 reasons cho 1000 URLs < 3s, có thể thêm
> optional query param `?include_reasons=true` sau này.

#### `POST /api/explain` — Detailed SHAP Explanation

```json
// Request
{
  "url": "https://paypa1-login.example.com/verify"
}

// Response
{
  "url": "...",
  "risk_score": 0.9423,
  "explanation": {
    "type": "shap",
    "model_output": "raw",
    "note": "SHAP values explain the underlying LightGBM decision before probability calibration",
    "base_value": 0.45,
    "feature_contributions": {
      "domain_length": {"value": 32, "shap_value": 1.12},
      "path_length": {"value": 7, "shap_value": 0.34}
    },
    "top_features": [...],
    "reasons": [...],
    "waterfall_data": {
      "features": ["domain_length", "path_length", ...],
      "values": [1.12, 0.34, ...],
      "cumulative": [0.45, 1.57, 1.91, ...]
    }
  }
}
```

#### `GET /api/model-info` — Model Metadata

```json
{
  "model_name": "LightGBM",
  "model_version": "lightgbm_20260815_143022",
  "feature_set": "Final",
  "n_features": 37,
  "calibration_method": "isotonic",
  "threshold": 0.515,
  "data_sources": ["phiusiil", "phishtank", "tranco"],
  "final_test_metrics": {"f1": 0.9849, "precision": 0.9908, "recall": 0.9791},
  "global_feature_importance": [
    {"feature": "domain_length", "importance": 2.28},
    {"feature": "path_length", "importance": 2.21}
  ]
}
```

#### `GET /api/health` — Health Check

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "lightgbm_20260815_143022",
  "uptime_seconds": 3600
}
```

### 3.3 Model Loading Strategy

```python
# Singleton — load once at startup via FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    model_dir = Path(os.getenv("MODEL_DIR", "../artifacts"))
    app.state.model = joblib.load(model_dir / "model.joblib")
    app.state.calibrated_model = joblib.load(model_dir / "calibrated_model.joblib")
    app.state.feature_schema = json.load(open(model_dir / "feature_schema.json"))
    app.state.threshold_config = json.load(open(model_dir / "threshold_config.json"))
    app.state.metadata = json.load(open(model_dir / "model_metadata.json"))
    # SHAP TreeExplainer trên base model (không phải calibrated)
    app.state.explainer = shap.TreeExplainer(app.state.model)
    app.state.global_importance = pd.read_csv(model_dir / "global_feature_importance.csv")
    yield
```

### 3.4 SHAP Explanation Scope

```
SHAP TreeExplainer → chạy trên base LightGBM model (model.joblib)
Calibrated model   → chạy predict_proba cho risk_score (calibrated_model.joblib)

LightGBM raw output
       │
       ├── SHAP explanation (explains this layer)
       │
       ▼
Isotonic calibration
       │
       ▼
risk_score (calibrated probability)
```

SHAP giải thích quyết định của base model, không phải calibrated probability.
UI phải phản ánh điều này (xem Section 4.3).

### 3.5 Batch Processing — Vectorized Inference

```
CSV upload
    ↓
Parse + validate URLs (backend, authoritative)
    ↓
Batch feature extraction (loop per URL — URL parsing inherently sequential)
    ↓
Feature matrix (N × 37)
    ↓
calibrated_model.predict_proba(X)  ← vectorized, single call
    ↓
Risk mapping (vectorized)
    ↓
Response
```

`predict_proba` nhận full matrix, không loop từng row. Feature extraction
vẫn sequential vì mỗi URL cần parse riêng, nhưng đây là I/O-bound không phải
compute-bound.

### 3.6 Privacy-Aware Logging

```
Application-level prediction logger ghi:
  - timestamp
  - url_hash (SHA-256, not raw URL)
  - risk_score
  - prediction
  - inference_time_ms
  - model_version

Application-level prediction logger KHÔNG ghi:
  - raw URL
  - feature vector
  - user IP

Client-side:
  - Scan history lưu trong localStorage (browser) bao gồm raw URLs
  - Không bao giờ gửi về server ngoài inference request
  - User có thể xóa bất cứ lúc nào qua "Clear history"

Infrastructure note:
  - Nginx access log có thể chứa IP và timestamp ở infrastructure level
  - Scanned URL nằm trong request body (POST), không xuất hiện trong URI
```

---

## 4. Frontend Architecture

### 4.1 Project Structure

```
frontend/
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router/
│   │   └── index.js              # Route definitions
│   ├── stores/
│   │   └── scanHistory.js        # Pinia store (persisted to localStorage)
│   ├── api/
│   │   └── client.js             # Axios instance + interceptors
│   ├── views/
│   │   ├── ScanView.vue          # Main scan page
│   │   ├── BatchView.vue         # Batch scan page
│   │   ├── DashboardView.vue     # Model info + global SHAP
│   │   └── AboutView.vue         # Project info + disclaimers
│   ├── components/
│   │   ├── scan/
│   │   │   ├── UrlInput.vue           # URL input (minimal validation: non-empty + length)
│   │   │   ├── RiskGauge.vue          # Circular gauge with threshold line
│   │   │   ├── RiskBadge.vue          # Color-coded badge: low/medium/high/critical
│   │   │   ├── PredictionBadge.vue    # Binary badge: PHISHING / LEGITIMATE
│   │   │   ├── ReasonsList.vue        # Human-readable explanation list
│   │   │   └── FeatureWaterfall.vue   # SHAP waterfall chart (ECharts)
│   │   ├── batch/
│   │   │   ├── CsvUploader.vue        # Drag-and-drop CSV upload (UX validation only)
│   │   │   ├── BatchResultsTable.vue  # Sortable results table + Detail button
│   │   │   └── RiskDistribution.vue   # Pie/bar chart: risk level distribution
│   │   ├── dashboard/
│   │   │   ├── ModelCard.vue          # Model metadata display
│   │   │   ├── MetricsCard.vue        # F1, Precision, Recall display
│   │   │   ├── FeatureImportance.vue  # Global SHAP bar chart
│   │   │   └── DataSourcesCard.vue    # Training data composition
│   │   └── layout/
│   │       ├── AppHeader.vue
│   │       ├── AppSidebar.vue
│   │       └── AppFooter.vue
│   └── utils/
│       ├── riskColors.js              # Risk level → color mapping
│       └── formatters.js              # Number, time formatters
├── index.html
├── vite.config.js
└── package.json
```

### 4.2 Routes

| Route        | View                | Mô tả                                   |
| ------------ | ------------------- | ---------------------------------------- |
| `/`          | ScanView            | Trang chính: scan single URL             |
| `/batch`     | BatchView           | Upload CSV, batch scan                   |
| `/dashboard` | DashboardView       | Model info, global SHAP, metrics         |
| `/about`     | AboutView           | Project info, methodology, disclaimers   |

### 4.3 UI Design Specifications

#### 4.3.1 ScanView — Trang chính

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo] Phishing URL Detector    [Scan] [Batch] [Dashboard]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────┐               │
│   │ 🔍  Enter URL to scan...                [Scan] │            │
│   └─────────────────────────────────────────────┘               │
│                                                                 │
│   ┌─── Result Card ────────────────────────────────────────┐    │
│   │                                                        │    │
│   │   ┌─────────┐    Prediction: ⛔ PHISHING               │    │
│   │   │  Gauge  │    Risk Score: 94.2%                     │    │
│   │   │  with   │    Risk Level: [CRITICAL]                │    │
│   │   │threshold│    Threshold: 51.5%                      │    │
│   │   │  line   │                                          │    │
│   │   └─────────┘                                          │    │
│   │                                                        │    │
│   │   These factors contributed most to the model's        │    │
│   │   phishing prediction:                                 │    │
│   │   ┌────────────────────────────────────────────────┐   │    │
│   │   │ ⚠ Token similar to known brand (typosquatting)│   │    │
│   │   │ ⚠ Contains login-related keywords              │   │    │
│   │   │ ⚠ Unusual domain length                        │   │    │
│   │   └────────────────────────────────────────────────┘   │    │
│   │                                                        │    │
│   │   Feature Impact                                       │    │
│   │   ┌────────────────────────────────────────────────┐   │    │
│   │   │          ◄── Safe    Risky ──►                 │   │    │
│   │   │ ████████████████████████░░░░░ domain_length    │   │    │
│   │   │ ███████████████░░░░░░░░░░░░░ has_login_keyword │   │    │
│   │   │ ██████████░░░░░░░░░░░░░░░░░░ brand_lev_dist   │   │    │
│   │   │ ░░░░░░░░░░░░░░░░░░░████████ reg_domain_len ↓  │   │    │
│   │   └────────────────────────────────────────────────┘   │    │
│   └────────────────────────────────────────────────────────┘    │
│                                                                 │
│   ┌─── Recent Scans ──────────── [Clear History] ─────────┐    │
│   │  URL                    Score   Prediction   Time      │    │
│   │  paypa1-login.xyz       94.2%   PHISHING     2s ago    │    │
│   │  google.com             3.1%    LEGIT        5m ago    │    │
│   └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Design details:**
- Risk Gauge: semi-circular gauge with **threshold line** (dashed) so user sees "score đã vượt ngưỡng"
  - Green (0-30) → Amber (30-60) → Orange (60-85) → Red (85-100)
- PredictionBadge: binary — `PHISHING` (red) or `LEGITIMATE` (green)
- RiskBadge: severity — `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`
- Reasons header: "These factors contributed most to the model's phishing prediction"
  - **KHÔNG** viết "SHAP explains why the probability is 94.2%"
- SHAP waterfall: horizontal bar chart, blue = decreases risk, red = increases risk
- Recent Scans: persisted qua localStorage, tối đa 20 entries, "Clear History" button
- URL input: chỉ validate `trim() !== ''` + length ≤ 8192. **Không** regex URL validation.

#### 4.3.2 BatchView — Batch Scan

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌─── Upload ─────────────────────────────────────────────┐   │
│   │     ┌──────────────────────────────────┐               │   │
│   │     │   📁 Drop CSV here or click     │               │   │
│   │     │      to browse                   │               │   │
│   │     │      (max 1000 URLs)             │               │   │
│   │     └──────────────────────────────────┘               │   │
│   │                                          [Scan All]    │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─── Summary ────────────────────────────────────────────┐   │
│   │  Total: 150  │  Phishing: 23  │  Legitimate: 127      │   │
│   │  [PIE CHART: risk distribution]                        │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─── Results Table ──────────────────────────────────────┐   │
│   │  # │ URL              │ Score │ Level  │ Actions       │   │
│   │  1 │ evil-site.tk     │ 96.1% │ CRIT   │ [Detail]      │   │
│   │  2 │ safe-bank.com    │  4.2% │ LOW    │ [Detail]      │   │
│   │  ...                                                   │   │
│   │                              [Export CSV] [Export JSON] │   │
│   └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Design details:**
- CSV upload: frontend chỉ UX validation (file extension, file size < 5MB, column "url" exists). Backend là authoritative validator.
- Batch response KHÔNG bao gồm SHAP. Detail button gọi `POST /api/explain` → modal với full waterfall.
- Export: download results as CSV hoặc JSON
- Navigation guard: warning "Unsaved results will be lost" khi navigate away chưa export
- Progress bar during scanning

#### 4.3.3 DashboardView — Model & Insights

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─── Model Info ──────────┐  ┌─── Performance ────────────┐  │
│  │ Model: LightGBM         │  │ F1:        0.9849          │  │
│  │ Version: lgbm_20260815  │  │ Precision: 0.9908          │  │
│  │ Features: 37 (Final)    │  │ Recall:    0.9791          │  │
│  │ Calibration: Isotonic   │  │ ROC-AUC:   0.9971          │  │
│  │ Threshold: 0.515        │  │ PR-AUC:    0.9973          │  │
│  └──────────────────────────┘  └────────────────────────────┘  │
│                                                                 │
│  ┌─── Data Sources ───────────────────────────────────────┐    │
│  │  PhiUSIIL: 195k URLs  │  PhishTank: 55k  │ Tranco: 9k │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── Global Feature Importance (SHAP) ───────────────────┐   │
│  │  domain_length          ████████████████████████  2.28  │   │
│  │  path_length            ███████████████████████   2.21  │   │
│  │  ...                                                    │   │
│  │                              [Show All 37 Features]     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.4 AboutView — Disclaimers

About page bao gồm:

- Project overview và methodology
- Data sources description
- **Disclaimer**: "Risk scores represent calibrated model outputs and should be interpreted as decision-support signals, not absolute guarantees. The model analyzes URL structure only and cannot detect phishing hosted on compromised legitimate websites with clean URL patterns."
- Privacy statement: "Scan history is stored locally in your browser. It is never sent to or persisted by the server beyond the inference request."

### 4.4 Validation Responsibility

| Validation | Frontend | Backend |
| --- | --- | --- |
| URL non-empty | ✓ (UX) | ✓ (authoritative) |
| URL length ≤ 8192 | ✓ (UX) | ✓ (authoritative) |
| URL format/scheme | ✗ | ✓ (url_normalizer.py) |
| CSV file extension | ✓ (UX) | ✗ |
| CSV file size < 5MB | ✓ (UX) | ✓ |
| CSV column "url" exists | ✓ (UX) | ✓ (authoritative) |
| CSV row count ≤ 1000 | ✓ (UX) | ✓ (authoritative) |
| URL normalization | ✗ | ✓ |
| URL security validation | ✗ | ✓ |

> Frontend validation là UX convenience — giúp user thấy lỗi nhanh.
> Backend validation là security boundary — không bao giờ trust client input.

---

## 5. Data Flow

### 5.1 Single Scan Flow

```
User enters URL
    → Frontend: check non-empty + length (UX only)
    → POST /api/scan { url }
    → Backend:
        1. validate_url(url) → normalized_url
        2. extract_features(normalized_url) → feature_dict
        3. Select Final FS (37 features) → feature_vector
        4. calibrated_model.predict_proba(feature_vector) → risk_score
        5. risk_score >= threshold → prediction
        6. map_risk_level(risk_score) → risk_level
        7. explainer.shap_values(feature_vector) → shap_values (base model)
        8. generate_human_reasons(top_features) → reasons
    → Response JSON (risk_score + prediction + explanation)
    → Frontend: display gauge (with threshold line) + prediction badge
                + risk badge + reasons + waterfall
```

### 5.2 Batch Scan Flow

```
User uploads CSV
    → Frontend: check extension + size + column header (UX only)
    → POST /api/scan/batch (multipart/form-data)
    → Backend:
        1. Parse CSV (authoritative) → validate URLs
        2. Batch feature extraction (sequential per URL)
        3. Build feature matrix (N × 37)
        4. calibrated_model.predict_proba(X) → risk_scores (single vectorized call)
        5. Map risk levels (vectorized)
    → Response JSON with results array + summary (no SHAP)
    → Frontend: display table + charts
    → User clicks "Detail" → POST /api/explain → modal with waterfall
```

---

## 6. Risk Level Color System

```javascript
const RISK_COLORS = {
  low:      { bg: '#10B981', text: '#ECFDF5', label: 'LOW' },       // green
  medium:   { bg: '#F59E0B', text: '#FFFBEB', label: 'MEDIUM' },    // amber
  high:     { bg: '#F97316', text: '#FFF7ED', label: 'HIGH' },      // orange
  critical: { bg: '#EF4444', text: '#FEF2F2', label: 'CRITICAL' },  // red
}

// Risk bands (independent of threshold)
// 0.00 - 0.30 → low
// 0.30 - 0.60 → medium
// 0.60 - 0.85 → high
// 0.85 - 1.00 → critical

// Prediction (binary, based on threshold)
// risk_score >= 0.515 → PHISHING
// risk_score <  0.515 → LEGITIMATE
//
// Note: prediction và risk_level là hai concepts độc lập.
// Một URL có thể là prediction=PHISHING + risk_level=MEDIUM (score=0.55)
// UI hiển thị cả hai, gauge vẽ threshold line để user hiểu tại sao.
```

---

## 7. Error Handling

### Backend

| Error               | HTTP Code | Response                                     |
| ------------------- | --------- | -------------------------------------------- |
| Invalid URL         | 422       | `{ "detail": "Invalid URL: {reason}" }`      |
| URL too long        | 422       | `{ "detail": "URL exceeds 8192 characters" }`|
| Batch too large     | 422       | `{ "detail": "Max 1000 URLs per batch" }`    |
| CSV missing column  | 422       | `{ "detail": "CSV must have 'url' column" }` |
| Model not loaded    | 503       | `{ "detail": "Model not available" }`        |
| Internal error      | 500       | `{ "detail": "Internal server error" }`      |

### Frontend

- Network error → toast notification "Cannot connect to server"
- 422 errors → inline validation message dưới input
- 503 → full-page "Service Unavailable" message
- Slow response (> 5s) → loading spinner with "Analyzing..."

---

## 8. Performance Targets

| Metric                    | Target      | Measured (Phase 1) |
| ------------------------- | ----------- | ------------------ |
| Single scan latency       | < 100ms     | ~12ms inference    |
| Single scan + SHAP        | < 500ms     | TBD                |
| Batch scan (1000 URLs)    | < 30s       | TBD                |
| Frontend initial load     | < 2s        | TBD                |
| Cold start (model load)   | < 10s       | TBD                |

---

## 9. Deployment

### 9.1 Hai modes hoạt động

| | Development (Demo) | Production |
| --- | --- | --- |
| Khởi động | 2 lệnh terminal | `docker compose up` |
| Backend | `uvicorn` trực tiếp | Container + Uvicorn |
| Frontend | Vite dev server (HMR) | nginx serve static + reverse proxy |
| API routing | Vite proxy `/api/*` → localhost:8000 | nginx proxy `/api/*` → backend:8000 |
| CORS | Không cần (same origin qua proxy) | Không cần (same origin qua nginx) |
| Hot reload | Có (cả BE lẫn FE) | Không |
| Yêu cầu | Python 3.11+, Node 20+ | Docker + Docker Compose |

### 9.2 Development Mode

**Terminal 1 — Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev    # → http://localhost:5173
```

**Vite config** (`frontend/vite.config.js`):
```javascript
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

> Vite dev server proxy `/api/*` requests sang backend.
> Browser chỉ thấy `localhost:5173` — không cross-origin, không cần CORS.
>
> **TailwindCSS v4 CSS entry** (`src/style.css`): chỉ cần `@import "tailwindcss";`
> — không cần `@tailwind base/components/utilities` như v3.
> Không cần `postcss.config.js` hay `tailwind.config.js`.

### 9.3 Production Mode

**Docker Compose (`docker-compose.yml`):**
```yaml
services:
  backend:
    build: ./backend
    expose:
      - "8000"
    volumes:
      - ./artifacts:/app/artifacts:ro
    environment:
      - MODEL_DIR=/app/artifacts
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**Frontend nginx config** (`frontend/nginx.conf`):
```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 9.4 CORS Fallback

Backend enable CORS cho trường hợp frontend chạy ở origin khác mà không qua proxy
(ví dụ dev frontend connect trực tiếp đến remote backend):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 9.5 Project Root — Single Source of Truth cho Artifacts

```
phishing-url-detection/
├── artifacts/              # From Phase 1 Colab — SINGLE SOURCE OF TRUTH
│   ├── calibrated_model.joblib
│   ├── model.joblib
│   ├── threshold_config.json
│   ├── feature_schema.json
│   ├── model_metadata.json
│   ├── global_feature_importance.csv
│   ├── brand_list.json
│   └── shared_infra_domains.json
├── backend/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
└── README.md
```

> **Không có `backend/artifacts/`.** Backend reference artifacts qua:
> - Development: `MODEL_DIR=../artifacts` (relative path)
> - Production Docker: `volumes: ./artifacts:/app/artifacts:ro`
>
> Một nơi duy nhất, không có risk deploy nhầm model version.

# Backend Work Packages

## Tổng quan

```
WP1 → WP2 → WP3 → WP4 → WP5 → WP6 → WP7 → WP8 → WP9 → WP10
 │                  │                  │
 │ Foundation       │ Intelligence     │ API Layer
 └──────────────────┴──────────────────┴──────────────────────→
```

| WP | Tên | Phụ thuộc | Effort ước tính |
| --- | --- | --- | --- |
| WP1 | Project Scaffolding & Config | — | Nhỏ |
| WP2 | URL Normalizer Service | WP1 | Nhỏ |
| WP3 | Feature Extractor Service | WP1 | Nhỏ |
| WP4 | Predictor Service | WP1 | Trung bình |
| WP5 | SHAP Explainer Service | WP4 | Trung bình |
| WP6 | Risk Mapper Service | WP4 | Nhỏ |
| WP7 | Pydantic Schemas | WP6 | Nhỏ |
| WP8 | API Routers | WP2–WP7 | Trung bình |
| WP9 | Middleware | WP8 | Nhỏ |
| WP10 | Docker & Integration | WP8 | Nhỏ |

---

## WP1: Project Scaffolding & Config

### Mục tiêu
Tạo project structure, cài dependencies, config artifact loading, app khởi động được.

### Deliverables

**1.1 — Project structure**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   └── middleware/
│       └── __init__.py
├── tests/
│   └── __init__.py
└── requirements.txt
```

**1.2 — requirements.txt**
```
fastapi>=0.115
uvicorn>=0.30
pydantic>=2.0
python-multipart>=0.0.9
scikit-learn>=1.5
lightgbm>=4.5
shap>=0.46
pandas>=2.0
numpy>=1.26
tldextract>=5.0
rapidfuzz>=3.0
idna>=3.0
joblib>=1.3
python-dotenv>=1.0
pytest>=8.0
httpx>=0.27
```

**1.3 — app/config.py**
- `MODEL_DIR` từ environment variable, fallback `../artifacts`
- Load tất cả JSON configs (threshold, feature_schema, metadata, brand_list, shared_infra_domains)
- Constants: RISK_LEVEL_BANDS, MAX_URL_LENGTH, MAX_BATCH_SIZE, SUSPICIOUS_TLDS, URL_SHORTENERS, SUSPICIOUS_KEYWORDS
- Pydantic `Settings` class với `model_config = SettingsConfigDict(env_file=".env")`

**1.4 — app/main.py**
- FastAPI app với lifespan (load artifacts at startup)
- CORS middleware (fallback cho dev không qua proxy)
- Router includes (placeholder)
- Root redirect `/` → `/docs`

### Checkpoints

- [ ] `pip install -r requirements.txt` thành công
- [ ] `uvicorn app.main:app --port 8000` khởi động không lỗi
- [ ] `GET http://localhost:8000/docs` hiển thị Swagger UI
- [ ] Console log "Model loaded: lightgbm_..." khi startup
- [ ] `app.state.model` không None sau startup
- [ ] `app.state.calibrated_model` không None sau startup
- [ ] `app.state.threshold_config["threshold"]` = 0.515
- [ ] `app.state.feature_schema["n_features"]` = 37
- [ ] Config đọc đúng brand_list.json (50 brands)
- [ ] Config đọc đúng shared_infra_domains.json

---

## WP2: URL Normalizer Service

### Mục tiêu
Port url_normalizer từ Phase 1 notebook sang backend service, thêm edge case handling.

### Deliverables

**2.1 — app/services/url_normalizer.py**
- `validate_url(url: str) → URLValidationResult`
- `normalize_url(url: str) → str`
- `batch_validate_and_normalize(urls: list[str]) → list[URLValidationResult]`
- Port logic từ Phase 1: percent-decode, punycode/IDN, resolve `/../`, strip default port, lowercase

**2.2 — tests/test_normalizer.py**
- Port tất cả tests từ Phase 1 + thêm edge cases

### Checkpoints

- [ ] `validate_url("")` → `is_valid=False, error="empty_url"`
- [ ] `validate_url("not-a-url")` → auto-prepend `http://`, validate
- [ ] `validate_url("ftp://x.com")` → `is_valid=False, error="unsupported_scheme"`
- [ ] `normalize_url("HTTP://Example.COM/login/")` → `"http://example.com/login"`
- [ ] `normalize_url("http://example.com/a/../login")` → `"http://example.com/login"`
- [ ] `normalize_url("http://example.com/%6c%6f%67%69%6e")` → `"http://example.com/login"`
- [ ] `normalize_url("http://example.com:80/path")` → không có `:80`
- [ ] `normalize_url("https://example.com:443/path")` → không có `:443`
- [ ] `normalize_url("http://example.com:8080/path")` → giữ `:8080`
- [ ] Punycode: `http://xn--pple-43d.com` → normalize thành công
- [ ] URL quá dài (>8192 chars) → `is_valid=False, error="url_too_long"`
- [ ] URL có `@` symbol → normalize giữ nguyên userinfo
- [ ] URL là IP address → normalize giữ nguyên IP
- [ ] `pytest tests/test_normalizer.py` — tất cả pass

---

## WP3: Feature Extractor Service

### Mục tiêu
Port feature_extractor từ Phase 1 notebook, extract đúng 37 features (Final FS).

### Deliverables

**3.1 — app/services/feature_extractor.py**
- `extract_features(url: str) → dict` — extract full V1+V2 features
- `extract_features_final(url: str, feature_names: list[str]) → dict` — extract chỉ Final FS features
- `extract_features_batch(urls: list[str], feature_names: list[str]) → pd.DataFrame` — batch extraction → DataFrame
- Internal helpers: `_entropy()`, `_is_gibberish_token()`, `_randomness_score()`, `_brand_distance()`, `_parse_url()`
- Load brand_list và config từ `app.config`

**3.2 — tests/test_features.py**
- Port tests từ Phase 1 + thêm Final FS specific tests

### Checkpoints

- [ ] `extract_features("http://example.com")` trả về dict với ≥37 keys
- [ ] `extract_features_final(url, schema["feature_names"])` trả về dict với đúng 37 keys
- [ ] Feature names khớp chính xác với `feature_schema.json`
- [ ] `has_https`: `https://...` → 1, `http://...` → 0
- [ ] `has_ip_address`: `http://192.168.1.1` → 1
- [ ] `has_login_keyword`: `http://x.com/login` → 1
- [ ] `contains_brand_token`: `http://paypal-x.com` → 1
- [ ] `brand_levenshtein_min_distance`: `http://paypa1.com` → distance nhỏ (< 20)
- [ ] `subdomain_count`: `http://a.b.c.example.com` → 3
- [ ] `is_suspicious_tld`: `http://x.xyz` → 1
- [ ] `has_url_shortener`: `http://bit.ly/abc` → 1
- [ ] `url_entropy` > 0 cho mọi URL hợp lệ
- [ ] `extract_features_batch(100_urls)` trả về DataFrame shape (100, 37)
- [ ] Feature extraction cho single URL < 50ms
- [ ] `pytest tests/test_features.py` — tất cả pass

---

## WP4: Predictor Service

### Mục tiêu
Inference pipeline: feature vector → calibrated probability → prediction → risk level.

### Deliverables

**4.1 — app/services/predictor.py**
- `predict_single(feature_dict: dict) → PredictionResult` — single URL prediction
- `predict_batch(feature_df: pd.DataFrame) → list[PredictionResult]` — vectorized batch
- Internal: load feature_names từ schema, build feature vector đúng thứ tự, gọi `calibrated_model.predict_proba()`
- `PredictionResult`: dataclass chứa `risk_score`, `prediction`, `risk_level`, `threshold`, `inference_time_ms`

**4.2 — app/models/common.py**
- `RiskLevel` enum: LOW, MEDIUM, HIGH, CRITICAL
- `PredictionResult` dataclass
- `map_risk_level(score: float) → RiskLevel`

### Checkpoints

- [ ] `predict_single(features)` trả về `PredictionResult` với tất cả fields
- [ ] `risk_score` nằm trong [0, 1]
- [ ] `prediction` = "phishing" khi `risk_score >= 0.515`
- [ ] `prediction` = "legitimate" khi `risk_score < 0.515`
- [ ] `risk_level` mapping đúng: 0.1→LOW, 0.4→MEDIUM, 0.7→HIGH, 0.9→CRITICAL
- [ ] `threshold` = 0.515 (từ config)
- [ ] `inference_time_ms` > 0
- [ ] `predict_batch(df_100)` trả về list 100 results
- [ ] Batch dùng single `predict_proba(X)` call — verify bằng mock/spy
- [ ] Feature vector order khớp với `feature_schema.json["feature_names"]`
- [ ] Prediction cho `https://google.com/` → legitimate (risk_score thấp)
- [ ] Prediction cho URL phishing mẫu → phishing (risk_score cao)

---

## WP5: SHAP Explainer Service

### Mục tiêu
SHAP TreeExplainer trên base model — local explanation per URL + cached global importance.

### Deliverables

**5.1 — app/services/explainer.py**
- `explain_single(feature_dict: dict) → ExplanationResult` — local SHAP values + top features + reasons
- `get_global_importance() → list[dict]` — cached global feature importance từ CSV
- `generate_human_reasons(top_features: list) → list[str]` — SHAP values → human-readable text
- Feature explanation mapping dict (feature → positive/negative reason text)

**5.2 — ExplanationResult dataclass**
- `type`: "shap"
- `model_output`: "raw"
- `note`: "SHAP values explain the underlying LightGBM decision before probability calibration"
- `top_features`: list of {feature, value, shap_value, direction}
- `reasons`: list of human-readable strings
- `waterfall_data`: {features, values, cumulative} cho frontend chart
- `base_value`: float
- `all_shap_values`: dict
- `latency_ms`: float

### Checkpoints

- [ ] `explain_single(features)` trả về `ExplanationResult` với tất cả fields
- [ ] `type` = "shap", `model_output` = "raw"
- [ ] `note` chứa "before probability calibration"
- [ ] `top_features` có ≤ 6 entries, sorted by |shap_value| desc
- [ ] Mỗi top_feature có `direction` = "increases_risk" hoặc "decreases_risk"
- [ ] `reasons` có ≤ 6 entries, đều là human-readable strings
- [ ] `waterfall_data.features` list length = 37 (hoặc top N)
- [ ] `waterfall_data.cumulative[0]` = `base_value`
- [ ] `base_value` là float hợp lệ
- [ ] `latency_ms` > 0, < 500 (performance target)
- [ ] `get_global_importance()` trả về list 37 dicts, sorted desc
- [ ] Global importance cached — gọi lần 2 không đọc file lại
- [ ] `explain_single()` cho URL phishing → top features hợp lý (domain_length, brand_distance...)
- [ ] `explain_single()` cho URL legitimate → top features explain tại sao safe

---

## WP6: Risk Mapper Service

### Mục tiêu
Map risk score → risk level + cung cấp risk metadata cho API response.

### Deliverables

**6.1 — app/services/risk_mapper.py**
- `map_risk_level(score: float) → RiskLevel` — score → LOW/MEDIUM/HIGH/CRITICAL
- `get_risk_color(level: RiskLevel) → dict` — level → {bg, text, label}
- `get_risk_bands() → list[dict]` — trả về danh sách bands cho frontend gauge rendering

### Checkpoints

- [ ] `map_risk_level(0.15)` → LOW
- [ ] `map_risk_level(0.45)` → MEDIUM
- [ ] `map_risk_level(0.72)` → HIGH
- [ ] `map_risk_level(0.92)` → CRITICAL
- [ ] Boundary cases: `map_risk_level(0.30)` → MEDIUM (lower inclusive)
- [ ] Boundary cases: `map_risk_level(0.85)` → CRITICAL
- [ ] `map_risk_level(0.0)` → LOW, `map_risk_level(1.0)` → CRITICAL
- [ ] `get_risk_bands()` trả về 4 bands với đúng boundaries

---

## WP7: Pydantic Schemas

### Mục tiêu
Định nghĩa request/response schemas cho tất cả API endpoints.

### Deliverables

**7.1 — app/schemas/scan.py**
```python
class ScanRequest(BaseModel):
    url: str  # raw URL from user

class ScanResponse(BaseModel):
    url: str
    normalized_url: str
    prediction: str                     # "phishing" | "legitimate"
    risk_score: float                   # 0-1, calibrated
    risk_level: str                     # "low" | "medium" | "high" | "critical"
    threshold: float
    explanation: ExplanationResponse    # SHAP explanation
    inference_time_ms: float
    model_version: str

class BatchScanRequest:                 # multipart/form-data, handled by UploadFile

class BatchResultItem(BaseModel):
    url: str
    prediction: str
    risk_score: float
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
```

**7.2 — app/schemas/explain.py**
```python
class ExplainRequest(BaseModel):
    url: str

class FeatureContribution(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str                      # "increases_risk" | "decreases_risk"

class WaterfallData(BaseModel):
    features: list[str]
    values: list[float]
    cumulative: list[float]

class ExplanationResponse(BaseModel):
    type: str                           # "shap"
    model_output: str                   # "raw"
    note: str
    base_value: float
    top_features: list[FeatureContribution]
    reasons: list[str]
    waterfall_data: WaterfallData

class ExplainResponse(BaseModel):
    url: str
    risk_score: float
    explanation: ExplanationResponse
```

### Checkpoints

- [ ] `ScanRequest(url="https://example.com")` — validate thành công
- [ ] `ScanRequest(url="")` — Pydantic raise ValidationError
- [ ] `ScanResponse` serialize ra JSON khớp format trong architecture
- [ ] `BatchScanResponse` chứa `results` list + `summary` object
- [ ] `ExplanationResponse.model_output` = "raw" (hardcoded)
- [ ] `FeatureContribution.direction` chỉ chấp nhận "increases_risk" hoặc "decreases_risk"
- [ ] Tất cả schemas có example trong docstring cho Swagger UI

---

## WP8: API Routers

### Mục tiêu
Implement tất cả endpoints, wire services vào routers, end-to-end flow hoạt động.

### Deliverables

**8.1 — app/routers/scan.py**
- `POST /api/scan` — single URL scan (normalize → extract → predict → explain → respond)
- `POST /api/scan/batch` — batch scan (parse CSV → validate → batch extract → vectorized predict → respond)
- CSV parsing: `UploadFile` → pandas → validate column "url", row count ≤ 1000, file size ≤ 5MB
- Error handling: invalid URL → 422, batch too large → 422, model not loaded → 503

**8.2 — app/routers/explain.py**
- `POST /api/explain` — detailed SHAP explanation (normalize → extract → predict → full SHAP → respond)

**8.3 — app/routers/model_info.py**
- `GET /api/model-info` — trả về model metadata + global feature importance
- `GET /api/health` — health check: model_loaded, model_version, uptime

**8.4 — tests/test_scan_api.py + tests/test_explain_api.py**
- Integration tests dùng `httpx.AsyncClient` + `TestClient`

### Checkpoints

**Single scan:**
- [ ] `POST /api/scan {"url": "https://google.com"}` → 200, prediction="legitimate"
- [ ] `POST /api/scan {"url": "http://paypa1-login.xyz/verify"}` → 200, prediction="phishing"
- [ ] Response JSON chứa tất cả fields theo `ScanResponse` schema
- [ ] `explanation.type` = "shap", `explanation.model_output` = "raw"
- [ ] `explanation.reasons` là list non-empty strings cho phishing URLs
- [ ] `explanation.waterfall_data` có đủ data cho frontend chart
- [ ] `inference_time_ms` < 500
- [ ] `POST /api/scan {"url": ""}` → 422
- [ ] `POST /api/scan {"url": "ftp://x.com"}` → 422 với error message

**Batch scan:**
- [ ] Upload CSV 10 URLs → 200, response có `total=10`, `results` list 10 items
- [ ] Upload CSV 1001 URLs → 422 "Max 1000 URLs per batch"
- [ ] Upload CSV không có column "url" → 422
- [ ] Upload file > 5MB → 422
- [ ] Upload file không phải CSV → 422
- [ ] Batch response không chứa `explanation` (SHAP)
- [ ] `summary.risk_distribution` tổng = `total`
- [ ] Batch 100 URLs < 10s

**Explain:**
- [ ] `POST /api/explain {"url": "https://paypa1.com"}` → 200 với full SHAP data
- [ ] Response chứa `waterfall_data` với `cumulative` array
- [ ] Response chứa `base_value` float

**Model info & health:**
- [ ] `GET /api/model-info` → 200, chứa model_name, model_version, threshold, metrics
- [ ] `GET /api/model-info` → chứa `global_feature_importance` list 37 items
- [ ] `GET /api/health` → 200, `status="healthy"`, `model_loaded=true`
- [ ] `GET /api/health` → `uptime_seconds` > 0

**Cross-cutting:**
- [ ] Swagger UI (`/docs`) hiển thị tất cả endpoints với examples
- [ ] Tất cả endpoints trả về `Content-Type: application/json`
- [ ] `pytest tests/test_scan_api.py tests/test_explain_api.py` — tất cả pass

---

## WP9: Middleware

### Mục tiêu
Privacy-aware logging và rate limiting.

### Deliverables

**9.1 — app/middleware/request_logger.py**
- Log mỗi prediction: timestamp, url_hash (SHA-256), risk_score, prediction, inference_time_ms, model_version
- KHÔNG log: raw URL, feature vector, user IP
- Log format: JSON lines, ghi vào file `logs/predictions.jsonl`

**9.2 — app/middleware/rate_limiter.py**
- Simple in-memory rate limiting
- Single scan: 60 requests/minute per IP
- Batch scan: 10 requests/minute per IP
- Return 429 Too Many Requests khi exceed

### Checkpoints

**Logger:**
- [ ] Scan URL → log entry xuất hiện trong `logs/predictions.jsonl`
- [ ] Log entry có: timestamp, url_hash, risk_score, prediction, inference_time_ms, model_version
- [ ] Log entry KHÔNG có: raw URL
- [ ] `url_hash` là SHA-256 hex string (64 chars)
- [ ] Batch scan → log N entries (một per URL)
- [ ] Log file parseable bằng `json.loads()` per line

**Rate limiter:**
- [ ] 61st single scan request trong 1 phút → 429
- [ ] 11th batch scan request trong 1 phút → 429
- [ ] 429 response chứa `Retry-After` header
- [ ] Rate limit reset sau 1 phút

---

## WP10: Docker & Integration

### Mục tiêu
Dockerize backend, integration test end-to-end, sẵn sàng cho frontend integration.

### Deliverables

**10.1 — Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**10.2 — Integration test script**
- Script chạy backend + test tất cả endpoints end-to-end
- Verify artifacts loaded đúng
- Verify prediction output hợp lý

### Checkpoints

**Docker:**
- [ ] `docker build -t phishing-backend .` thành công
- [ ] `docker run -v $(pwd)/../artifacts:/app/artifacts:ro -p 8000:8000 phishing-backend` khởi động
- [ ] Container log "Model loaded: lightgbm_..."
- [ ] `GET http://localhost:8000/api/health` → 200 từ Docker container
- [ ] `POST /api/scan` hoạt động từ Docker container

**Integration end-to-end:**
- [ ] Backend startup → model loaded → health check pass
- [ ] Single scan: URL → normalize → features → predict → explain → response (< 500ms)
- [ ] Batch scan: CSV 100 URLs → results (< 10s)
- [ ] Explain: URL → full SHAP waterfall data
- [ ] Model info: metadata + global importance
- [ ] Error cases: invalid URL → 422, empty body → 422
- [ ] CORS headers present khi request từ allowed origin
- [ ] Prediction logger ghi log đúng format
- [ ] Rate limiter hoạt động

**Dev mode verification:**
- [ ] `cd backend && uvicorn app.main:app --reload --port 8000` — hoạt động
- [ ] Hot reload: sửa code → server restart tự động
- [ ] Swagger UI hiển thị tất cả endpoints, try-it-out hoạt động

---

## Thứ tự thực hiện khuyến nghị

```
Ngày 1:  WP1 (scaffolding) + WP2 (normalizer) + WP3 (features)
         → Backend khởi động, core services hoạt động, tests pass

Ngày 2:  WP4 (predictor) + WP6 (risk mapper) + WP7 (schemas)
         → Inference pipeline hoàn chỉnh, schemas defined

Ngày 3:  WP5 (explainer)
         → SHAP explanation hoạt động, latency benchmark

Ngày 4:  WP8 (routers) + integration tests
         → Tất cả API endpoints hoạt động end-to-end

Ngày 5:  WP9 (middleware) + WP10 (Docker)
         → Production-ready: logging, rate limiting, containerized
```

Mỗi WP kết thúc bằng tất cả checkpoints pass. Nếu checkpoint nào fail, fix trước khi sang WP tiếp theo.

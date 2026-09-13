# Frontend Work Packages

## Tổng quan

```
WP1 → WP2 → WP3 ──→ WP4 ──→ WP5 ──→ WP6 ──→ WP7 ──→ WP8
 │           │        │        │        │        │        │
 │ Setup     │ Infra  │ Core   │ Batch  │ Info   │ Info   │ Polish
 │           │        │ Page   │ Page   │ Pages  │        │
```

| WP | Tên | Phụ thuộc | Effort |
| --- | --- | --- | --- |
| WP1 | Project Scaffolding | — | Nhỏ |
| WP2 | Layout Shell & Navigation | WP1 | Nhỏ |
| WP3 | API Client & Store | WP1 | Nhỏ |
| WP4 | ScanView — Trang chính | WP2, WP3 | Lớn |
| WP5 | BatchView — Batch Scan | WP3, WP4 (reuse components) | Trung bình |
| WP6 | DashboardView — Model Info | WP3 | Trung bình |
| WP7 | AboutView | WP2 | Nhỏ |
| WP8 | Polish & Integration | WP4–WP7 | Trung bình |

---

## WP1: Project Scaffolding

### Mục tiêu
Vue 3 project chạy được, TailwindCSS v4 hoạt động, routing setup, dev server proxy đúng.

### Deliverables

**1.1 — Khởi tạo project**
```bash
npm create vite@latest frontend -- --template vue
cd frontend
npm install
```

**1.2 — Install dependencies**
```bash
# Core
npm install vue-router@4 pinia axios

# UI
npm install @tailwindcss/vite tailwindcss
npm install echarts vue-echarts
npm install lucide-vue-next
npm install vue3-toastify
npm install pinia-plugin-persistedstate
```

**1.3 — vite.config.js**
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

**1.4 — CSS entry** (`src/style.css`)
```css
@import "tailwindcss";
```

**1.5 — Cấu trúc thư mục**
```
src/
├── App.vue
├── main.js
├── style.css
├── router/
│   └── index.js
├── stores/
├── api/
├── views/
├── components/
│   ├── scan/
│   ├── batch/
│   ├── dashboard/
│   └── layout/
└── utils/
```

### Checkpoints

- [ ] `npm run dev` khởi động thành công → `http://localhost:5173`
- [ ] TailwindCSS hoạt động: thêm `class="text-red-500"` → text đỏ
- [ ] Vue Router: navigate giữa `/` , `/batch`, `/dashboard`, `/about` không reload trang
- [ ] Vite proxy: `fetch('/api/health')` từ browser → nhận response từ backend (cần backend đang chạy)
- [ ] Console không có warning/error
- [ ] `npm run build` thành công, output trong `dist/`

---

## WP2: Layout Shell & Navigation

### Mục tiêu
App shell với header, sidebar/navigation, footer. Responsive layout.

### Deliverables

**2.1 — AppHeader.vue**

```
┌─────────────────────────────────────────────────────────────────┐
│  🛡️ PhishGuard                    [Scan] [Batch] [Dashboard]    │
│                                    [About]              │
└─────────────────────────────────────────────────────────────────┘
```

Thiết kế:
- **Logo + tên app** bên trái: icon shield (lucide `Shield`) + text "PhishGuard" hoặc tên project
- **Navigation links** bên phải: 4 links, active state highlight
- Sticky top, `z-50`, border-bottom subtle
- Height: `h-16`
- Background: white (light) / slate-900 (dark-ready nhưng chưa cần implement dark mode)
- Nav links: text-sm font-medium, hover underline, active link có màu primary (blue-600)
- Mobile: hamburger menu collapse nav links (responsive ≤ 768px)

**2.2 — App.vue layout**

```
┌────────────────────────────────────┐
│           AppHeader                │  ← sticky top
├────────────────────────────────────┤
│                                    │
│         <RouterView />             │  ← main content, min-height fill
│                                    │
├────────────────────────────────────┤
│           AppFooter                │  ← bottom
└────────────────────────────────────┘
```

Thiết kế:
- Layout: flex-col, min-h-screen
- Main content: flex-1, max-w-5xl mx-auto, px-4 py-8
- Không dùng sidebar (overkill cho 4 pages) — top navigation đủ

**2.3 — AppFooter.vue**

```
┌─────────────────────────────────────────────────────────────────┐
│  Phishing URL Detection with Explainable ML — Graduation Project│
│  Built with FastAPI + Vue 3 + LightGBM                          │
└─────────────────────────────────────────────────────────────────┘
```

Thiết kế:
- Text center, text-sm text-gray-500
- Border-top subtle, py-6
- 2 dòng: project title + tech stack

### Checkpoints

- [ ] Header hiển thị logo + 4 nav links
- [ ] Click nav link → navigate đúng route, không reload
- [ ] Active route highlight (màu khác hoặc underline)
- [ ] Layout: header sticky, content fills viewport, footer ở cuối
- [ ] Responsive ≤768px: nav links collapse thành hamburger menu
- [ ] Hamburger menu mở/đóng đúng
- [ ] Footer hiển thị đúng text
- [ ] Không có layout shift khi navigate giữa pages
- [ ] Content area max-width giới hạn (~1024-1280px), center aligned

---

## WP3: API Client & Store

### Mục tiêu
Axios client với error handling, Pinia store cho scan history (persisted).

### Deliverables

**3.1 — api/client.js**

```javascript
import axios from 'axios'
import { toast } from 'vue3-toastify'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,       // 30s cho batch
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      toast.error('Cannot connect to server')
    } else if (error.response.status === 503) {
      toast.error('Model not available. Please try again later.')
    } else if (error.response.status === 429) {
      toast.warning('Too many requests. Please slow down.')
    }
    // 422 errors handled inline by components
    return Promise.reject(error)
  }
)

export default apiClient

// API functions
export const scanUrl = (url) => apiClient.post('/scan', { url })
export const scanBatch = (formData) => apiClient.post('/scan/batch', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  timeout: 60000,
})
export const explainUrl = (url) => apiClient.post('/explain', { url })
export const getModelInfo = () => apiClient.get('/model-info')
export const getHealth = () => apiClient.get('/health')
```

**3.2 — stores/scanHistory.js**

```javascript
import { defineStore } from 'pinia'

export const useScanHistory = defineStore('scanHistory', {
  state: () => ({
    recentScans: [],       // max 20 entries
    maxEntries: 20,
  }),
  actions: {
    addScan(result) {
      this.recentScans.unshift({
        url: result.url,
        risk_score: result.risk_score,
        prediction: result.prediction,
        risk_level: result.risk_level,
        scanned_at: new Date().toISOString(),
      })
      if (this.recentScans.length > this.maxEntries) {
        this.recentScans.pop()
      }
    },
    clearHistory() {
      this.recentScans = []
    },
  },
  persist: true,           // pinia-plugin-persistedstate
})
```

**3.3 — utils/riskColors.js**

```javascript
export const RISK_COLORS = {
  low:      { bg: '#10B981', bgLight: '#ECFDF5', text: '#065F46', label: 'LOW' },
  medium:   { bg: '#F59E0B', bgLight: '#FFFBEB', text: '#92400E', label: 'MEDIUM' },
  high:     { bg: '#F97316', bgLight: '#FFF7ED', text: '#9A3412', label: 'HIGH' },
  critical: { bg: '#EF4444', bgLight: '#FEF2F2', text: '#991B1B', label: 'CRITICAL' },
}

export const PREDICTION_COLORS = {
  phishing:   { bg: '#EF4444', bgLight: '#FEF2F2', text: '#991B1B', icon: 'ShieldAlert' },
  legitimate: { bg: '#10B981', bgLight: '#ECFDF5', text: '#065F46', icon: 'ShieldCheck' },
}

export function getRiskColor(level) {
  return RISK_COLORS[level] || RISK_COLORS.low
}
```

**3.4 — utils/formatters.js**

```javascript
export function formatPercent(value) {
  return (value * 100).toFixed(1) + '%'
}

export function formatTimeAgo(isoString) {
  const seconds = Math.floor((Date.now() - new Date(isoString)) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function truncateUrl(url, maxLen = 50) {
  if (url.length <= maxLen) return url
  return url.substring(0, maxLen - 3) + '...'
}
```

### Checkpoints

- [ ] `apiClient.get('/health')` trả về data khi backend chạy
- [ ] Network error → toast "Cannot connect to server" xuất hiện
- [ ] 503 error → toast "Model not available" xuất hiện
- [ ] 429 error → toast "Too many requests" xuất hiện
- [ ] `useScanHistory().addScan(result)` → `recentScans.length` = 1
- [ ] Thêm 21 scans → `recentScans.length` = 20 (capped)
- [ ] `clearHistory()` → `recentScans.length` = 0
- [ ] Refresh browser → `recentScans` vẫn còn (localStorage persist)
- [ ] `formatPercent(0.9423)` → `"94.2%"`
- [ ] `truncateUrl("http://very-long-url...", 30)` → truncated + "..."
- [ ] Toast notifications render đúng vị trí (top-right), auto-dismiss

---

## WP4: ScanView — Trang chính

### Mục tiêu
Trang scan single URL — input, kết quả, SHAP explanation, recent scans. Đây là trang quan trọng nhất.

### Deliverables & Design

**4.1 — UrlInput.vue**

```
┌─────────────────────────────────────────────────────────────┐
│  🔍  Enter a URL to analyze...                     [Scan ➜] │
└─────────────────────────────────────────────────────────────┘
   ⚠ URL cannot be empty                    ← inline error (red)
```

Thiết kế:
- Full width input, h-12, rounded-xl, border gray-300, focus:ring-2 ring-blue-500
- Search icon (lucide `Search`) bên trái, padding-left cho icon
- Scan button bên phải, bg-blue-600, text-white, rounded-r-xl, hover:bg-blue-700
- Button disabled + spinner khi đang loading
- Inline error text dưới input: text-sm text-red-500, chỉ hiện khi validate fail
- Validation: chỉ check `trim() !== ''` + `length ≤ 8192`
- Enter key triggers scan
- Auto-focus khi page load

**4.2 — Result Card (ScanView container)**

```
┌─── Scan Result ─────────────────────────────────────────────────┐
│                                                                  │
│   ┌─────────────────────┐  ┌──────────────────────────────────┐ │
│   │                     │  │                                  │ │
│   │     RiskGauge       │  │  PredictionBadge: ⛔ PHISHING   │ │
│   │     (semi-circle)   │  │                                  │ │
│   │                     │  │  Risk Score: 94.2%               │ │
│   │     94.2%           │  │  Risk Level: [CRITICAL]          │ │
│   │     ╌╌╌╌╌ 51.5%    │  │  Threshold:  51.5%               │ │
│   │     threshold line  │  │                                  │ │
│   └─────────────────────┘  └──────────────────────────────────┘ │
│                                                                  │
│   ─── Why this prediction? ───────────────────────────────────── │
│                                                                  │
│   ReasonsList                                                    │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  ⚠ Token similar to known brand (possible typosquatting)│  │
│   │  ⚠ Contains login-related keywords                      │  │
│   │  ⚠ Unusual domain length                                │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ─── Feature Impact ────────────────────────────────────────── │
│                                                                  │
│   FeatureWaterfall (ECharts)                                     │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │       ◄── Decreases risk    Increases risk ──►           │  │
│   │ ██████████████████████████░░░░░ domain_length   +2.34   │  │
│   │ █████████████████░░░░░░░░░░░░░ has_login_kw     +1.87   │  │
│   │ ████████████░░░░░░░░░░░░░░░░░░ brand_lev_dist   +1.12   │  │
│   │ ░░░░░░░░░░░░░░░░░░░░░████████ reg_domain_len   -0.85   │  │
│   │ ░░░░░░░░░░░░░░░░░░░████░░░░░░ path_entropy     -0.42   │  │
│   │ ░░░░░░░░░░░░░░░░░██░░░░░░░░░░ subdomain_count  -0.28   │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ℹ SHAP values explain the underlying model decision before    │
│     probability calibration.                                     │
└──────────────────────────────────────────────────────────────────┘
```

Layout:
- Rounded-2xl border, shadow-sm, bg-white, p-6
- Top section: 2 columns (gauge left, metadata right) trên desktop, stack trên mobile
- Sections divided by subtle divider (border-t border-gray-100 my-4)
- Khi chưa scan: hidden (v-if="result")
- Animate entrance: fade + slide-up khi result xuất hiện

**4.3 — RiskGauge.vue**

Thiết kế chi tiết:
- Semi-circular gauge (180°), width 200px
- ECharts gauge series với custom color bands:
  - 0-30%: #10B981 (green)
  - 30-60%: #F59E0B (amber)
  - 60-85%: #F97316 (orange)
  - 85-100%: #EF4444 (red)
- **Threshold line**: dashed mark tại 51.5%, labelcó text nhỏ "Threshold"
- Center text: risk score percentage, font-bold text-2xl
- Pointer animation: từ 0 sweep đến giá trị score
- Props: `score` (0-1), `threshold` (0-1)

**4.4 — PredictionBadge.vue**

Thiết kế:
- Pill shape, px-4 py-2, rounded-full, font-semibold, text-sm uppercase
- PHISHING: bg-red-100 text-red-800, icon ShieldAlert
- LEGITIMATE: bg-green-100 text-green-800, icon ShieldCheck
- Props: `prediction` ("phishing" | "legitimate")

**4.5 — RiskBadge.vue**

Thiết kế:
- Pill shape nhỏ hơn PredictionBadge, px-3 py-1, rounded-full, text-xs uppercase
- Color theo RISK_COLORS mapping
- Props: `level` ("low" | "medium" | "high" | "critical")

**4.6 — ReasonsList.vue**

Thiết kế:
- Header: "These factors contributed most to the model's phishing prediction"
  - Nếu legitimate: "These factors indicate the URL appears safe"
- List items: icon ⚠ (AlertTriangle cho phishing, CheckCircle cho legitimate) + text
- Items: py-2, border-b last:border-0, text-sm
- Max 6 items
- Props: `reasons` (string[]), `prediction` ("phishing" | "legitimate")

**4.7 — FeatureWaterfall.vue**

Thiết kế:
- ECharts horizontal bar chart
- Bars: đỏ (#EF4444) cho positive SHAP (increases risk), xanh (#3B82F6) cho negative (decreases risk)
- Y axis: feature names (top 6-8 by |shap_value|)
- X axis: SHAP value, centered at 0
- Each bar labeled with SHAP value (+2.34 / -0.85)
- Below chart: footnote italic text-xs text-gray-400: "SHAP values explain the underlying model decision before probability calibration."
- Height: 250-300px
- Props: `topFeatures` (array of {feature, shap_value, direction}), `baseValue` (float)

**4.8 — RecentScans section (trong ScanView)**

```
┌─── Recent Scans ───────────────────────── [Clear History] ──┐
│  URL                        Score    Prediction    Time      │
│  paypa1-login.xyz           94.2%    🔴 PHISHING   2s ago    │
│  google.com                  3.1%    🟢 LEGIT      5m ago    │
│  verify-account.tk          87.5%    🔴 PHISHING   8m ago    │
│                                                              │
│  (click a row to scan that URL again)                        │
└──────────────────────────────────────────────────────────────┘
```

Thiết kế:
- Header row: text-xs uppercase text-gray-500 tracking-wider
- Data rows: hover:bg-gray-50, cursor-pointer (click → scan lại URL đó)
- URL column: truncate nếu dài, font-mono text-sm
- Score: font-semibold, colored theo risk level
- Prediction: PredictionBadge mini (inline, nhỏ hơn)
- Time: formatTimeAgo(), text-gray-400
- "Clear History" button: text-sm text-red-500 hover:underline, ở header right
- Empty state: "No recent scans" text-gray-400 italic, centered
- Max 20 rows, scrollable nếu cần

**4.9 — Loading & Error states**

- Scanning: button disabled + spinner, text "Analyzing..."
- Slow (>3s): thêm progress bar indeterminate dưới input
- Error 422 (invalid URL): inline error dưới input, toast không cần
- Error 500/503: toast error notification
- Network error: toast "Cannot connect to server"

### Checkpoints

**UrlInput:**
- [ ] Input auto-focus khi page load
- [ ] Nhập URL + Enter → trigger scan
- [ ] Click button → trigger scan
- [ ] Empty input + scan → inline error "URL cannot be empty"
- [ ] Đang loading → button disabled + spinner
- [ ] Input > 8192 chars → inline error "URL too long"

**Result Card:**
- [ ] Scan legitimate URL → Result card xuất hiện, prediction=LEGITIMATE (green)
- [ ] Scan phishing URL → prediction=PHISHING (red), risk level=HIGH/CRITICAL
- [ ] Result card có animation entrance (fade/slide)
- [ ] Khi chưa scan → result card hidden

**RiskGauge:**
- [ ] Score 0.94 → pointer ở vùng đỏ, text "94.2%"
- [ ] Score 0.15 → pointer ở vùng xanh, text "15.0%"
- [ ] Threshold line hiển thị tại 51.5%
- [ ] Pointer có animation sweep
- [ ] Color bands đúng: green/amber/orange/red

**PredictionBadge + RiskBadge:**
- [ ] "phishing" → red pill với ShieldAlert icon
- [ ] "legitimate" → green pill với ShieldCheck icon
- [ ] Risk level "critical" → red badge, "low" → green badge

**ReasonsList:**
- [ ] Phishing URL → hiển thị reasons với ⚠ icons
- [ ] Legitimate URL → hiển thị reasons với ✓ icons (hoặc ẩn nếu empty)
- [ ] Header text đúng theo prediction type
- [ ] Max 6 items hiển thị

**FeatureWaterfall:**
- [ ] ECharts render horizontal bar chart
- [ ] Positive SHAP → red bar bên phải
- [ ] Negative SHAP → blue bar bên trái
- [ ] Feature names hiển thị trên Y axis
- [ ] SHAP values labeled trên mỗi bar
- [ ] Footnote về calibration hiển thị dưới chart
- [ ] 6-8 features hiển thị (top by |shap_value|)

**RecentScans:**
- [ ] Scan URL → entry mới xuất hiện ở đầu list
- [ ] Max 20 entries
- [ ] "Clear History" → list trống, localStorage cleared
- [ ] Click row → input nhận URL đó, trigger scan
- [ ] Refresh browser → list vẫn còn (localStorage)
- [ ] Time column hiển thị "Xs ago", "Xm ago" đúng
- [ ] Empty state: "No recent scans"

**End-to-end ScanView:**
- [ ] Nhập `https://google.com` → scan → result legitimate → entry trong recent scans
- [ ] Nhập `http://paypa1-login.xyz` → scan → result phishing → gauge đỏ, reasons list, waterfall
- [ ] Scan 3 URLs liên tiếp → recent scans có 3 entries đúng thứ tự
- [ ] Response time < 1s cho single scan (cảm nhận instant)

---

## WP5: BatchView — Batch Scan

### Mục tiêu
Upload CSV, batch scan, results table, export, detail modal.

### Deliverables & Design

**5.1 — CsvUploader.vue**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│     ┌───────────────────────────────────────────────┐       │
│     │                                               │       │
│     │     📁  Drop CSV file here                   │       │
│     │         or click to browse                    │       │
│     │                                               │       │
│     │     Accepted: .csv, max 5MB, max 1000 URLs    │       │
│     │     Required column: "url"                    │       │
│     │                                               │       │
│     └───────────────────────────────────────────────┘       │
│                                                             │
│     file-selected.csv  (342 URLs detected)     [Remove]     │
│                                                             │
│                                          [Scan All URLs ➜]  │
└─────────────────────────────────────────────────────────────┘
```

Thiết kế:
- Drop zone: border-2 border-dashed border-gray-300, rounded-xl, h-48
- Drag hover state: border-blue-500 bg-blue-50
- File selected state: file name + row count preview + remove button
- UX validation: .csv extension, file size < 5MB, parse header row check column "url"
- "Scan All URLs" button: bg-blue-600, disabled until file validated
- Loading state: button disabled + progress bar

**5.2 — Scanning Progress**

```
┌─────────────────────────────────────────────────────────────┐
│  Scanning 342 URLs...                                       │
│  ████████████████████████░░░░░░░░░░░  68%  (232/342)        │
│                                          [Cancel]           │
└─────────────────────────────────────────────────────────────┘
```

Thiết kế:
- Progress bar: h-2, bg-blue-600, rounded-full, animate width
- Text: "Scanning X URLs..." + percentage + count
- Cancel button: text-sm text-gray-500
- Note: progress là simulated (0→100% over estimated time) vì batch là single API call

**5.3 — Batch Summary Cards**

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐
│ Total    │  │ Phishing │  │ Legit    │  │  Risk Distribution   │
│   342    │  │    23    │  │   319    │  │  [PIE CHART]         │
│          │  │  🔴 6.7% │  │ 🟢 93.3% │  │  crit/high/med/low   │
└──────────┘  └──────────┘  └──────────┘  └──────────────────────┘
```

Thiết kế:
- 4 cards inline, rounded-xl, shadow-sm, p-4
- Stat cards: large number (text-3xl font-bold), label dưới (text-sm text-gray-500)
- Phishing card: red accent, Legitimate card: green accent
- Pie chart: ECharts donut, 4 segments (critical/high/medium/low) với risk colors
- Responsive: 2×2 grid trên mobile

**5.4 — BatchResultsTable.vue**

```
┌──────────────────────────────────────────────────────────────────┐
│ Filter: [All ▾]  [Phishing only]  [Legit only]   Search: [___] │
├──────────────────────────────────────────────────────────────────┤
│  #  │ URL                          │ Score  │ Level    │ Action │
│ ────┼──────────────────────────────┼────────┼──────────┼────────│
│  1  │ evil-site.tk/login           │ 96.1%  │ 🔴 CRIT  │ [📋]  │
│  2  │ suspicious.xyz/verify        │ 72.3%  │ 🟠 HIGH  │ [📋]  │
│  3  │ safe-bank.com                │  4.2%  │ 🟢 LOW   │ [📋]  │
│ ... │                              │        │          │        │
├──────────────────────────────────────────────────────────────────┤
│  Showing 1-20 of 342          [◄] [1] [2] [3] ... [18] [►]     │
│                                      [Export CSV] [Export JSON]  │
└──────────────────────────────────────────────────────────────────┘
```

Thiết kế:
- Sortable: click header → sort asc/desc (default: score desc = phishing first)
- Filterable: dropdown All/Phishing/Legitimate + text search by URL
- Pagination: 20 rows per page, client-side
- Risk level cell: RiskBadge component
- Score cell: colored text theo risk level
- Action cell: Detail button (lucide `FileSearch`) → open ExplainModal
- URL column: font-mono text-sm, truncate + tooltip on hover
- Export buttons: bottom right, outline style
- Responsive: horizontal scroll trên mobile

**5.5 — ExplainModal.vue**

```
┌─── URL Explanation ─────────────────────────── [✕] ─┐
│                                                      │
│  URL: evil-site.tk/login                             │
│  Risk Score: 96.1%  |  Prediction: 🔴 PHISHING      │
│                                                      │
│  ─── Why this prediction? ─────────────────────────  │
│  ⚠ Contains login-related keywords                  │
│  ⚠ Suspicious TLD                                   │
│                                                      │
│  ─── Feature Impact ───────────────────────────────  │
│  [SHAP WATERFALL CHART]                              │
│                                                      │
│  ℹ SHAP values explain the underlying model          │
│    decision before probability calibration.           │
│                                                      │
│                                           [Close]    │
└──────────────────────────────────────────────────────┘
```

Thiết kế:
- Modal overlay: bg-black/50, z-50
- Modal body: bg-white, rounded-2xl, max-w-2xl, mx-auto, p-6
- Reuse ReasonsList + FeatureWaterfall từ WP4
- Loading state khi gọi `/api/explain`: spinner + "Loading explanation..."
- Close: X button top-right + click overlay + Escape key

**5.6 — Navigation guard**

- `onBeforeRouteLeave()`: nếu có batch results chưa export → confirm dialog "Unsaved results will be lost. Leave anyway?"
- `beforeunload` event: same warning khi close tab

### Checkpoints

**CsvUploader:**
- [ ] Drag CSV file vào drop zone → file accepted, preview row count
- [ ] Click drop zone → file browser opens
- [ ] File không phải .csv → error "Only CSV files accepted"
- [ ] File > 5MB → error "File too large"
- [ ] CSV không có column "url" → error "CSV must contain 'url' column"
- [ ] Remove button → clear file selection
- [ ] "Scan All" disabled khi chưa có file hoặc file invalid

**Scanning:**
- [ ] Click "Scan All" → progress bar xuất hiện
- [ ] Scan complete → progress bar hide, results show
- [ ] API error → toast error, progress bar hide

**Summary Cards:**
- [ ] Total, Phishing count, Legitimate count hiển thị đúng
- [ ] Pie chart hiển thị 4 risk levels đúng colors
- [ ] Pie chart hover → tooltip với count + percentage

**Results Table:**
- [ ] Sort by Score (click header) → desc/asc toggle
- [ ] Filter "Phishing only" → chỉ hiện phishing rows
- [ ] Search "xyz" → chỉ hiện URLs chứa "xyz"
- [ ] Pagination: 20 rows/page, navigate pages đúng
- [ ] Detail button → ExplainModal opens

**ExplainModal:**
- [ ] Click Detail → modal opens, loading spinner
- [ ] API response → ReasonsList + FeatureWaterfall render
- [ ] Close: X button, click overlay, Escape key
- [ ] Scroll lock khi modal open

**Export:**
- [ ] Export CSV → file download, data đúng
- [ ] Export JSON → file download, data đúng
- [ ] Exported file chứa tất cả results (không chỉ current page)

**Navigation guard:**
- [ ] Có results + navigate away → confirm dialog
- [ ] Confirm "Leave" → navigate, results lost
- [ ] Confirm "Stay" → stay on page
- [ ] Sau export → navigate away không warning
- [ ] Close tab → browser warning

---

## WP6: DashboardView — Model Info

### Mục tiêu
Hiển thị model metadata, performance metrics, data sources, global SHAP.

### Deliverables & Design

**6.1 — Full page layout**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌─── Model Information ─────┐  ┌─── Performance ──────────┐ │
│   │                           │  │                           │ │
│   │  Model      LightGBM     │  │  F1-Score    0.9849       │ │
│   │  Version    lgbm_2026... │  │  Precision   0.9908       │ │
│   │  Features   37 (Final)   │  │  Recall      0.9791       │ │
│   │  Calibr.    Isotonic     │  │  ROC-AUC     0.9971       │ │
│   │  Threshold  0.515        │  │  PR-AUC      0.9973       │ │
│   │  Strategy   Deploy A1    │  │                           │ │
│   │                           │  │                           │ │
│   └───────────────────────────┘  └───────────────────────────┘ │
│                                                                 │
│   ┌─── Training Data Sources ──────────────────────────────┐   │
│   │                                                        │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐              │   │
│   │  │ PhiUSIIL │ │PhishTank │ │ Tranco   │              │   │
│   │  │  ~195k   │ │  ~55k    │ │  ~9k     │              │   │
│   │  │ URLs     │ │ URLs     │ │ domains  │              │   │
│   │  └──────────┘ └──────────┘ └──────────┘              │   │
│   │                                                        │   │
│   │  [STACKED BAR showing phishing/legitimate per source]  │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─── Global Feature Importance (SHAP) ───────────────────┐  │
│   │                                                         │  │
│   │  domain_length          ████████████████████████  2.28  │  │
│   │  path_length            ███████████████████████   2.21  │  │
│   │  registered_domain_len  ███████████████          1.55   │  │
│   │  special_char_ratio     ████████████             1.38   │  │
│   │  num_digits             ████████                 0.94   │  │
│   │  url_length             █████                    0.46   │  │
│   │  subdomain_count        █████                    0.45   │  │
│   │  path_entropy           ████                     0.44   │  │
│   │  domain_entropy         ████                     0.42   │  │
│   │  num_hyphens            ████                     0.36   │  │
│   │                                                         │  │
│   │  Showing top 10 of 37        [Show All Features]        │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**6.2 — ModelCard.vue**

Thiết kế:
- Rounded-xl, shadow-sm, p-6
- Key-value pairs: label text-sm text-gray-500 + value text-base font-medium
- 6 rows: Model, Version, Features, Calibration, Threshold, Deploy Strategy
- Data từ `GET /api/model-info`

**6.3 — MetricsCard.vue**

Thiết kế:
- Rounded-xl, shadow-sm, p-6
- 5 metrics: F1, Precision, Recall, ROC-AUC, PR-AUC
- Mỗi metric: large number (text-2xl font-bold), label dưới
- Color: tất cả green vì metrics đều > 0.97
- Optional: circular progress ring cho mỗi metric (ECharts gauge nhỏ)

**6.4 — DataSourcesCard.vue**

Thiết kế:
- 3 source cards inline: PhiUSIIL, PhishTank, Tranco
- Mỗi card: icon, name, URL count, brief description
- Stacked bar chart bên dưới: phishing (red) vs legitimate (green) per source
- ECharts stacked bar, horizontal

**6.5 — FeatureImportance.vue**

Thiết kế:
- ECharts horizontal bar chart
- Bars: gradient blue (single color, not red/blue like waterfall)
- Y axis: feature names
- X axis: mean |SHAP| value
- Default: show top 10
- "Show All Features" button → expand to all 37
- Each bar labeled with importance value
- Height: auto (scales with number of features shown)

### Checkpoints

- [ ] Page load → gọi `GET /api/model-info` → data populate
- [ ] ModelCard: hiển thị 6 fields đúng
- [ ] MetricsCard: 5 metrics hiển thị đúng giá trị, formatted 4 decimal places
- [ ] DataSourcesCard: 3 source cards + stacked bar chart render
- [ ] FeatureImportance: top 10 features hiển thị, bars sorted desc
- [ ] "Show All Features" → expand to 37 features
- [ ] Click "Show All" lần nữa → collapse về 10
- [ ] Loading state: skeleton placeholders khi API chưa trả về
- [ ] Error state: toast nếu API fail, retry button
- [ ] Responsive: 2-column → 1-column trên mobile

---

## WP7: AboutView

### Mục tiêu
Project info, methodology, disclaimers, privacy statement.

### Deliverables & Design

**7.1 — Page layout**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   About This System                                             │
│                                                                 │
│   ─── Overview ──────────────────────────────────────────────── │
│   Phishing URL Detection with Explainable Machine Learning      │
│   is a web-based system that analyzes URL structure to detect   │
│   potential phishing websites. The system uses a tuned          │
│   LightGBM model trained on multi-source data and provides     │
│   SHAP-based explanations for every prediction.                 │
│                                                                 │
│   ─── How It Works ──────────────────────────────────────────── │
│                                                                 │
│   [1. Input]  →  [2. Analysis]  →  [3. Result]                 │
│   User enters     37 features       Risk score +                │
│   a URL           extracted         explanation                 │
│                   from URL          displayed                   │
│                                                                 │
│   ─── Methodology ───────────────────────────────────────────── │
│   • Multi-source training data (PhiUSIIL + PhishTank + Tranco) │
│   • LightGBM with Optuna hyperparameter tuning                 │
│   • Isotonic probability calibration                            │
│   • SHAP TreeExplainer for explainability                       │
│                                                                 │
│   ─── Important Disclaimers ─────────────────────────────────── │
│                                                                 │
│   ⚠ Risk Scores                                                │
│   Risk scores represent calibrated model outputs and should     │
│   be interpreted as decision-support signals, not absolute      │
│   guarantees. Model accuracy varies with URL types.             │
│                                                                 │
│   ⚠ Known Limitations                                          │
│   The model analyzes URL structure only. It cannot detect       │
│   phishing hosted on compromised legitimate websites with       │
│   clean URL patterns. For comprehensive protection, combine     │
│   with content analysis, WHOIS lookup, and threat intelligence. │
│                                                                 │
│   ─── Privacy ───────────────────────────────────────────────── │
│   • Scan history is stored locally in your browser              │
│   • It is never sent to or persisted by the server              │
│     beyond the inference request                                │
│   • You can clear your history anytime from the Scan page       │
│                                                                 │
│   ─── Project ───────────────────────────────────────────────── │
│   Graduation project — [University name]                        │
│   Built with: FastAPI · Vue 3 · LightGBM · SHAP                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Thiết kế:
- Content: prose, max-w-3xl mx-auto
- Sections: h2 headers, dividers
- "How it works": 3-step horizontal flow diagram (có thể dùng simple flexbox + icons thay vì ECharts)
- Disclaimers: bg-amber-50 border-l-4 border-amber-400 p-4 (callout style)
- Privacy: bg-blue-50 border-l-4 border-blue-400 p-4
- Static content, không cần API call

### Checkpoints

- [ ] Page render đúng tất cả sections
- [ ] Disclaimers nổi bật (callout style, không dễ bỏ qua)
- [ ] Privacy statement rõ ràng
- [ ] "How it works" diagram hiển thị 3 steps
- [ ] Không có API call trên trang này
- [ ] Text readable, line-height comfortable (leading-relaxed)
- [ ] Responsive: content readable trên mobile

---

## WP8: Polish & Integration

### Mục tiêu
Cross-cutting concerns, UX polish, production build verification.

### Deliverables

**8.1 — Loading & Error states consistency**
- Tất cả pages: skeleton loading khi fetch API
- Toast notifications: consistent position (top-right), auto-dismiss 4s
- 503 error: banner "Service Unavailable" trên header hoặc full-page
- Network offline: detect `navigator.onLine`, show offline banner

**8.2 — Responsive verification**
- Tất cả pages test trên viewport 375px (mobile), 768px (tablet), 1280px (desktop)
- Touch targets ≥ 44px trên mobile
- No horizontal overflow

**8.3 — Accessibility basics**
- Tất cả buttons có aria-label
- Form inputs có associated labels
- Color contrast ratio ≥ 4.5:1 cho text
- Focus visible trên tất cả interactive elements
- Modal: focus trap, Escape to close

**8.4 — Performance**
- `npm run build` → check bundle size
- Lazy load routes: `() => import('./views/BatchView.vue')`
- ECharts tree-shaking: import chỉ components cần dùng

**8.5 — Production build test**
- `npm run build` thành công
- Preview: `npm run preview` → app hoạt động đúng
- All routes work với SPA fallback (try_files)

### Checkpoints

**Loading & Error:**
- [ ] Mỗi page có loading skeleton khi fetch API
- [ ] Toast position consistent (top-right)
- [ ] Toast auto-dismiss sau 4s
- [ ] Disconnect backend → toast "Cannot connect" trên mọi page
- [ ] Reconnect → toast clear, app hoạt động lại

**Responsive:**
- [ ] ScanView usable trên 375px viewport
- [ ] BatchView table horizontally scrollable trên mobile
- [ ] DashboardView cards stack trên mobile
- [ ] Header navigation hamburger trên mobile
- [ ] Không có horizontal overflow trên bất kỳ page nào

**Accessibility:**
- [ ] Tab navigation qua tất cả interactive elements
- [ ] Focus ring visible
- [ ] Screen reader: buttons có aria-label
- [ ] Modal: Escape to close, focus trapped inside

**Performance:**
- [ ] `npm run build` < 30s
- [ ] Bundle size < 500KB gzipped (excl. ECharts)
- [ ] First contentful paint < 2s
- [ ] Route lazy loading hoạt động (check Network tab)

**Production:**
- [ ] `npm run build` → `dist/` generated
- [ ] `npm run preview` → app hoạt động
- [ ] Navigate trực tiếp đến `/batch` → page renders (SPA fallback)
- [ ] All API calls work qua Vite proxy

---

## Thứ tự thực hiện khuyến nghị

```
Ngày 1:  WP1 (scaffolding) + WP2 (layout) + WP3 (API client + store)
         → App shell chạy, navigation, API connected, toast works

Ngày 2:  WP4 phần 1 — UrlInput + RiskGauge + PredictionBadge + RiskBadge
         → Scan flow hoạt động, result card hiển thị score/prediction

Ngày 3:  WP4 phần 2 — ReasonsList + FeatureWaterfall + RecentScans
         → ScanView hoàn chỉnh, SHAP waterfall render, history works

Ngày 4:  WP5 phần 1 — CsvUploader + BatchResultsTable + Summary
         → Batch upload + results display hoạt động

Ngày 5:  WP5 phần 2 — ExplainModal + Export + Navigation guard
         → BatchView hoàn chỉnh

Ngày 6:  WP6 (Dashboard) + WP7 (About)
         → Tất cả pages done

Ngày 7:  WP8 (Polish)
         → Responsive, accessibility, performance, production build
```

Core path: WP1→WP2→WP3→WP4 — sau khi WP4 done, app đã usable cho demo.
WP5-WP7 mở rộng features. WP8 polish cuối cùng.

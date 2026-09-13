<template>
  <div class="space-y-6">
    <!-- Upload -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
      <div
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop.prevent="handleDrop"
        @click="$refs.fileInput.click()"
        class="border-2 border-dashed rounded-xl h-44 flex flex-col items-center justify-center cursor-pointer transition"
        :class="dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'"
      >
        <FolderUp class="w-10 h-10 text-gray-400 mb-2" />
        <p class="text-sm text-gray-600 font-medium">Drop CSV file here or click to browse</p>
        <p class="text-xs text-gray-400 mt-1">Max 1,000 URLs · .csv only · max 5MB</p>
      </div>
      <input ref="fileInput" type="file" accept=".csv" class="hidden" @change="handleFileSelect" />

      <div v-if="fileName" class="mt-3 flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2">
        <span class="text-sm text-gray-700">{{ fileName }} ({{ urlCount }} URLs detected)</span>
        <button @click="clearFile" class="text-xs text-red-500 hover:underline">Remove</button>
      </div>

      <div class="mt-4 flex justify-end">
        <button
          @click="handleBatchScan"
          :disabled="!csvFile || scanning"
          class="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
        >
          <Loader2 v-if="scanning" class="w-4 h-4 animate-spin" />
          {{ scanning ? 'Scanning...' : 'Scan All URLs' }}
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div v-if="batchResult" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border p-4 text-center">
        <p class="text-3xl font-bold text-gray-900">{{ batchResult.total }}</p>
        <p class="text-sm text-gray-500">Total</p>
      </div>
      <div class="bg-white rounded-xl border p-4 text-center">
        <p class="text-3xl font-bold text-red-600">{{ batchResult.phishing }}</p>
        <p class="text-sm text-gray-500">Phishing</p>
      </div>
      <div class="bg-white rounded-xl border p-4 text-center">
        <p class="text-3xl font-bold text-green-600">{{ batchResult.legitimate }}</p>
        <p class="text-sm text-gray-500">Legitimate</p>
      </div>
      <div class="bg-white rounded-xl border p-4 text-center">
        <p class="text-2xl font-bold text-gray-700">{{ formatMs(batchResult.summary.total_time_ms) }}</p>
        <p class="text-sm text-gray-500">Total Time</p>
      </div>
    </div>

    <!-- Results Table -->
    <div v-if="batchResult" class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div class="px-5 py-3 border-b border-gray-100 flex flex-wrap items-center gap-3">
        <select v-model="filter" class="text-sm border rounded-lg px-3 py-1.5">
          <option value="all">All</option>
          <option value="phishing">Phishing only</option>
          <option value="legitimate">Legitimate only</option>
        </select>
        <input v-model="search" placeholder="Search URL..." class="text-sm border rounded-lg px-3 py-1.5 flex-1 min-w-[150px]" />
        <div class="flex gap-2 ml-auto">
          <button @click="exportCSV" class="text-xs border rounded-lg px-3 py-1.5 hover:bg-gray-50">Export CSV</button>
          <button @click="exportJSON" class="text-xs border rounded-lg px-3 py-1.5 hover:bg-gray-50">Export JSON</button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="text-xs text-gray-500 uppercase tracking-wider bg-gray-50">
            <tr>
              <th class="px-5 py-2 text-left">#</th>
              <th class="px-3 py-2 text-left cursor-pointer hover:text-gray-700" @click="toggleSort">
                URL <span v-if="sortField === 'url'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th class="px-3 py-2 text-right cursor-pointer hover:text-gray-700" @click="sortByScore">
                Score <span v-if="sortField === 'score'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th class="px-3 py-2 text-center">Level</th>
              <th class="px-3 py-2 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in paginatedResults" :key="i" class="border-t border-gray-50 hover:bg-gray-50">
              <td class="px-5 py-2 text-gray-400">{{ (currentPage - 1) * pageSize + i + 1 }}</td>
              <td class="px-3 py-2 font-mono text-xs truncate max-w-[300px]" :title="r.url">{{ truncateUrl(r.url, 60) }}</td>
              <td class="px-3 py-2 text-right font-semibold" :style="{ color: getRiskColor(r.risk_level).text }">
                {{ formatPercent(r.risk_score) }}
              </td>
              <td class="px-3 py-2 text-center"><RiskBadge :level="r.risk_level" /></td>
              <td class="px-3 py-2 text-center">
                <button @click="showDetail(r.url)" class="text-blue-600 hover:underline text-xs">Detail</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
        <span>Showing {{ (currentPage-1)*pageSize+1 }}–{{ Math.min(currentPage*pageSize, filteredResults.length) }} of {{ filteredResults.length }}</span>
        <div class="flex gap-1">
          <button @click="currentPage--" :disabled="currentPage <= 1" class="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-30">←</button>
          <button @click="currentPage++" :disabled="currentPage >= totalPages" class="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-30">→</button>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <Teleport to="body">
      <div v-if="detailModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="detailModal = null">
        <div class="bg-white rounded-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto p-6 space-y-4">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold">URL Explanation</h2>
            <button @click="detailModal = null" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
          </div>

          <div v-if="detailLoading" class="py-12 text-center text-gray-400">
            <Loader2 class="w-6 h-6 animate-spin mx-auto mb-2" /> Loading explanation...
          </div>

          <template v-else-if="detailData">
            <p class="text-sm font-mono text-gray-600 break-all">{{ detailData.url }}</p>
            <div class="flex items-center gap-3">
              <PredictionBadge :prediction="detailData.prediction" />
              <span class="text-sm text-gray-600">Risk Score: <b>{{ formatPercent(detailData.risk_score) }}</b></span>
              <RiskBadge :level="detailData.risk_level" />
            </div>
            <hr class="border-gray-100" />
            <ReasonsList :reasons="detailData.explanation?.reasons || []" :prediction="detailData.prediction" />
            <FeatureWaterfall v-if="detailData.explanation?.top_features" :top-features="detailData.explanation.top_features" />
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { FolderUp, Loader2, X } from 'lucide-vue-next'
import { scanBatch, explainUrl } from '../api/client'
import { formatPercent, truncateUrl, formatMs } from '../utils/formatters'
import { getRiskColor } from '../utils/riskColors'

import RiskBadge from '../components/scan/RiskBadge.vue'
import PredictionBadge from '../components/scan/PredictionBadge.vue'
import ReasonsList from '../components/scan/ReasonsList.vue'
import FeatureWaterfall from '../components/scan/FeatureWaterfall.vue'

const dragOver = ref(false)
const csvFile = ref(null)
const fileName = ref('')
const urlCount = ref(0)
const scanning = ref(false)
const batchResult = ref(null)
const filter = ref('all')
const search = ref('')
const sortField = ref('score')
const sortDir = ref('desc')
const currentPage = ref(1)
const pageSize = 20
const exported = ref(false)
const detailModal = ref(null)
const detailLoading = ref(false)
const detailData = ref(null)

function handleFileSelect(e) { processFile(e.target.files[0]) }
function handleDrop(e) { dragOver.value = false; processFile(e.dataTransfer.files[0]) }

function processFile(file) {
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) return alert('Only CSV files accepted')
  if (file.size > 5 * 1024 * 1024) return alert('File exceeds 5MB limit')
  csvFile.value = file
  fileName.value = file.name
  // Quick row count
  const reader = new FileReader()
  reader.onload = (e) => {
    const lines = e.target.result.split('\n').filter(l => l.trim())
    urlCount.value = Math.max(0, lines.length - 1)  // minus header
  }
  reader.readAsText(file)
}

function clearFile() { csvFile.value = null; fileName.value = ''; urlCount.value = 0 }

async function handleBatchScan() {
  scanning.value = true; exported.value = false; batchResult.value = null
  const formData = new FormData()
  formData.append('file', csvFile.value)
  try {
    const { data } = await scanBatch(formData)
    batchResult.value = data
    currentPage.value = 1
  } catch (err) {
    alert(err.response?.data?.detail || 'Batch scan failed')
  } finally { scanning.value = false }
}

const filteredResults = computed(() => {
  if (!batchResult.value) return []
  let items = batchResult.value.results
  if (filter.value !== 'all') items = items.filter(r => r.prediction === filter.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    items = items.filter(r => r.url.toLowerCase().includes(q))
  }
  items = [...items].sort((a, b) => {
    if (sortField.value === 'score') return sortDir.value === 'desc' ? b.risk_score - a.risk_score : a.risk_score - b.risk_score
    return sortDir.value === 'desc' ? b.url.localeCompare(a.url) : a.url.localeCompare(b.url)
  })
  return items
})

const totalPages = computed(() => Math.ceil(filteredResults.value.length / pageSize))
const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredResults.value.slice(start, start + pageSize)
})

function toggleSort() { sortField.value = 'url'; sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc' }
function sortByScore() { sortField.value = 'score'; sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc' }

function exportCSV() {
  const header = 'url,prediction,risk_score,risk_level\n'
  const rows = batchResult.value.results.map(r => `"${r.url}",${r.prediction},${r.risk_score},${r.risk_level}`).join('\n')
  downloadFile(header + rows, 'scan_results.csv', 'text/csv')
  exported.value = true
}
function exportJSON() {
  downloadFile(JSON.stringify(batchResult.value, null, 2), 'scan_results.json', 'application/json')
  exported.value = true
}
function downloadFile(content, name, type) {
  const blob = new Blob([content], { type })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click()
}

async function showDetail(url) {
  detailModal.value = url; detailLoading.value = true; detailData.value = null
  try {
    const { data } = await explainUrl(url)
    detailData.value = data
  } catch { detailData.value = null }
  finally { detailLoading.value = false }
}

// Navigation guard
onBeforeRouteLeave((to, from, next) => {
  if (batchResult.value && !exported.value) {
    const leave = confirm('Unsaved results will be lost. Leave anyway?')
    next(leave)
  } else next()
})

const beforeUnload = (e) => {
  if (batchResult.value && !exported.value) { e.preventDefault(); e.returnValue = '' }
}
window.addEventListener('beforeunload', beforeUnload)
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
</script>

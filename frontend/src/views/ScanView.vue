<template>
  <div class="space-y-6">
    <!-- URL Input -->
    <UrlInput ref="urlInputRef" :loading="loading" @scan="handleScan" />

    <!-- Result Card -->
    <transition name="fade-slide">
      <div v-if="result" class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">
        <!-- Top: Gauge + Metadata -->
        <div class="flex flex-col md:flex-row items-center gap-6">
          <RiskGauge :score="result.risk_score" :threshold="result.threshold" />
          <div class="space-y-2 text-center md:text-left">
            <PredictionBadge :prediction="result.prediction" />
            <div class="space-y-1 text-sm text-gray-600 mt-3">
              <p>Risk Score: <span class="font-semibold text-gray-900">{{ formatPercent(result.risk_score) }}</span></p>
              <p>Risk Level: <RiskBadge :level="result.risk_level" /></p>
              <p>Threshold: {{ formatPercent(result.threshold) }}</p>
            </div>
          </div>
        </div>

        <hr class="border-gray-100" />

        <!-- Reasons -->
        <ReasonsList
          :reasons="result.explanation?.reasons || []"
          :prediction="result.prediction"
        />

        <hr v-if="result.explanation?.top_features?.length" class="border-gray-100" />

        <!-- SHAP Waterfall -->
        <FeatureWaterfall
          v-if="result.explanation?.top_features?.length"
          :top-features="result.explanation.top_features"
        />
      </div>
    </transition>

    <!-- Error from API -->
    <div v-if="apiError" class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
      {{ apiError }}
    </div>

    <!-- Recent Scans -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-700">Recent Scans</h2>
        <button
          v-if="history.recentScans.length > 0"
          @click="history.clearHistory()"
          class="text-xs text-red-500 hover:underline"
        >
          Clear History
        </button>
      </div>

      <div v-if="history.recentScans.length === 0" class="px-5 py-8 text-center text-sm text-gray-400 italic">
        No recent scans
      </div>

      <table v-else class="w-full text-sm">
        <thead class="text-xs text-gray-500 uppercase tracking-wider bg-gray-50">
          <tr>
            <th class="px-5 py-2 text-left">URL</th>
            <th class="px-3 py-2 text-right">Score</th>
            <th class="px-3 py-2 text-center">Prediction</th>
            <th class="px-3 py-2 text-right hidden sm:table-cell">Time</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(scan, i) in history.recentScans" :key="i"
            class="border-t border-gray-50 hover:bg-gray-50 cursor-pointer transition"
            @click="rescan(scan.url)"
          >
            <td class="px-5 py-2.5 font-mono text-xs text-gray-700 truncate max-w-[280px]">
              {{ truncateUrl(scan.url) }}
            </td>
            <td class="px-3 py-2.5 text-right font-semibold"
                :style="{ color: getRiskColor(scan.risk_level).text }">
              {{ formatPercent(scan.risk_score) }}
            </td>
            <td class="px-3 py-2.5 text-center">
              <PredictionBadge :prediction="scan.prediction" />
            </td>
            <td class="px-3 py-2.5 text-right text-gray-400 hidden sm:table-cell">
              {{ formatTimeAgo(scan.scanned_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { scanUrl } from '../api/client'
import { useScanHistory } from '../stores/scanHistory'
import { formatPercent, formatTimeAgo, truncateUrl } from '../utils/formatters'
import { getRiskColor } from '../utils/riskColors'

import UrlInput from '../components/scan/UrlInput.vue'
import RiskGauge from '../components/scan/RiskGauge.vue'
import PredictionBadge from '../components/scan/PredictionBadge.vue'
import RiskBadge from '../components/scan/RiskBadge.vue'
import ReasonsList from '../components/scan/ReasonsList.vue'
import FeatureWaterfall from '../components/scan/FeatureWaterfall.vue'

const history = useScanHistory()
const urlInputRef = ref(null)
const loading = ref(false)
const result = ref(null)
const apiError = ref('')

async function handleScan(url) {
  loading.value = true
  apiError.value = ''
  result.value = null

  try {
    const { data } = await scanUrl(url)
    result.value = data
    history.addScan(data)
  } catch (err) {
    if (err.response?.status === 422) {
      apiError.value = err.response.data?.detail || 'Invalid URL'
    } else if (!err.response) {
      apiError.value = 'Cannot connect to server'
    } else {
      apiError.value = 'An error occurred'
    }
  } finally {
    loading.value = false
  }
}

function rescan(url) {
  urlInputRef.value?.setUrl(url)
  handleScan(url)
}
</script>

<style scoped>
.fade-slide-enter-active { transition: all 0.3s ease-out; }
.fade-slide-enter-from { opacity: 0; transform: translateY(12px); }
</style>

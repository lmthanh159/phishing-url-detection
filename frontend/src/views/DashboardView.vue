<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Model Dashboard</h1>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-400">Loading model information...</div>

    <template v-else-if="info">
      <!-- Model + Metrics cards -->
      <div class="grid md:grid-cols-2 gap-4">
        <!-- Model Info -->
        <div class="bg-white rounded-xl border p-6 space-y-3">
          <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Model Information</h2>
          <dl class="space-y-2 text-sm">
            <div class="flex justify-between"><dt class="text-gray-500">Model</dt><dd class="font-medium">{{ info.model_name }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Version</dt><dd class="font-mono text-xs">{{ info.model_version }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Features</dt><dd class="font-medium">{{ info.n_features }} ({{ info.feature_set }})</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Calibration</dt><dd class="font-medium">{{ info.calibration_method }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Threshold</dt><dd class="font-medium">{{ info.threshold }}</dd></div>
          </dl>
        </div>

        <!-- Metrics -->
        <div class="bg-white rounded-xl border p-6 space-y-3">
          <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Performance</h2>
          <div class="grid grid-cols-2 gap-4" v-if="info.final_test_metrics">
            <div v-for="(val, key) in info.final_test_metrics" :key="key" class="text-center">
              <p class="text-2xl font-bold text-green-700">{{ typeof val === 'number' ? val.toFixed(4) : val }}</p>
              <p class="text-xs text-gray-500 uppercase">{{ key.replace(/_/g, ' ') }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Data Sources -->
      <div class="bg-white rounded-xl border p-6">
        <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Training Data Sources</h2>
        <div class="flex flex-wrap gap-3">
          <div v-for="src in info.data_sources" :key="src"
               class="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
            {{ src }}
          </div>
        </div>
      </div>

      <!-- Global Feature Importance -->
      <div class="bg-white rounded-xl border p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            Global Feature Importance (SHAP)
          </h2>
          <button @click="showAll = !showAll" class="text-xs text-blue-600 hover:underline">
            {{ showAll ? 'Show Top 10' : `Show All ${importance.length}` }}
          </button>
        </div>
        <div :style="{ height: chartHeight }">
          <v-chart :option="importanceChart" autoresize />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getModelInfo } from '../api/client'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const loading = ref(true)
const info = ref(null)
const showAll = ref(false)

onMounted(async () => {
  try {
    const { data } = await getModelInfo()
    info.value = data
  } catch { /* toast handled by interceptor */ }
  finally { loading.value = false }
})

const importance = computed(() => info.value?.global_feature_importance || [])
const displayedFeatures = computed(() => showAll.value ? importance.value : importance.value.slice(0, 10))
const chartHeight = computed(() => `${Math.max(200, displayedFeatures.value.length * 28 + 40)}px`)

const importanceChart = computed(() => {
  const features = [...displayedFeatures.value].reverse()
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '40%', right: '10%', top: '5%', bottom: '5%' },
    xAxis: {
      type: 'value',
      axisLabel: { fontSize: 11 },
      name: 'Mean |SHAP|',
      nameLocation: 'center',
      nameGap: 30,
    },
    yAxis: {
      type: 'category',
      data: features.map(f => (f.feature || '').replace(/_/g, ' ')),
      axisLabel: { fontSize: 11, color: '#475569' },
    },
    series: [{
      type: 'bar',
      data: features.map(f => ({
        value: f.mean_abs_shap,
        itemStyle: {
          color: '#3B82F6',
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barWidth: '65%',
      label: {
        show: true,
        position: 'right',
        formatter: (p) => p.value.toFixed(2),
        fontSize: 10,
        color: '#64748b',
      },
    }],
  }
})
</script>

<template>
  <div>
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Feature Impact</h3>
    <div class="h-64">
      <v-chart :option="chartOption" autoresize />
    </div>
    <p class="mt-2 text-xs text-gray-400 italic">
      SHAP values explain the underlying model decision before probability calibration.
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  topFeatures: { type: Array, default: () => [] },
})

const chartOption = computed(() => {
  const features = [...props.topFeatures].reverse()
  const names = features.map(f => f.feature.replace(/_/g, ' '))
  const values = features.map(f => f.shap_value)
  const colors = features.map(f => f.shap_value > 0 ? '#EF4444' : '#3B82F6')

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const dir = p.value > 0 ? '↑ Increases risk' : '↓ Decreases risk'
        return `${p.name}<br/>SHAP: ${p.value > 0 ? '+' : ''}${p.value.toFixed(4)}<br/>${dir}`
      },
    },
    grid: { left: '35%', right: '10%', top: '5%', bottom: '10%' },
    xAxis: {
      type: 'value',
      axisLabel: { fontSize: 11 },
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { fontSize: 11, color: '#475569' },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({
        value: v,
        itemStyle: { color: colors[i], borderRadius: v > 0 ? [0, 4, 4, 0] : [4, 0, 0, 4] },
      })),
      barWidth: '60%',
      label: {
        show: true,
        position: 'right',
        formatter: (p) => (p.value > 0 ? '+' : '') + p.value.toFixed(2),
        fontSize: 10,
        color: '#64748b',
      },
    }],
  }
})
</script>

<template>
  <div>
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Feature Impact</h3>
    <div :style="{ height: chartHeight }">
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
  waterfallData: { type: Object, default: null },
})

const featureRows = computed(() => {
  if (props.waterfallData?.features?.length && props.waterfallData?.values?.length) {
    return props.waterfallData.features.map((feature, index) => ({
      feature,
      shap_value: Number(props.waterfallData.values[index] || 0),
      cumulative: props.waterfallData.cumulative?.[index + 1],
    }))
  }

  return props.topFeatures.map(feature => ({
    feature: feature.feature,
    shap_value: Number(feature.shap_value || 0),
    cumulative: null,
  }))
})

const chartHeight = computed(() => {
  const count = Math.max(featureRows.value.length, 1)
  return `${Math.min(Math.max(count * 26 + 56, 260), 920)}px`
})

const chartOption = computed(() => {
  const features = [...featureRows.value].reverse()
  const names = features.map(f => f.feature.replace(/_/g, ' '))
  const values = features.map(f => f.shap_value)
  const colors = features.map(f => f.shap_value > 0 ? '#EF4444' : '#3B82F6')

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const row = features[p.dataIndex]
        const dir = p.value > 0 ? 'Increases risk' : 'Decreases risk'
        const cumulative = Number.isFinite(row?.cumulative)
          ? `<br/>Cumulative raw output: ${row.cumulative.toFixed(4)}`
          : ''
        return `${p.name}<br/>SHAP: ${p.value > 0 ? '+' : ''}${p.value.toFixed(4)}<br/>${dir}${cumulative}`
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

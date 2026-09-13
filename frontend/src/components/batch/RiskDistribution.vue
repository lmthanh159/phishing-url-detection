<template>
  <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Risk Distribution</h2>
      <span class="text-xs text-gray-400">{{ total }} URLs</span>
    </div>
    <div class="h-64">
      <v-chart :option="chartOption" autoresize />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getRiskColor } from '../../utils/riskColors'

use([PieChart, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  distribution: { type: Object, default: () => ({}) },
})

const rows = computed(() => (
  ['critical', 'high', 'medium', 'low']
    .map(level => ({ level, count: Number(props.distribution[level] || 0) }))
    .filter(row => row.count > 0)
))

const total = computed(() => rows.value.reduce((sum, row) => sum + row.count, 0))

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)',
  },
  legend: {
    bottom: 0,
    textStyle: { color: '#475569', fontSize: 12 },
  },
  series: [{
    type: 'pie',
    radius: ['45%', '70%'],
    center: ['50%', '42%'],
    avoidLabelOverlap: true,
    label: {
      formatter: '{b}\n{c}',
      color: '#475569',
      fontSize: 11,
    },
    data: rows.value.map(row => ({
      name: getRiskColor(row.level).label,
      value: row.count,
      itemStyle: { color: getRiskColor(row.level).bg },
    })),
  }],
}))
</script>

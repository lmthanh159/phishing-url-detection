<template>
  <div class="w-52 h-40">
    <v-chart :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GaugeChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { formatPercent } from '../../utils/formatters'

use([GaugeChart, CanvasRenderer])

const props = defineProps({
  score: { type: Number, required: true },
  threshold: { type: Number, default: null },
})

const chartOption = computed(() => {
  const series = [
    {
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      radius: '100%',
      center: ['50%', '85%'],
      axisLine: {
        lineStyle: {
          width: 20,
          color: [
            [0.30, '#10B981'],
            [0.60, '#F59E0B'],
            [0.85, '#F97316'],
            [1, '#EF4444'],
          ],
        },
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: {
        length: '60%',
        width: 4,
        itemStyle: { color: '#334155' },
      },
      detail: {
        formatter: formatPercent(props.score),
        fontSize: 22,
        fontWeight: 'bold',
        color: '#0f172a',
        offsetCenter: [0, '-15%'],
      },
      data: [{ value: props.score * 100 }],
      markLine: {},
      title: { show: false },
    },
  ]

  if (typeof props.threshold === 'number') {
    series.push({
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      radius: '100%',
      center: ['50%', '85%'],
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: {
        length: '70%',
        width: 2,
        itemStyle: { color: '#94a3b8' },
      },
      detail: {
        formatter: 'Threshold',
        fontSize: 10,
        color: '#94a3b8',
        offsetCenter: [0, '20%'],
      },
      data: [{ value: props.threshold * 100 }],
      title: { show: false },
    })
  }

  return { series }
})
</script>

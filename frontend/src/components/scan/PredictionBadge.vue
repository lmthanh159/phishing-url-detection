<template>
  <span
    class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold uppercase"
    :style="{ backgroundColor: color.bgLight, color: color.text }"
  >
    <ShieldAlert v-if="prediction === 'phishing'" class="w-4 h-4" />
    <ShieldCheck v-else class="w-4 h-4" />
    {{ prediction === 'phishing' ? 'Phishing' : 'Legitimate' }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { ShieldAlert, ShieldCheck } from 'lucide-vue-next'
import { getPredictionColor } from '../../utils/riskColors'

const props = defineProps({ prediction: { type: String, required: true } })
const color = computed(() => getPredictionColor(props.prediction))
</script>

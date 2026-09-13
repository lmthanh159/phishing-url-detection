<template>
  <span
    class="inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide"
    :style="{ backgroundColor: color.bgLight, color: color.text }"
  >
    {{ color.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getRiskColor } from '../../utils/riskColors'

const props = defineProps({ level: { type: String, required: true } })
const color = computed(() => getRiskColor(props.level))
</script>

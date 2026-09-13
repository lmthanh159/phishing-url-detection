<template>
  <div v-if="reasons.length > 0">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">
      {{ prediction === 'phishing'
        ? 'These factors contributed most to the model\'s phishing prediction:'
        : 'These factors indicate the URL appears safe:' }}
    </h3>
    <ul class="space-y-2">
      <li
        v-for="(reason, i) in reasons" :key="i"
        class="flex items-start gap-2 text-sm text-gray-600"
      >
        <AlertTriangle v-if="prediction === 'phishing'" class="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
        <CheckCircle v-else class="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
        <span>{{ reason }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { AlertTriangle, CheckCircle } from 'lucide-vue-next'

defineProps({
  reasons: { type: Array, default: () => [] },
  prediction: { type: String, default: 'phishing' },
})
</script>

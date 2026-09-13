<template>
  <div>
    <div class="flex rounded-xl border border-gray-300 bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition">
      <div class="flex items-center pl-4 text-gray-400">
        <Search class="w-5 h-5" />
      </div>
      <input
        ref="inputRef"
        v-model="url"
        type="text"
        placeholder="Enter a URL to analyze..."
        class="flex-1 px-3 py-3 text-sm bg-transparent outline-none"
        :disabled="loading"
        @keydown.enter="handleScan"
      />
      <button
        @click="handleScan"
        :disabled="loading"
        class="px-5 py-3 bg-blue-600 text-white text-sm font-medium rounded-r-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
      >
        <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
        <span>{{ loading ? 'Analyzing...' : 'Scan' }}</span>
      </button>
    </div>
    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, Loader2 } from 'lucide-vue-next'

const emit = defineEmits(['scan'])
const props = defineProps({ loading: Boolean })

const url = ref('')
const error = ref('')
const inputRef = ref(null)

onMounted(() => inputRef.value?.focus())

function handleScan() {
  error.value = ''
  const trimmed = url.value.trim()
  if (!trimmed) {
    error.value = 'URL cannot be empty'
    return
  }
  if (trimmed.length > 8192) {
    error.value = 'URL is too long (max 8192 characters)'
    return
  }
  emit('scan', trimmed)
}

function setUrl(newUrl) {
  url.value = newUrl
}

defineExpose({ setUrl })
</script>

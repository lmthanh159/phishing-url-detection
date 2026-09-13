<template>
  <div class="min-h-screen flex flex-col bg-slate-50">
    <AppHeader />
    <main class="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
      <router-view />
    </main>
    <AppFooter />
  </div>
</template>

<script setup>
import AppHeader from './components/layout/AppHeader.vue'
import AppFooter from './components/layout/AppFooter.vue'
</script>

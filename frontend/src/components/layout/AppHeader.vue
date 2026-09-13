<template>
  <header class="sticky top-0 z-50 bg-white border-b border-gray-200">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2 text-lg font-bold text-gray-900 hover:text-blue-600 transition">
        <ShieldCheck class="w-6 h-6 text-blue-600" />
        <span>PhishGuard</span>
      </router-link>

      <!-- Desktop nav -->
      <nav class="hidden md:flex items-center gap-1">
        <router-link
          v-for="link in navLinks" :key="link.to"
          :to="link.to"
          class="px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition"
        >
          <component :is="link.icon" class="w-4 h-4 inline mr-1.5 -mt-0.5" />
          {{ link.label }}
        </router-link>
      </nav>

      <!-- Mobile hamburger -->
      <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-lg hover:bg-gray-100" aria-label="Toggle menu">
        <Menu v-if="!mobileOpen" class="w-5 h-5" />
        <X v-else class="w-5 h-5" />
      </button>
    </div>

    <!-- Mobile menu -->
    <div v-if="mobileOpen" class="md:hidden border-t border-gray-100 bg-white px-4 pb-3">
      <router-link
        v-for="link in navLinks" :key="link.to"
        :to="link.to"
        class="flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-100"
        @click="mobileOpen = false"
      >
        <component :is="link.icon" class="w-4 h-4" />
        {{ link.label }}
      </router-link>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { ShieldCheck, Search, FolderUp, LayoutDashboard, Info, Menu, X } from 'lucide-vue-next'

const mobileOpen = ref(false)

const navLinks = [
  { to: '/', label: 'Scan', icon: Search },
  { to: '/batch', label: 'Batch', icon: FolderUp },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/about', label: 'About', icon: Info },
]
</script>

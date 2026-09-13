import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'scan',
    component: () => import('../views/ScanView.vue'),
  },
  {
    path: '/batch',
    name: 'batch',
    component: () => import('../views/BatchView.vue'),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'text-blue-600 font-semibold',
})

export default router

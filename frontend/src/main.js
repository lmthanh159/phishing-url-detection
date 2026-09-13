import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPersistedstate from 'pinia-plugin-persistedstate'
import Vue3Toastify from 'vue3-toastify'
import 'vue3-toastify/styles.css'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPersistedstate)
app.use(pinia)

app.use(router)

app.use(Vue3Toastify, {
  autoClose: 4000,
  position: 'top-right',
  theme: 'light',
})

app.mount('#app')

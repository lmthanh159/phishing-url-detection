import { defineStore } from 'pinia'

export const useScanHistory = defineStore('scanHistory', {
  state: () => ({
    recentScans: [],
    maxEntries: 20,
  }),
  actions: {
    addScan(result) {
      this.recentScans.unshift({
        url: result.url,
        risk_score: result.risk_score,
        model_score: result.model_score,
        prediction: result.prediction,
        risk_level: result.risk_level,
        scanned_at: new Date().toISOString(),
      })
      if (this.recentScans.length > this.maxEntries) {
        this.recentScans.pop()
      }
    },
    clearHistory() {
      this.recentScans = []
    },
  },
  persist: true,
})

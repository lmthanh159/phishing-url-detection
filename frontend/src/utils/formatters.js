export function formatPercent(value, decimals = 1) {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'N/A'
  const percent = value * 100
  if (percent > 0 && percent < 0.1) return '<0.1%'
  if (percent < 100 && percent > 99.9) return '>99.9%'
  return percent.toFixed(decimals) + '%'
}

export function displayScore(result) {
  if (!result) return 0
  return typeof result.model_score === 'number' ? result.model_score : result.risk_score
}

export function formatTimeAgo(isoString) {
  const seconds = Math.floor((Date.now() - new Date(isoString)) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function truncateUrl(url, maxLen = 55) {
  if (!url) return ''
  if (url.length <= maxLen) return url
  return url.substring(0, maxLen - 3) + '...'
}

export function formatMs(ms) {
  if (ms < 1) return '<1ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

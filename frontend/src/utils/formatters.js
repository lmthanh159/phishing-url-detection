export function formatPercent(value, decimals = 1) {
  return (value * 100).toFixed(decimals) + '%'
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

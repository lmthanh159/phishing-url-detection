export const RISK_COLORS = {
  low:      { bg: '#10B981', bgLight: '#ECFDF5', text: '#065F46', label: 'LOW' },
  medium:   { bg: '#F59E0B', bgLight: '#FFFBEB', text: '#92400E', label: 'MEDIUM' },
  high:     { bg: '#F97316', bgLight: '#FFF7ED', text: '#9A3412', label: 'HIGH' },
  critical: { bg: '#EF4444', bgLight: '#FEF2F2', text: '#991B1B', label: 'CRITICAL' },
}

export const PREDICTION_COLORS = {
  phishing:   { bg: '#EF4444', bgLight: '#FEF2F2', text: '#991B1B' },
  legitimate: { bg: '#10B981', bgLight: '#ECFDF5', text: '#065F46' },
}

export function getRiskColor(level) {
  return RISK_COLORS[level] || RISK_COLORS.low
}

export function getPredictionColor(prediction) {
  return PREDICTION_COLORS[prediction] || PREDICTION_COLORS.legitimate
}

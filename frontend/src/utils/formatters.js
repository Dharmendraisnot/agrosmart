/**
 * formatters.js — display formatting utilities.
 */

export const fmtFloat = (v, decimals = 1) =>
  v != null ? Number(v).toFixed(decimals) : '—'

export const fmtPct = (v) =>
  v != null ? `${Number(v).toFixed(1)}%` : '—'

export const fmtDate = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export const fmtConfidence = (v) =>
  v != null ? `${(Number(v) * 100).toFixed(1)}%` : '—'

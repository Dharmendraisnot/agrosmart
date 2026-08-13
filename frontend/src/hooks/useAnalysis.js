/**
 * useAnalysis.js — triggers POST /api/analysis/run and tracks loading state.
 */
import { useState } from 'react'
import { runAnalysis } from '../services/api'

export function useAnalysis() {
  const [result,   setResult]   = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  const trigger = async (readingId = null) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await runAnalysis(readingId)
      setResult(data)
      return data
    } catch (err) {
      const msg = err?.response?.data?.error || err.message || 'Analysis failed'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }

  return { result, loading, error, trigger }
}

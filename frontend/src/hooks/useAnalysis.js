/**
 * useAnalysis.js — triggers POST /api/analysis/run and tracks loading state.
 */
import { useState } from 'react'
import { runAnalysis } from '../services/api'
import { getErrorMessage } from '../utils/errors'

export function useAnalysis() {
  const [result,   setResult]   = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  const trigger = async (params = {}) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await runAnalysis(params)
      setResult(data)
      return data
    } catch (err) {
      const msg = getErrorMessage(err, 'Analysis failed. Please check inputs and try again.')
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setResult(null)
    setError(null)
    setLoading(false)
  }

  return { result, setResult, loading, error, trigger, reset }
}

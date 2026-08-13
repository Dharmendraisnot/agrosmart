/**
 * useHistory.js — fetches paginated prediction/analysis history.
 */
import { useState, useEffect, useCallback } from 'react'
import { getPredictionHistory, getAnalysisHistory } from '../services/api'

export function usePredictionHistory(perPage = 20) {
  const [items,   setItems]   = useState([])
  const [total,   setTotal]   = useState(0)
  const [pages,   setPages]   = useState(1)
  const [page,    setPage]    = useState(1)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const fetch = useCallback(async (p = page) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await getPredictionHistory(p, perPage)
      setItems(data.items)
      setTotal(data.total)
      setPages(data.pages)
      setPage(p)
    } catch (err) {
      setError(err?.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }, [page, perPage])

  useEffect(() => { fetch(1) }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  return { items, total, pages, page, loading, error, fetch, setPage }
}

export function useAnalysisHistory(perPage = 20) {
  const [items,   setItems]   = useState([])
  const [total,   setTotal]   = useState(0)
  const [pages,   setPages]   = useState(1)
  const [page,    setPage]    = useState(1)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const fetch = useCallback(async (p = page) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await getAnalysisHistory(p, perPage)
      setItems(data.items)
      setTotal(data.total)
      setPages(data.pages)
      setPage(p)
    } catch (err) {
      setError(err?.response?.data?.error || err.message)
    } finally {
      setLoading(false)
    }
  }, [page, perPage])

  useEffect(() => { fetch(1) }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  return { items, total, pages, page, loading, error, fetch, setPage }
}

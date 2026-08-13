/**
 * useSensorData.js — polls /api/sensors/latest every 10 seconds.
 * Writes results into the Zustand sensorStore.
 */
import { useEffect, useRef } from 'react'
import { getLatestReading } from '../services/api'
import useSensorStore from '../store/sensorStore'

const POLL_INTERVAL_MS = 10_000

export function useSensorData() {
  const { setReading, setError, setConnecting } = useSensorStore()
  const timerRef = useRef(null)

  const fetchReading = async () => {
    try {
      const { data } = await getLatestReading()
      setReading(data)
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Connection failed')
    }
  }

  useEffect(() => {
    setConnecting()
    fetchReading()                              // immediate first fetch
    timerRef.current = setInterval(fetchReading, POLL_INTERVAL_MS)
    return () => clearInterval(timerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}

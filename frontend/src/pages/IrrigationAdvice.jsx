/**
 * IrrigationAdvice.jsx — shows irrigation advice from latest analysis.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLatestPredictions } from '../services/api'
import IrrigationCard from '../components/recommendations/IrrigationCard'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorAlert     from '../components/shared/ErrorAlert'
import { fmtDate }   from '../utils/formatters'
import { RefreshCw } from 'lucide-react'

export default function IrrigationAdvice() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    getLatestPredictions()
      .then(({ data: d }) => setData(d))
      .catch((err) => {
        if (err?.response?.status === 404) setData(null)
        else setError(err?.response?.data?.error || err.message)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <LoadingSpinner message="Loading irrigation advice…" />

  const irrigation = data?.predictions?.irrigation?.result

  return (
    <div className="space-y-5">
      {error && <ErrorAlert message={error} />}

      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-xs text-gray-400">
          {data
            ? `Analysis #${data.analysis_id} · ${fmtDate(data.timestamp)}`
            : 'No analysis results yet'}
        </p>
        <div className="flex gap-2">
          <button onClick={load}
            className="btn-secondary flex items-center gap-1.5 text-sm py-2 px-3">
            <RefreshCw size={14} /> Refresh
          </button>
          <Link to="/analysis" className="btn-primary text-sm py-2 px-3">
            Run New Analysis
          </Link>
        </div>
      </div>

      {!data ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 text-sm mb-4">
            No analysis results found. Run an analysis to get irrigation advice.
          </p>
          <Link to="/analysis" className="btn-primary">Run Analysis</Link>
        </div>
      ) : (
        <IrrigationCard irrigation={irrigation} />
      )}
    </div>
  )
}

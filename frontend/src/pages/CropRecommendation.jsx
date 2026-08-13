/**
 * CropRecommendation.jsx — shows top-3 crops from the latest analysis.
 *
 * Fetches GET /api/predictions/latest and displays the crop predictions.
 * Provides a "Re-run Analysis" button if no data is present.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLatestPredictions } from '../services/api'
import CropList       from '../components/recommendations/CropList'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorAlert     from '../components/shared/ErrorAlert'
import { fmtDate }    from '../utils/formatters'
import { RefreshCw }  from 'lucide-react'

export default function CropRecommendation() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    getLatestPredictions()
      .then(({ data: d }) => setData(d))
      .catch((err) => {
        const msg = err?.response?.data?.error || err.message
        if (err?.response?.status === 404) {
          setData(null)
          setError(null)
        } else {
          setError(msg)
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <LoadingSpinner message="Loading crop recommendations…" />

  const crops = data?.predictions?.crop?.result?.crops || []

  return (
    <div className="space-y-5">
      {error && <ErrorAlert message={error} />}

      {/* Header row */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-xs text-gray-400">
            {data
              ? `Analysis #${data.analysis_id} · ${fmtDate(data.timestamp)}`
              : 'No analysis results yet'}
          </p>
        </div>
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

      {/* Soil context */}
      {data?.soil && (
        <div className="card flex flex-wrap gap-4 text-sm">
          <span className="text-gray-500">
            Soil type: <strong className="text-gray-700">{data.soil.type || '—'}</strong>
          </span>
          <span className="text-gray-500">
            Health: <strong className="text-gray-700">{data.soil.health_status}</strong>
            {' '}({data.soil.health_score}/100)
          </span>
        </div>
      )}

      {/* Crop list */}
      {!data ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 text-sm mb-4">
            No analysis results found. Run an analysis to get crop recommendations.
          </p>
          <Link to="/analysis" className="btn-primary">
            Run Analysis
          </Link>
        </div>
      ) : (
        <CropList crops={crops} />
      )}
    </div>
  )
}

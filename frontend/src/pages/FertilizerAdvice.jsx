/**
 * FertilizerAdvice.jsx — shows fertilizer recommendation from latest analysis,
 * with support for switching target crops on-demand.
 */
import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { getLatestPredictions, getFertilizerAdvice, getAnalysis } from '../services/api'
import FertilizerCard from '../components/recommendations/FertilizerCard'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorAlert     from '../components/shared/ErrorAlert'
import { fmtDate }   from '../utils/formatters'
import { getErrorMessage } from '../utils/errors'
import { RefreshCw, Leaf, Loader2 } from 'lucide-react'

export default function FertilizerAdvice() {
  const location = useLocation()
  const [data,    setData]    = useState(null)
  const [customFertilizer, setCustomFertilizer] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingCrop, setLoadingCrop] = useState(false)
  const [error,   setError]   = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    setCustomFertilizer(null)
    getLatestPredictions()
      .then(({ data: d }) => {
        setData(d)
        if (location.state?.selectedCrop) {
          switchCrop(d, location.state.selectedCrop)
        }
      })
      .catch((err) => {
        if (err?.response?.status === 404) setData(null)
        else setError(getErrorMessage(err, 'Failed to load fertilizer advice.'))
      })
      .finally(() => setLoading(false))
  }

  const switchCrop = async (predictionData, cropName) => {
    if (!predictionData) return
    setLoadingCrop(true)
    try {
      let sensorData = null
      if (predictionData.analysis_id) {
        try {
          const anResp = await getAnalysis(predictionData.analysis_id)
          sensorData = anResp?.data?.sensor_reading
        } catch (_) {}
      }
      const resp = await getFertilizerAdvice({
        sensor_data: sensorData,
        soil_type: predictionData.soil?.type,
        target_crop: cropName,
      })
      if (resp?.data) {
        setCustomFertilizer(resp.data)
      }
    } catch (err) {
      setError(getErrorMessage(err, `Failed to load advice for ${cropName}`))
    } finally {
      setLoadingCrop(false)
    }
  }

  useEffect(() => { load() }, [location.state?.selectedCrop])

  if (loading) return <LoadingSpinner message="Loading fertilizer advice…" />

  const rawFertilizer = data?.predictions?.fertilizer?.result
  const defaultFertilizer = rawFertilizer
    ? {
        ...rawFertilizer,
        crop: rawFertilizer.crop || data?.predictions?.crop?.top_recommendation,
        soil_type: rawFertilizer.soil_type || data?.soil?.type,
      }
    : null

  const activeFertilizer = customFertilizer || defaultFertilizer
  const topCrops = data?.predictions?.crop?.result?.crops || []

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

      {/* Quick crop switcher if predictions has top crops */}
      {topCrops.length > 0 && (
        <div className="card p-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-500 font-medium flex items-center gap-1">
            <Leaf size={14} className="text-agro-green" />
            Switch Crop Target:
          </span>
          {topCrops.map((c) => {
            const cropName = c.crop
            const isSelected = (activeFertilizer?.crop || '').toLowerCase() === cropName.toLowerCase()
            return (
              <button
                key={cropName}
                type="button"
                onClick={() => switchCrop(data, cropName)}
                disabled={loadingCrop}
                className={`px-3 py-1.5 rounded-lg border font-medium capitalize transition-all flex items-center gap-1 ${
                  isSelected
                    ? 'bg-agro-green text-white border-agro-green shadow-sm'
                    : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-white hover:border-agro-green hover:text-agro-green'
                }`}
              >
                {loadingCrop && isSelected ? <Loader2 size={12} className="animate-spin" /> : null}
                {cropName} (Rank {c.rank})
              </button>
            )
          })}
        </div>
      )}

      {!data ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 text-sm mb-4">
            No analysis results found. Run an analysis to get fertilizer recommendations.
          </p>
          <Link to="/analysis" className="btn-primary">Run Analysis</Link>
        </div>
      ) : (
        <FertilizerCard fertilizer={activeFertilizer} />
      )}
    </div>
  )
}

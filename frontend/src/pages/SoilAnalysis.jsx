/**
 * SoilAnalysis.jsx — upload image + trigger analysis + display soil result.
 *
 * Flow:
 *   1. (Optional) Upload a soil image → CNN soil type
 *   2. Click "Run Analysis" → POST /api/analysis/run
 *   3. Display soil type, health score, and links to recommendations
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAnalysis } from '../hooks/useAnalysis'
import AnalysisForm from '../components/analysis/AnalysisForm'
import ImageUpload  from '../components/analysis/ImageUpload'
import ResultCard   from '../components/analysis/ResultCard'
import ErrorAlert   from '../components/shared/ErrorAlert'
import { fmtDate }  from '../utils/formatters'
import { ArrowRight, Database } from 'lucide-react'

export default function SoilAnalysis() {
  const { result, loading, error, trigger } = useAnalysis()
  const [cnnResult, setCnnResult] = useState(null)

  const handleRun = () => trigger()

  return (
    <div className="space-y-6">

      {/* Error */}
      {error && <ErrorAlert message={error} />}

      {/* Image upload (optional) */}
      <div className="card">
        <h3 className="text-gray-700 mb-1">Step 1 — Upload Soil Image (optional)</h3>
        <p className="text-sm text-gray-400 mb-4">
          A soil photo improves classification accuracy via CNN.
          Skip this step to use sensor-based estimation.
        </p>
        <ImageUpload onResult={setCnnResult} />
      </div>

      {/* Trigger */}
      <AnalysisForm onRun={handleRun} loading={loading} />

      {/* Result */}
      {result && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-700">
              Analysis #{result.analysis_id}
              <span className="text-xs font-normal text-gray-400 ml-2">
                {fmtDate(result.timestamp)}
              </span>
            </h3>
          </div>

          {/* Soil type + health */}
          <ResultCard soil={result.soil} />

          {/* Sensor snapshot */}
          <details className="card cursor-pointer">
            <summary className="flex items-center gap-2 text-sm font-medium text-gray-600 select-none">
              <Database size={15} />
              Sensor Reading Snapshot (#{result.sensor_reading?.id})
            </summary>
            <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              {Object.entries(result.sensor_reading || {})
                .filter(([k]) => !['id', 'timestamp', 'source'].includes(k))
                .map(([k, v]) => (
                  <div key={k} className="bg-gray-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400 capitalize">{k.replace(/_/g, ' ')}</p>
                    <p className="font-semibold text-gray-700">{v != null ? Number(v).toFixed(1) : '—'}</p>
                  </div>
                ))}
            </div>
          </details>

          {/* Navigation to recommendations */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { to: '/crops',       label: 'View Crop Recommendations', color: 'bg-green-50 border-green-200 text-green-700' },
              { to: '/fertilizer',  label: 'View Fertilizer Advice',    color: 'bg-blue-50 border-blue-200 text-blue-700'   },
              { to: '/irrigation',  label: 'View Irrigation Advice',    color: 'bg-sky-50 border-sky-200 text-sky-700'      },
            ].map(({ to, label, color }) => (
              <Link
                key={to} to={to}
                className={`flex items-center justify-between p-4 rounded-xl border font-medium text-sm ${color} hover:opacity-80 transition-opacity`}
              >
                {label}
                <ArrowRight size={16} />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

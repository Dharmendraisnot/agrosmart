/**
 * SoilAnalysis.jsx — Full end-to-end software analysis workstation.
 *
 * Flow:
 *   1. (Optional) Upload a soil image → MobileNetV2 CNN classification
 *   2. Enter 8 manual soil/environmental parameters (or select a preset / simulator mode)
 *   3. If Alluvial soil is detected or selected, specify confirmed physical texture
 *   4. Run Analysis → executes crop recommendation, fertilizer advice, irrigation plan, health index
 *   5. Consolidated view of all outputs with scientific explanations
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAnalysis } from '../hooks/useAnalysis'
import AnalysisForm from '../components/analysis/AnalysisForm'
import ImageUpload  from '../components/analysis/ImageUpload'
import ResultCard   from '../components/analysis/ResultCard'
import CropList     from '../components/recommendations/CropList'
import FertilizerCard from '../components/recommendations/FertilizerCard'
import IrrigationCard from '../components/recommendations/IrrigationCard'
import ErrorAlert   from '../components/shared/ErrorAlert'
import { fmtDate }  from '../utils/formatters'
import { ArrowRight, Database, Sprout, Leaf, Droplets, CheckCircle } from 'lucide-react'

export default function SoilAnalysis() {
  const { result, loading, error, trigger, reset } = useAnalysis()
  const [cnnResult, setCnnResult] = useState(null)

  const handleRun = (options) => {
    trigger({
      ...options,
      image_path: cnnResult?.filename || options.image_path || null,
    })
  }

  const handleClearImage = () => {
    setCnnResult(null)
  }

  return (
    <div className="space-y-6">
      {/* Error alert */}
      {error && <ErrorAlert message={error} />}

      {/* Step 1: Image upload (optional) */}
      <div className="card">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-gray-800 font-semibold">Step 1 — Soil Image Classification (Optional)</h3>
          {cnnResult && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-green-100 text-green-700 flex items-center gap-1">
              <CheckCircle size={12} /> Image Linked
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Upload a soil photograph to classify soil order with MobileNetV2 (224×224).
          If skipped, the pipeline estimates soil type from soil moisture and pH rules.
        </p>
        <ImageUpload
          onResult={setCnnResult}
          onClear={handleClearImage}
        />
      </div>

      {/* Step 2: Analysis parameters & execution */}
      <div>
        <h3 className="text-gray-800 font-semibold mb-2">Step 2 — Soil & Environmental Parameters</h3>
        <AnalysisForm
          onRun={handleRun}
          loading={loading}
          detectedSoilType={cnnResult?.soil_type || null}
          imagePath={cnnResult?.filename || null}
        />
      </div>

      {/* Step 3: Consolidated Result View */}
      {result && (
        <div className="space-y-6 pt-2">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-4 bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div>
              <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                Analysis #{result.analysis_id} Complete
                <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-agro-green-pale text-agro-green">
                  {result.sensor_reading?.source === 'manual' ? 'Manual Input' : 'Simulator Reading'}
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Timestamp: {fmtDate(result.timestamp)}
              </p>
            </div>
            <button
              onClick={reset}
              className="text-xs text-gray-500 hover:text-gray-800 underline self-start sm:self-auto"
            >
              Clear Results
            </button>
          </div>

          {/* Soil Classification & Health Index */}
          <ResultCard soil={result.soil} />

          {/* Crop Recommendations */}
          <div className="space-y-3">
            <h3 className="text-gray-800 font-semibold flex items-center gap-2">
              <Sprout size={18} className="text-agro-green" />
              Recommended Crops (Random Forest Multi-Class)
            </h3>
            <CropList crops={result.crops || []} />
          </div>

          {/* Fertilizer & Irrigation Advice in 2 columns */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Fertilizer */}
            <div className="space-y-3">
              <h3 className="text-gray-800 font-semibold flex items-center gap-2">
                <Leaf size={18} className="text-agro-green" />
                Fertilizer Recommendation (Decision Tree)
              </h3>
              <FertilizerCard fertilizer={result.fertilizer} />
            </div>

            {/* Irrigation */}
            <div className="space-y-3">
              <h3 className="text-gray-800 font-semibold flex items-center gap-2">
                <Droplets size={18} className="text-agro-sky" />
                Irrigation Schedule (Agronomic Rules)
              </h3>
              <IrrigationCard irrigation={result.irrigation} />
            </div>
          </div>

          {/* Sensor Reading Snapshot (collapsible) */}
          <details className="card cursor-pointer" open>
            <summary className="flex items-center gap-2 text-sm font-semibold text-gray-700 select-none">
              <Database size={16} className="text-gray-500" />
              Input Parameter Snapshot (#{result.sensor_reading?.id} · Source: {result.sensor_reading?.source || 'manual'})
            </summary>
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 text-sm">
              {Object.entries(result.sensor_reading || {})
                .filter(([k]) => !['id', 'timestamp', 'source'].includes(k))
                .map(([k, v]) => {
                  let unit = ''
                  let label = k.replace(/_/g, ' ')
                  if (k === 'moisture') unit = '%'
                  else if (k === 'rainfall') unit = ' mm'
                  else if (k === 'ph') unit = ''
                  else if (k.includes('temp')) unit = '°C'
                  else if (k === 'air_humidity') unit = '%'
                  else if (['nitrogen', 'phosphorus', 'potassium'].includes(k)) unit = ' mg/kg'

                  return (
                    <div key={k} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                      <p className="text-xs text-gray-400 capitalize font-medium">{label}</p>
                      <p className="font-bold text-gray-800 mt-0.5">
                        {v != null ? `${Number(v).toFixed(1)}${unit}` : '—'}
                      </p>
                    </div>
                  )
                })}
            </div>
          </details>

          {/* Navigation to dedicated detail pages */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { to: '/crops',       label: 'View Detailed Crops Page',      color: 'bg-green-50 border-green-200 text-green-800' },
              { to: '/fertilizer',  label: 'View Detailed Fertilizer Page', color: 'bg-blue-50 border-blue-200 text-blue-800'   },
              { to: '/irrigation',  label: 'View Detailed Irrigation Page', color: 'bg-sky-50 border-sky-200 text-sky-800'      },
            ].map(({ to, label, color }) => (
              <Link
                key={to} to={to}
                className={`flex items-center justify-between p-4 rounded-xl border font-semibold text-sm ${color} hover:opacity-85 transition-opacity`}
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

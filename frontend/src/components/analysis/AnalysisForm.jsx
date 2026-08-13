/**
 * AnalysisForm.jsx — triggers POST /api/analysis/run with loading state.
 */
import { FlaskConical, Loader2 } from 'lucide-react'

export default function AnalysisForm({ onRun, loading }) {
  return (
    <div className="card flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <h3 className="text-gray-800">Run Soil Analysis</h3>
        <p className="text-sm text-gray-500 mt-0.5">
          Reads live sensor data and runs all AI models in one step.
        </p>
      </div>
      <button
        onClick={onRun}
        disabled={loading}
        className="btn-primary flex items-center gap-2 whitespace-nowrap"
      >
        {loading
          ? <><Loader2 size={16} className="animate-spin" /> Analysing…</>
          : <><FlaskConical size={16} /> Run Analysis</>
        }
      </button>
    </div>
  )
}

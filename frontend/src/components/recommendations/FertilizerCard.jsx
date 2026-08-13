/**
 * FertilizerCard.jsx — NPK fertilizer recommendation display.
 */
import { Leaf, AlertTriangle } from 'lucide-react'

export default function FertilizerCard({ fertilizer }) {
  if (!fertilizer) {
    return (
      <div className="card text-center py-10 text-gray-400">
        <Leaf size={32} className="mx-auto mb-2 opacity-40" />
        <p className="text-sm">No fertilizer data — run an analysis first.</p>
      </div>
    )
  }

  const isPrototype = fertilizer.model_label?.includes('prototype')

  return (
    <div className="space-y-4">
      {/* Prototype warning banner */}
      {isPrototype && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-50 border border-yellow-200 text-yellow-700 text-xs">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>
            Prototype model (Kaggle data). Will be replaced by AgroSmart-trained model after field data collection.
          </span>
        </div>
      )}

      {/* Main card */}
      <div className="card space-y-4">
        {/* Fertilizer name */}
        <div className="flex items-center gap-3">
          <div className="bg-agro-green/10 rounded-xl p-3">
            <Leaf size={22} className="text-agro-green" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
              Recommended Fertilizer
            </p>
            <p className="text-2xl font-bold text-agro-green">
              {fertilizer.fertilizer}
            </p>
          </div>
        </div>

        {/* Advice */}
        <div className="bg-agro-green-pale rounded-xl px-4 py-3">
          <p className="text-sm text-gray-700">{fertilizer.advice}</p>
        </div>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-4 pt-1 border-t border-gray-100 text-xs text-gray-400">
          {fertilizer.soil_type && (
            <span>Soil type: <strong className="text-gray-600">{fertilizer.soil_type}</strong></span>
          )}
          {fertilizer.crop && (
            <span>Top crop: <strong className="text-gray-600 capitalize">{fertilizer.crop}</strong></span>
          )}
          <span>Model: <strong className="text-gray-500">{fertilizer.model_label}</strong></span>
        </div>
      </div>
    </div>
  )
}

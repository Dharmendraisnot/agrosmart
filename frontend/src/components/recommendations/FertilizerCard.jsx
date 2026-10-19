/**
 * FertilizerCard.jsx — NPK fertilizer recommendation display.
 * Clearly distinguishes active predictions from scientifically withheld advice.
 */
import { Leaf, AlertTriangle, Info, CheckCircle2 } from 'lucide-react'

export default function FertilizerCard({ fertilizer }) {
  if (!fertilizer) {
    return (
      <div className="card text-center py-10 text-gray-400">
        <Leaf size={32} className="mx-auto mb-2 opacity-40" />
        <p className="text-sm">No fertilizer data — run an analysis first.</p>
      </div>
    )
  }

  const isUnavailable = fertilizer.fertilizer === 'Reliable recommendation unavailable' || fertilizer.status === 'unsupported'
  const isPrototype = fertilizer.model_label?.includes('prototype')

  return (
    <div className="space-y-4">
      {/* Prototype warning banner */}
      {isPrototype && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-50 border border-yellow-200 text-yellow-700 text-xs">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>
            Prototype model (Kaggle benchmark data). Will be upgraded with AgroSmart experimental field trials.
          </span>
        </div>
      )}

      {/* Main card */}
      <div className="card space-y-4">
        {/* Fertilizer name / status */}
        <div className="flex items-center gap-3">
          <div className={`rounded-xl p-3 ${isUnavailable ? 'bg-amber-100 text-amber-700' : 'bg-agro-green/10 text-agro-green'}`}>
            {isUnavailable ? <AlertTriangle size={22} /> : <Leaf size={22} />}
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
              {isUnavailable ? 'Recommendation Status' : 'Recommended Fertilizer'}
            </p>
            <p className={`text-2xl font-bold ${isUnavailable ? 'text-amber-800 text-xl' : 'text-agro-green'}`}>
              {fertilizer.fertilizer}
            </p>
          </div>
        </div>

        {/* Advice / Reason Box */}
        <div className={`rounded-xl px-4 py-3.5 border text-sm ${
          isUnavailable
            ? 'bg-amber-50/70 border-amber-200 text-amber-900 leading-relaxed'
            : 'bg-agro-green-pale border-agro-green/20 text-gray-800'
        }`}>
          <div className="flex items-start gap-2">
            {isUnavailable ? (
              <Info size={16} className="text-amber-600 mt-0.5 shrink-0" />
            ) : (
              <CheckCircle2 size={16} className="text-agro-green mt-0.5 shrink-0" />
            )}
            <p>{fertilizer.advice}</p>
          </div>
        </div>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-4 pt-1 border-t border-gray-100 text-xs text-gray-400">
          {fertilizer.soil_type && (
            <span>Soil type: <strong className="text-gray-600">{fertilizer.soil_type}</strong></span>
          )}
          {fertilizer.crop && (
            <span>Crop: <strong className="text-gray-600 capitalize">{fertilizer.crop}</strong></span>
          )}
          {fertilizer.mapped_crop_category && (
            <span>Mapped category: <strong className="text-gray-600">{fertilizer.mapped_crop_category}</strong></span>
          )}
          <span>Model: <strong className="text-gray-500">{fertilizer.model_label}</strong></span>
        </div>
      </div>
    </div>
  )
}

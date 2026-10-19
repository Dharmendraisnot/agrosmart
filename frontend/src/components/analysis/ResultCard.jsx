/**
 * ResultCard.jsx — soil type + health score summary card.
 * Clearly distinguishes CNN classification from heuristic estimation and manual overrides.
 */
import StatusBadge from '../shared/StatusBadge'
import { fmtFloat, fmtConfidence } from '../../utils/formatters'
import { Layers, Heart, Sparkles, Sliders } from 'lucide-react'

export default function ResultCard({ soil }) {
  if (!soil) return null
  const { type, type_confidence, health_status, health_score, confirmed_soil_texture, cnn_status } = soil

  const scoreColor =
    health_score >= 70 ? 'text-green-600' :
    health_score >= 45 ? 'text-yellow-600' : 'text-red-500'

  const isCnn = type_confidence != null || cnn_status === 'ok'

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Soil type & origin */}
      <div className="card flex items-start gap-4">
        <div className="bg-agro-earth/10 rounded-xl p-3 shrink-0">
          <Layers size={22} className="text-agro-earth" />
        </div>
        <div className="flex-1">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Soil Classification
          </p>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold text-gray-800">{type || '—'}</p>
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-600">
              {isCnn ? 'CNN Predicted' : 'Heuristic Estimate'}
            </span>
          </div>

          {isCnn && type_confidence != null && (
            <p className="text-xs text-green-700 font-medium mt-1 flex items-center gap-1">
              <Sparkles size={12} />
              MobileNetV2 Confidence: {fmtConfidence(type_confidence)}
            </p>
          )}

          {!isCnn && (
            <p className="text-xs text-gray-500 mt-1">
              Estimated via moisture & pH agronomic rules (no image supplied)
            </p>
          )}

          {confirmed_soil_texture && (
            <div className="mt-2.5 pt-2 border-t border-gray-100 text-xs text-gray-600 flex items-center gap-1.5">
              <Sliders size={12} className="text-agro-green" />
              <span>Confirmed Physical Texture: <strong className="text-gray-800">{confirmed_soil_texture}</strong></span>
            </div>
          )}
        </div>
      </div>

      {/* Health score */}
      <div className="card flex items-start gap-4">
        <div className="bg-green-50 rounded-xl p-3 shrink-0">
          <Heart size={22} className="text-green-600" />
        </div>
        <div className="flex-1">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Soil Health Index
          </p>
          <div className="flex items-center gap-2">
            <p className={`text-2xl font-bold ${scoreColor}`}>
              {fmtFloat(health_score, 0)}
              <span className="text-base font-normal text-gray-400">/100</span>
            </p>
            <StatusBadge status={health_status} />
          </div>
          {/* Score bar */}
          <div className="mt-2.5 w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-1.5 rounded-full transition-all duration-500 ${
                health_score >= 70 ? 'bg-green-500' :
                health_score >= 45 ? 'bg-yellow-400' : 'bg-red-400'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, health_score ?? 0))}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Evaluates pH, moisture adequacy, temperature, and NPK balance
          </p>
        </div>
      </div>
    </div>
  )
}

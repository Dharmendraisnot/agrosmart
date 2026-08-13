/**
 * ResultCard.jsx — soil type + health score summary card.
 */
import StatusBadge from '../shared/StatusBadge'
import { fmtFloat, fmtConfidence } from '../../utils/formatters'
import { Layers, Heart } from 'lucide-react'

export default function ResultCard({ soil }) {
  if (!soil) return null
  const { type, type_confidence, health_status, health_score } = soil

  const scoreColor =
    health_score >= 70 ? 'text-green-600' :
    health_score >= 45 ? 'text-yellow-600' : 'text-red-500'

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Soil type */}
      <div className="card flex items-start gap-4">
        <div className="bg-agro-earth/10 rounded-xl p-3">
          <Layers size={22} className="text-agro-earth" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Soil Type
          </p>
          <p className="text-2xl font-bold text-gray-800">{type || '—'}</p>
          {type_confidence != null && (
            <p className="text-xs text-gray-400 mt-0.5">
              CNN confidence: {fmtConfidence(type_confidence)}
            </p>
          )}
          {!type_confidence && (
            <p className="text-xs text-gray-400 mt-0.5">
              Estimated from sensor data
            </p>
          )}
        </div>
      </div>

      {/* Health score */}
      <div className="card flex items-start gap-4">
        <div className="bg-green-50 rounded-xl p-3">
          <Heart size={22} className="text-green-600" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
            Soil Health
          </p>
          <div className="flex items-center gap-2">
            <p className={`text-2xl font-bold ${scoreColor}`}>
              {fmtFloat(health_score, 0)}
              <span className="text-base font-normal text-gray-400">/100</span>
            </p>
            <StatusBadge status={health_status} />
          </div>
          {/* Score bar */}
          <div className="mt-2 w-full bg-gray-100 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-500 ${
                health_score >= 70 ? 'bg-green-500' :
                health_score >= 45 ? 'bg-yellow-400' : 'bg-red-400'
              }`}
              style={{ width: `${health_score ?? 0}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

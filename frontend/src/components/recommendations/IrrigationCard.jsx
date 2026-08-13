/**
 * IrrigationCard.jsx — irrigation advice display.
 */
import { Droplets, Thermometer, Clock, CloudRain } from 'lucide-react'
import { URGENCY_COLOR } from '../../utils/constants'
import { fmtFloat } from '../../utils/formatters'

export default function IrrigationCard({ irrigation }) {
  if (!irrigation) {
    return (
      <div className="card text-center py-10 text-gray-400">
        <Droplets size={32} className="mx-auto mb-2 opacity-40" />
        <p className="text-sm">No irrigation data — run an analysis first.</p>
      </div>
    )
  }

  const urgencyClass = URGENCY_COLOR[irrigation.urgency] || URGENCY_COLOR.unknown

  return (
    <div className="space-y-4">
      {/* Action banner */}
      <div className={`p-4 rounded-2xl border-2 flex items-start gap-3 ${urgencyClass}`}>
        <Droplets size={22} className="mt-0.5 shrink-0" />
        <div>
          <p className="font-bold text-base">{irrigation.action}</p>
          {irrigation.reasoning && (
            <p className="text-sm mt-0.5 opacity-80">{irrigation.reasoning}</p>
          )}
        </div>
      </div>

      {/* Detail grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="card text-center">
          <Clock size={18} className="mx-auto text-agro-sky mb-1" />
          <p className="text-xs text-gray-400 mb-0.5">Frequency</p>
          <p className="text-sm font-semibold text-gray-700">{irrigation.frequency}</p>
        </div>
        <div className="card text-center">
          <CloudRain size={18} className="mx-auto text-agro-sky mb-1" />
          <p className="text-xs text-gray-400 mb-0.5">Est. Water</p>
          <p className="text-sm font-semibold text-gray-700">{irrigation.estimated_water}</p>
        </div>
        <div className="card text-center">
          <Droplets size={18} className="mx-auto text-agro-sky mb-1" />
          <p className="text-xs text-gray-400 mb-0.5">Effective Moisture</p>
          <p className="text-sm font-semibold text-gray-700">
            {fmtFloat(irrigation.effective_moisture)}%
          </p>
        </div>
      </div>

      {/* Temperature note */}
      {irrigation.temperature_note && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-orange-50 border border-orange-200 text-orange-700 text-sm">
          <Thermometer size={16} className="mt-0.5 shrink-0" />
          <span>{irrigation.temperature_note}</span>
        </div>
      )}
    </div>
  )
}

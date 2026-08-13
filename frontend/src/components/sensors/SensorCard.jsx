/**
 * SensorCard.jsx — displays a single sensor value with colour-coded status ring.
 */
import { SENSOR_THRESHOLDS } from '../../utils/constants'
import { fmtFloat } from '../../utils/formatters'

function getSensorColor(key, value) {
  if (value == null) return { ring: 'border-gray-200', text: 'text-gray-400', bg: 'bg-gray-50' }
  const t = SENSOR_THRESHOLDS[key]
  if (!t) return { ring: 'border-gray-200', text: 'text-gray-600', bg: 'bg-gray-50' }
  if (value < t.low)  return { ring: 'border-red-300',    text: 'text-red-600',    bg: 'bg-red-50'    }
  if (value > t.high) return { ring: 'border-orange-300', text: 'text-orange-600', bg: 'bg-orange-50' }
  return               { ring: 'border-green-300',   text: 'text-green-700',  bg: 'bg-green-50'  }
}

export default function SensorCard({ sensorKey, value }) {
  const t = SENSOR_THRESHOLDS[sensorKey] || { label: sensorKey, unit: '' }
  const color = getSensorColor(sensorKey, value)
  const decimals = sensorKey === 'ph' ? 2 : 1

  return (
    <div className={`card flex flex-col items-center gap-2 py-6 border-2 ${color.ring}`}>
      {/* Value */}
      <div className={`${color.bg} rounded-full w-16 h-16 flex items-center justify-center`}>
        <span className={`text-xl font-bold ${color.text}`}>
          {fmtFloat(value, decimals)}
        </span>
      </div>

      {/* Unit */}
      <p className="text-xs text-gray-400 font-medium">{t.unit || 'value'}</p>

      {/* Label */}
      <p className="text-sm font-medium text-gray-600 text-center leading-tight">{t.label}</p>
    </div>
  )
}

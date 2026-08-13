/**
 * Dashboard.jsx — live sensor overview with auto-polling every 10 s.
 */
import { useSensorData } from '../hooks/useSensorData'
import useSensorStore from '../store/sensorStore'
import SensorGrid from '../components/sensors/SensorGrid'
import SensorChart from '../components/sensors/SensorChart'
import StatusBadge from '../components/shared/StatusBadge'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorAlert from '../components/shared/ErrorAlert'
import { fmtDate } from '../utils/formatters'
import { RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  useSensorData()   // start / maintain polling

  const { reading, status, errorMessage, lastUpdated } = useSensorStore()

  return (
    <div className="space-y-6">

      {/* ── Status banner ──────────────────────────────────────────── */}
      {status === 'error' && (
        <ErrorAlert message={`Sensor connection error: ${errorMessage}`} />
      )}

      {/* ── Header row ────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-gray-800">Live Sensor Dashboard</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {status === 'live'
              ? `Last updated ${fmtDate(lastUpdated)}`
              : status === 'connecting'
              ? 'Connecting to sensors…'
              : 'Sensor offline'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {status === 'live'
            ? <Wifi size={16} className="text-green-500" />
            : <WifiOff size={16} className="text-red-400" />}
          <span className="text-xs text-gray-500 capitalize">{status}</span>
        </div>
      </div>

      {/* ── Sensor grid ───────────────────────────────────────────── */}
      {status === 'connecting' && !reading
        ? <LoadingSpinner message="Waiting for first sensor reading…" />
        : <SensorGrid reading={reading} />
      }

      {/* ── Quick stats row ───────────────────────────────────────── */}
      {reading && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="card">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
              Sensor Mode
            </p>
            <p className="text-lg font-bold text-agro-green capitalize">
              {reading.source || 'simulator'}
            </p>
          </div>
          <div className="card">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
              Reading ID
            </p>
            <p className="text-lg font-bold text-gray-700">#{reading.id}</p>
          </div>
          <div className="card">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
              Timestamp
            </p>
            <p className="text-sm font-semibold text-gray-700">
              {fmtDate(reading.timestamp)}
            </p>
          </div>
        </div>
      )}

      {/* ── Trend charts row ──────────────────────────────────────── */}
      <div>
        <h3 className="text-gray-700 mb-3">Sensor Trends</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SensorChart sensorKey="moisture" />
          <SensorChart sensorKey="ph" />
        </div>
      </div>

      {/* ── Run analysis CTA ──────────────────────────────────────── */}
      <div className="card flex flex-col sm:flex-row items-center justify-between gap-4 bg-agro-green-pale border-agro-green/20">
        <div>
          <h3 className="text-agro-green">Ready to analyse your soil?</h3>
          <p className="text-sm text-gray-600 mt-0.5">
            Run the full AI pipeline — crop, fertilizer and irrigation recommendations.
          </p>
        </div>
        <Link to="/analysis" className="btn-primary whitespace-nowrap">
          Run Analysis →
        </Link>
      </div>
    </div>
  )
}

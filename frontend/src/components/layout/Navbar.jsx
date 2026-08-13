/**
 * Navbar.jsx — top bar (mobile-friendly, shows sensor status indicator).
 */
import { Menu } from 'lucide-react'
import useSensorStore from '../../store/sensorStore'

export default function Navbar({ onMenuClick, title }) {
  const status = useSensorStore((s) => s.status)

  const dot = {
    live:       'bg-green-400 animate-pulse',
    connecting: 'bg-yellow-400 animate-pulse',
    error:      'bg-red-400',
  }[status] || 'bg-gray-400'

  const label = {
    live:       'Live',
    connecting: 'Connecting…',
    error:      'Offline',
  }[status] || '—'

  return (
    <header className="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3">
      <button
        onClick={onMenuClick}
        className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      <h1 className="flex-1 text-base font-semibold text-gray-800">{title}</h1>

      {/* Sensor status pill */}
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        {label}
      </div>
    </header>
  )
}

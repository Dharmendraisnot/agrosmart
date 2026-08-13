/**
 * ErrorAlert.jsx — dismissable red error banner.
 */
import { AlertTriangle } from 'lucide-react'

export default function ErrorAlert({ message, onDismiss }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <p className="flex-1 text-sm">{message}</p>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-400 hover:text-red-600 text-lg leading-none">×</button>
      )}
    </div>
  )
}

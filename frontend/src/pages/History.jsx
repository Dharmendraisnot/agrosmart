/**
 * History.jsx — paginated table of all past analyses and predictions.
 */
import { useState } from 'react'
import { useAnalysisHistory } from '../hooks/useHistory'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorAlert     from '../components/shared/ErrorAlert'
import StatusBadge    from '../components/shared/StatusBadge'
import { fmtDate, fmtFloat } from '../utils/formatters'
import { ChevronLeft, ChevronRight, History as HistoryIcon } from 'lucide-react'

export default function History() {
  const { items, total, pages, page, loading, error, fetch } = useAnalysisHistory(15)

  if (loading && items.length === 0)
    return <LoadingSpinner message="Loading history…" />

  return (
    <div className="space-y-5">
      {error && <ErrorAlert message={error} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">{total} analyses recorded</p>
      </div>

      {items.length === 0 ? (
        <div className="card text-center py-14">
          <HistoryIcon size={36} className="mx-auto text-gray-200 mb-3" />
          <p className="text-gray-400 text-sm">No analysis history yet.</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  {['#', 'Date', 'Soil Type', 'Health', 'Score', 'Top Crop', 'Fertilizer', 'Irrigation'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((a) => {
                  const crop  = a.predictions?.crop?.top_recommendation  || '—'
                  const fert  = a.predictions?.fertilizer?.top_recommendation || '—'
                  const irr   = a.predictions?.irrigation?.top_recommendation  || '—'
                  return (
                    <tr key={a.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-gray-400">#{a.id}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-gray-600">{fmtDate(a.timestamp)}</td>
                      <td className="px-4 py-3 font-medium text-gray-700">{a.soil_type || '—'}</td>
                      <td className="px-4 py-3"><StatusBadge status={a.soil_health_status} /></td>
                      <td className="px-4 py-3 text-gray-600">{fmtFloat(a.health_score, 0)}</td>
                      <td className="px-4 py-3 capitalize text-gray-700">{crop}</td>
                      <td className="px-4 py-3 text-gray-700">{fert}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate" title={irr}>{irr}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => fetch(page - 1)}
                className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm text-gray-500">
                Page {page} of {pages}
              </span>
              <button
                disabled={page >= pages}
                onClick={() => fetch(page + 1)}
                className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

/**
 * History.jsx — paginated table of all past software soil analyses and predictions.
 */
import { useState } from 'react'
import { useAnalysisHistory } from '../hooks/useHistory'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorAlert     from '../components/shared/ErrorAlert'
import StatusBadge    from '../components/shared/StatusBadge'
import { fmtDate, fmtFloat, fmtConfidence } from '../utils/formatters'
import { ChevronLeft, ChevronRight, History as HistoryIcon, Image as ImageIcon, Sparkles, ChevronDown, ChevronUp } from 'lucide-react'

export default function History() {
  const { items, total, pages, page, loading, error, fetch } = useAnalysisHistory(15)
  const [expandedId, setExpandedId] = useState(null)

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  if (loading && items.length === 0)
    return <LoadingSpinner message="Loading analysis history from database…" />

  return (
    <div className="space-y-5">
      {error && <ErrorAlert message={error} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-gray-800 font-bold">Analysis History</h2>
          <p className="text-xs text-gray-400 mt-0.5">{total} software analyses recorded in database</p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="card text-center py-14">
          <HistoryIcon size={36} className="mx-auto text-gray-200 mb-3" />
          <p className="text-gray-400 text-sm">No analysis history found in the database.</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50">
                  <th className="w-8"></th>
                  {['#', 'Date', 'Soil Classification', 'CNN Conf', 'Health', 'Score', 'Top Crop', 'Fertilizer Advice', 'Irrigation'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((a) => {
                  const crop = a.predictions?.crop?.top_recommendation  || '—'
                  const fert = a.predictions?.fertilizer?.top_recommendation || '—'
                  const irr  = a.predictions?.irrigation?.top_recommendation  || '—'
                  const isExpanded = expandedId === a.id
                  const isCnn = a.soil_type_confidence != null

                  return (
                    <tr key={a.id} className="group hover:bg-gray-50/80 transition-colors">
                      <td className="pl-3 py-3 text-gray-400">
                        <button
                          type="button"
                          onClick={() => toggleExpand(a.id)}
                          className="p-1 rounded hover:bg-gray-200 text-gray-500"
                          title="Toggle details"
                        >
                          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-500">#{a.id}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-gray-600">{fmtDate(a.timestamp)}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">
                        <div className="flex items-center gap-1.5">
                          {a.soil_image_path && <ImageIcon size={13} className="text-agro-green" title="Soil Image Attached" />}
                          <span>{a.soil_type || '—'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-xs">
                        {isCnn ? (
                          <span className="font-semibold text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200 flex items-center gap-1 w-fit">
                            <Sparkles size={10} />
                            {fmtConfidence(a.soil_type_confidence)}
                          </span>
                        ) : (
                          <span className="text-gray-400 italic">Heuristic</span>
                        )}
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={a.soil_health_status} /></td>
                      <td className="px-4 py-3 font-medium text-gray-700">{fmtFloat(a.health_score, 0)}/100</td>
                      <td className="px-4 py-3 capitalize font-semibold text-agro-green">{crop}</td>
                      <td className="px-4 py-3 text-gray-700 max-w-[180px] truncate" title={fert}>
                        {fert === 'Reliable recommendation unavailable' ? (
                          <span className="text-amber-700 font-medium italic text-xs">Withheld (Unsupported)</span>
                        ) : (
                          fert
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate text-xs" title={irr}>{irr}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Details drawer for expanded row */}
          {expandedId && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-2 text-xs">
              <p className="font-bold text-gray-700">Detailed Record for Analysis #{expandedId}:</p>
              {(() => {
                const item = items.find((i) => i.id === expandedId)
                if (!item) return null
                return (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                      <p className="font-semibold text-gray-600 mb-1">Crop Prediction Result:</p>
                      <p className="text-gray-800">{item.predictions?.crop?.top_recommendation || 'None'}</p>
                      <p className="text-gray-400 mt-1">Model: {item.predictions?.crop?.model_version || 'rf_v1'}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                      <p className="font-semibold text-gray-600 mb-1">Fertilizer Advice:</p>
                      <p className="text-gray-800">{item.predictions?.fertilizer?.result?.advice || item.predictions?.fertilizer?.top_recommendation || 'None'}</p>
                      <p className="text-gray-400 mt-1">Model: {item.predictions?.fertilizer?.model_version || 'unknown'}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                      <p className="font-semibold text-gray-600 mb-1">Irrigation Schedule:</p>
                      <p className="text-gray-800">{item.predictions?.irrigation?.result?.action || item.predictions?.irrigation?.top_recommendation || 'None'}</p>
                      <p className="text-gray-400 mt-1">Urgency: {item.predictions?.irrigation?.result?.urgency || 'medium'}</p>
                    </div>
                  </div>
                )
              })()}
            </div>
          )}

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                disabled={page <= 1}
                onClick={() => fetch(page - 1)}
                className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm text-gray-500 font-medium">
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

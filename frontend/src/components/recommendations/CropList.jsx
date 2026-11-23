/**
 * CropList.jsx — ranked crop recommendations with confidence bars and fertilizer advice actions.
 */
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Sprout, Leaf, CheckCircle2, Loader2 } from 'lucide-react'
import { fmtConfidence } from '../../utils/formatters'

const COLORS = ['#2d7a3a', '#4caf50', '#81c784']

export default function CropList({
  crops,
  activeCrop = null,
  onSelectCrop = null,
  loadingCrop = null,
}) {
  if (!crops || crops.length === 0) {
    return (
      <div className="card text-center py-10 text-gray-400">
        <Sprout size={32} className="mx-auto mb-2 opacity-40" />
        <p className="text-sm">No crop data — run an analysis first.</p>
      </div>
    )
  }

  const chartData = crops.map((c) => ({
    name: c.crop.charAt(0).toUpperCase() + c.crop.slice(1),
    confidence: Math.round(c.confidence * 100),
  }))

  return (
    <div className="space-y-4">
      {/* Bar chart */}
      <div className="card">
        <p className="text-sm font-medium text-gray-600 mb-3">Crop Suitability Scores</p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 10 }}>
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }}
                   tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={80} />
            <Tooltip formatter={(v) => [`${v}%`, 'Confidence']} />
            <Bar dataKey="confidence" radius={[0, 6, 6, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i] || '#a5d6a7'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Ranked list */}
      <div className="space-y-3">
        {crops.map((c) => {
          const isActive = (activeCrop || '').toLowerCase() === c.crop.toLowerCase()
          const isLoading = loadingCrop === c.crop

          return (
            <div
              key={c.crop}
              className={`card flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all ${
                isActive ? 'border-agro-green/50 bg-emerald-50/20 shadow-sm' : ''
              }`}
            >
              <div className="flex items-center gap-4 flex-1">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0
                  ${c.rank === 1 ? 'bg-agro-green' : c.rank === 2 ? 'bg-agro-green-light' : 'bg-gray-300'}`}>
                  {c.rank}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-gray-800 capitalize truncate">{c.crop}</p>
                    {isActive && (
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 flex items-center gap-1 shrink-0">
                        <CheckCircle2 size={11} /> Active Advice
                      </span>
                    )}
                  </div>
                  <div className="mt-1 w-full bg-gray-100 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-agro-green transition-all duration-700"
                      style={{ width: `${Math.round(c.confidence * 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-3 pl-13 sm:pl-0">
                <span className="text-sm font-bold text-agro-green shrink-0">
                  {fmtConfidence(c.confidence)}
                </span>

                {onSelectCrop && (
                  <button
                    type="button"
                    onClick={() => onSelectCrop(c.crop)}
                    disabled={isLoading}
                    className={`text-xs px-3 py-1.5 rounded-xl border font-medium transition-all flex items-center gap-1.5 shrink-0 ${
                      isActive
                        ? 'bg-agro-green text-white border-agro-green shadow-sm'
                        : 'bg-white text-gray-700 border-gray-200 hover:border-agro-green hover:text-agro-green'
                    }`}
                    title={`Calculate fertilizer dose and application guidelines for ${c.crop}`}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 size={13} className="animate-spin" />
                        <span>Updating…</span>
                      </>
                    ) : (
                      <>
                        <Leaf size={13} className={isActive ? 'text-white' : 'text-agro-green'} />
                        <span>{isActive ? 'Advice Loaded' : 'View Fertilizer Advice'}</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

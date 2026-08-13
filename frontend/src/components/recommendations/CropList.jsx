/**
 * CropList.jsx — ranked crop recommendations with confidence bars.
 */
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Sprout } from 'lucide-react'
import { fmtConfidence } from '../../utils/formatters'

const COLORS = ['#2d7a3a', '#4caf50', '#81c784']

export default function CropList({ crops }) {
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
        {crops.map((c) => (
          <div key={c.crop} className="card flex items-center gap-4">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm
              ${c.rank === 1 ? 'bg-agro-green' : c.rank === 2 ? 'bg-agro-green-light' : 'bg-gray-300'}`}>
              {c.rank}
            </div>
            <div className="flex-1">
              <p className="font-semibold text-gray-800 capitalize">{c.crop}</p>
              <div className="mt-1 w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full bg-agro-green transition-all duration-700"
                  style={{ width: `${Math.round(c.confidence * 100)}%` }}
                />
              </div>
            </div>
            <span className="text-sm font-bold text-agro-green">
              {fmtConfidence(c.confidence)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

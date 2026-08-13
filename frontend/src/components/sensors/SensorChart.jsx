/**
 * SensorChart.jsx — Recharts line chart for a single sensor's recent history.
 */
import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import { getSensorHistory } from '../../services/api'
import { SENSOR_THRESHOLDS } from '../../utils/constants'
import LoadingSpinner from '../shared/LoadingSpinner'

export default function SensorChart({ sensorKey }) {
  const [data,    setData]    = useState([])
  const [loading, setLoading] = useState(true)
  const t = SENSOR_THRESHOLDS[sensorKey] || { label: sensorKey, unit: '' }

  useEffect(() => {
    getSensorHistory(1, 30)
      .then(({ data: res }) => {
        // Reverse so oldest is left
        const points = [...res.items].reverse().map((r, i) => ({
          index: i + 1,
          value: r[sensorKey],
          ts: r.timestamp,
        }))
        setData(points)
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [sensorKey])

  if (loading) return <LoadingSpinner message="Loading chart…" />

  return (
    <div className="card">
      <p className="text-sm font-medium text-gray-600 mb-3">{t.label} — last 30 readings</p>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="index" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} width={40} />
          <Tooltip
            formatter={(v) => [`${Number(v).toFixed(1)}${t.unit}`, t.label]}
            labelFormatter={(i) => `Reading #${i}`}
          />
          <Line
            type="monotone" dataKey="value"
            stroke="#2d7a3a" strokeWidth={2} dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

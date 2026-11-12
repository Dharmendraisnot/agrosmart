import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { fmtTime, formatValue } from '../utils/metrics';

// Single-metric time series. `readings` must be oldest -> newest.
export default function TrendChart({ readings, metric, height = 240 }) {
  const data = readings
    .filter((r) => r[metric.key] !== null && r[metric.key] !== undefined)
    .map((r) => ({ t: r.timestamp, v: r[metric.key] }));
  const gid = `grad-${metric.key}`;
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={metric.color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={metric.color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="t" tickFormatter={fmtTime} tick={{ fontSize: 11, fill: '#94a3b8' }} minTickGap={36} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
          <Tooltip
            labelFormatter={(t) => new Date(t).toLocaleString()}
            formatter={(v) => [`${formatValue(metric, v)} ${metric.unit}`, metric.label]}
            contentStyle={{ borderRadius: 12, border: '1px solid #dcfce7', fontSize: 12 }}
          />
          <Area type="monotone" dataKey="v" stroke={metric.color} strokeWidth={2.5} fill={`url(#${gid})`} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

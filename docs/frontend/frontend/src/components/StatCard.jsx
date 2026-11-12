import { Badge } from './ui';
import { formatValue, statusOf } from '../utils/metrics';

const LABEL = { optimal: 'Optimal', low: 'Low', high: 'High', unknown: 'No data' };

// Horizontal bar with the optimal band shaded and a marker at the current value.
export function RangeBar({ metric, value }) {
  const span = metric.max - metric.min;
  const at = (v) => Math.min(100, Math.max(0, ((v - metric.min) / span) * 100));
  const status = statusOf(metric, value);
  const marker = status === 'optimal' ? 'bg-leaf-600' : status === 'unknown' ? 'bg-slate-300' : 'bg-amber-500';
  return (
    <div className="relative mt-3 h-2 rounded-full bg-slate-100">
      <div
        className="absolute inset-y-0 rounded-full bg-leaf-200"
        style={{ left: `${at(metric.lo)}%`, width: `${at(metric.hi) - at(metric.lo)}%` }}
      />
      {value !== null && value !== undefined && (
        <div
          className={`absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white shadow ${marker}`}
          style={{ left: `${at(value)}%`, transition: 'left .6s ease' }}
        />
      )}
    </div>
  );
}

export default function StatCard({ metric, value, compact = false }) {
  const Icon = metric.icon;
  const status = statusOf(metric, value);
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <span
          className="grid h-9 w-9 place-items-center rounded-xl"
          style={{ background: `${metric.color}1a`, color: metric.color }}
        >
          <Icon size={18} />
        </span>
        <Badge tone={status}>{LABEL[status]}</Badge>
      </div>
      <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{metric.label}</p>
      <p className={`font-extrabold text-slate-900 ${compact ? 'text-xl' : 'text-3xl'}`}>
        {formatValue(metric, value)}
        <span className="ml-1 text-sm font-semibold text-slate-400">{metric.unit}</span>
      </p>
      <RangeBar metric={metric} value={value} />
      <p className="mt-1.5 text-[11px] text-slate-400">
        Optimal {metric.lo}–{metric.hi}
        {metric.unit && ` ${metric.unit}`}
      </p>
    </div>
  );
}

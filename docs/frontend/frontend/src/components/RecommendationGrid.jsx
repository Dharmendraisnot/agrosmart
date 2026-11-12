import { Droplets, FlaskConical, Layers, Sprout, Gauge } from 'lucide-react';
import { Badge } from './ui';
import { capitalize } from '../utils/metrics';

const PRIORITY_TONE = { high: 'high', medium: 'low', low: 'optimal' };

function Confidence({ value }) {
  if (value === null || value === undefined) return null;
  return (
    <div className="mt-3">
      <div className="mb-1 flex justify-between text-xs font-semibold text-slate-500">
        <span>Confidence</span>
        <span>{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100">
        <div className="h-2 rounded-full bg-leaf-500" style={{ width: `${Math.min(100, value)}%`, transition: 'width .8s ease' }} />
      </div>
    </div>
  );
}

function Alternatives({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="mt-3 space-y-1.5 border-t border-slate-100 pt-3">
      {items.slice(0, 3).map((a, i) => (
        <li key={a.name} className="flex items-center justify-between text-xs text-slate-500">
          <span>
            {i + 1}. {capitalize(a.name)}
          </span>
          {a.confidence !== null && <span className="font-semibold">{a.confidence.toFixed(1)}%</span>}
        </li>
      ))}
    </ul>
  );
}

function Tile({ icon: Icon, tint, title, children }) {
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center gap-2">
        <span className={`grid h-9 w-9 place-items-center rounded-xl ${tint}`}>
          <Icon size={18} />
        </span>
        <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{title}</p>
      </div>
      {children}
    </div>
  );
}

// The four AI outputs: crop, fertilizer, soil type, irrigation.
export default function RecommendationGrid({ analysis }) {
  if (!analysis) return null;
  const { crop, fertilizer, soil, irrigation } = analysis;
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Tile icon={Sprout} tint="bg-leaf-100 text-leaf-700" title="Recommended Crop">
        <p className="text-2xl font-extrabold text-leaf-900">{crop ? capitalize(crop.name) : '—'}</p>
        <p className="text-xs text-slate-400">Random Forest</p>
        <Confidence value={crop?.confidence} />
        <Alternatives items={crop?.alternatives} />
      </Tile>

      <Tile icon={FlaskConical} tint="bg-violet-100 text-violet-700" title="Fertilizer">
        <p className="text-2xl font-extrabold text-leaf-900">{fertilizer ? fertilizer.name : '—'}</p>
        <p className="text-xs text-slate-400">Decision Tree{fertilizer?.model ? ` · ${fertilizer.model}` : ''}</p>
        <Confidence value={fertilizer?.confidence} />
      </Tile>

      <Tile icon={Layers} tint="bg-soil-100 text-soil-600" title="Soil Type (CNN)">
        <p className="text-2xl font-extrabold text-leaf-900">{soil ? soil.name : '—'}</p>
        <p className="text-xs text-slate-400">MobileNetV2</p>
        <Confidence value={soil?.confidence} />
      </Tile>

      <Tile icon={Droplets} tint="bg-sky-100 text-sky-700" title="Irrigation">
        <p className="text-lg font-extrabold leading-snug text-leaf-900">{irrigation ? irrigation.advice : '—'}</p>
        {irrigation?.priority && (
          <div className="mt-2">
            <Badge tone={PRIORITY_TONE[String(irrigation.priority).toLowerCase()] || 'neutral'}>
              {capitalize(irrigation.priority)} priority
            </Badge>
          </div>
        )}
        {irrigation?.water !== null && irrigation?.water !== undefined && (
          <p className="mt-3 flex items-center gap-1.5 text-sm text-slate-600">
            <Gauge size={14} /> Suggested water: <b>{irrigation.water} mm</b>
          </p>
        )}
        {irrigation?.reason && <p className="mt-2 text-xs leading-relaxed text-slate-500">{irrigation.reason}</p>}
      </Tile>
    </div>
  );
}

import { useState } from 'react';
import { Pause, Play, Send, ChevronLeft, ChevronRight } from 'lucide-react';
import { PageHeader, Card, Loading, ErrorBox, Empty, Badge } from '../components/ui';
import StatCard from '../components/StatCard';
import TrendChart from '../components/TrendChart';
import { useLatestReading, useSensorHistory, useSensorPage } from '../hooks/useData';
import { api, errorMessage } from '../services/api';
import { METRICS, METRIC_BY_KEY, fmtDateTime, formatValue, statusOf } from '../utils/metrics';

const FORM_FIELDS = [
  { key: 'moisture', api: 'soil_moisture', step: 0.1 },
  { key: 'temperature', api: 'temperature', step: 0.1 },
  { key: 'humidity', api: 'humidity', step: 0.1 },
  { key: 'ph', api: 'ph', step: 0.01 },
  { key: 'nitrogen', api: 'nitrogen', step: 1 },
  { key: 'phosphorus', api: 'phosphorus', step: 1 },
  { key: 'potassium', api: 'potassium', step: 1 },
  { key: 'rainfall', api: 'rainfall', step: 0.1 },
];

function ManualForm({ onDone }) {
  const [vals, setVals] = useState({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const body = {};
      FORM_FIELDS.forEach((f) => {
        if (vals[f.key] !== undefined && vals[f.key] !== '') body[f.api] = Number(vals[f.key]);
      });
      await api.submitReading(body);
      setMsg({ ok: true, text: 'Reading saved.' });
      setVals({});
      onDone();
    } catch (err) {
      setMsg({ ok: false, text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {FORM_FIELDS.map((f) => {
          const m = METRIC_BY_KEY[f.key];
          return (
            <div key={f.key}>
              <label className="label">
                {m.label} {m.unit && <span className="normal-case text-slate-400">({m.unit})</span>}
              </label>
              <input
                className="input"
                type="number"
                step={f.step}
                placeholder={`${m.lo}–${m.hi}`}
                value={vals[f.key] ?? ''}
                onChange={(e) => setVals({ ...vals, [f.key]: e.target.value })}
              />
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex items-center gap-3">
        <button className="btn-primary" disabled={busy}>
          <Send size={16} /> {busy ? 'Saving…' : 'Submit reading'}
        </button>
        {msg && <span className={`text-sm font-semibold ${msg.ok ? 'text-leaf-700' : 'text-red-600'}`}>{msg.text}</span>}
      </div>
    </form>
  );
}

export default function Sensors() {
  const [live, setLive] = useState(true);
  const latest = useLatestReading(live ? 5000 : 0);
  const history = useSensorHistory(72);
  const [chartKey, setChartKey] = useState('moisture');
  const [page, setPage] = useState(1);
  const perPage = 10;
  const table = useSensorPage(page, perPage);
  const reading = latest.data;
  const totalPages = Math.max(1, Math.ceil((table.data?.total || 0) / perPage));

  return (
    <>
      <PageHeader
        title="Live Sensors"
        subtitle="Raspberry Pi soil probe readings, compared with agronomic optimal ranges"
        actions={
          <button className={live ? 'btn-primary' : 'btn-ghost'} onClick={() => setLive(!live)}>
            {live ? <Pause size={16} /> : <Play size={16} />} {live ? 'Live (5 s)' : 'Paused'}
          </button>
        }
      />

      {latest.error && <ErrorBox message={latest.error} onRetry={latest.reload} />}
      {latest.loading && !reading && <Loading label="Reading sensors…" />}

      {reading && (
        <>
          <p className="mb-3 text-xs text-slate-500">Reading time: {fmtDateTime(reading.timestamp)}</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {METRICS.map((m) => (
              <StatCard key={m.key} metric={m} value={reading[m.key]} />
            ))}
          </div>
        </>
      )}

      <Card
        className="mt-6"
        title="History Chart"
        subtitle="Last 72 readings"
        action={
          <select className="input !w-auto !py-1.5" value={chartKey} onChange={(e) => setChartKey(e.target.value)}>
            {METRICS.map((m) => (
              <option key={m.key} value={m.key}>
                {m.label}
              </option>
            ))}
          </select>
        }
      >
        {history.loading && !history.data ? <Loading /> : <TrendChart readings={history.data?.readings || []} metric={METRIC_BY_KEY[chartKey]} height={280} />}
      </Card>

      <Card className="mt-6" title="Manual Reading" subtitle="Submit values by hand (POST /api/sensors/reading) — leave blank to skip a field">
        <ManualForm
          onDone={() => {
            latest.reload();
            history.reload();
            table.reload();
          }}
        />
      </Card>

      <Card className="mt-6" title="Reading Log" subtitle={`${table.data?.total ?? 0} stored readings`}>
        {table.error && <ErrorBox message={table.error} onRetry={table.reload} />}
        {table.loading && !table.data ? (
          <Loading />
        ) : !table.data?.rows.length ? (
          <Empty message="No readings stored yet." />
        ) : (
          <>
            <div className="-mx-5 overflow-x-auto">
              <table className="w-full min-w-[720px]">
                <thead className="border-b border-slate-100">
                  <tr>
                    <th className="th">Time</th>
                    {METRICS.slice(0, 7).map((m) => (
                      <th key={m.key} className="th">
                        {m.label.replace(/ \(.\)/, '')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {table.data.rows.map((r, i) => (
                    <tr key={r.id ?? i} className="hover:bg-leaf-50/40">
                      <td className="td whitespace-nowrap">{fmtDateTime(r.timestamp)}</td>
                      {METRICS.slice(0, 7).map((m) => {
                        const st = statusOf(m, r[m.key]);
                        return (
                          <td key={m.key} className="td">
                            <span className={st === 'optimal' || st === 'unknown' ? '' : 'font-semibold text-amber-700'}>{formatValue(m, r[m.key])}</span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <Badge tone="neutral">
                Page {page} / {totalPages}
              </Badge>
              <div className="flex gap-2">
                <button className="btn-ghost !px-3" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  <ChevronLeft size={16} />
                </button>
                <button className="btn-ghost !px-3" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </Card>
    </>
  );
}

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { PageHeader, Card, Loading, ErrorBox, Empty, Badge } from '../components/ui';
import { useAnalysisHistory, usePredictionHistory } from '../hooks/useData';
import { capitalize, fmtDateTime } from '../utils/metrics';

const COLORS = ['#16a34a', '#0ea5e9', '#f97316', '#8b5cf6', '#db2777', '#d97706', '#14b8a6', '#64748b'];

function HistoryTable({ rows, onOpen }) {
  if (!rows.length) return <Empty message="No records yet." />;
  return (
    <div className="-mx-5 overflow-x-auto">
      <table className="w-full min-w-[680px]">
        <thead className="border-b border-slate-100">
          <tr>
            <th className="th">#</th>
            <th className="th">Time</th>
            <th className="th">Crop</th>
            <th className="th">Fertilizer</th>
            <th className="th">Soil</th>
            <th className="th">Irrigation</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {rows.map((a, i) => (
            <tr key={a.id ?? i} className={a.id ? 'cursor-pointer hover:bg-leaf-50/50' : ''} onClick={() => a.id && onOpen(a.id)}>
              <td className="td text-slate-400">{a.id ?? '—'}</td>
              <td className="td whitespace-nowrap">{fmtDateTime(a.timestamp)}</td>
              <td className="td">
                <span className="font-semibold text-leaf-800">{capitalize(a.crop?.name) || '—'}</span>
                {a.crop?.confidence != null && <span className="ml-2 text-xs text-slate-400">{a.crop.confidence.toFixed(0)}%</span>}
              </td>
              <td className="td">{a.fertilizer?.name || '—'}</td>
              <td className="td">{a.soil?.name || '—'}</td>
              <td className="td">
                <Badge tone={a.irrigation?.priority === 'high' ? 'high' : a.irrigation?.priority === 'medium' ? 'low' : 'optimal'}>
                  {a.irrigation?.advice || '—'}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CropMix({ rows }) {
  const data = useMemo(() => {
    const counts = {};
    rows.forEach((a) => {
      const n = a.crop?.name;
      if (n) counts[n] = (counts[n] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name: capitalize(name), count }))
      .sort((a, b) => b.count - a.count);
  }, [rows]);

  if (!data.length) return <Empty message="Run a few analyses to see crop trends." />;
  return (
    <div style={{ height: 240 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #dcfce7', fontSize: 12 }} />
          <Bar dataKey="count" name="Times recommended" radius={[8, 8, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={d.name} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function History() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('analyses');
  const analyses = useAnalysisHistory(50);
  const predictions = usePredictionHistory(50);
  const active = tab === 'analyses' ? analyses : predictions;
  const rows = active.data?.rows || [];

  return (
    <>
      <PageHeader title="History" subtitle="Every AI analysis and prediction stored by the backend" />

      <Card title="Most Recommended Crops" subtitle={`Based on ${analyses.data?.rows.length ?? 0} analyses`} className="mb-6">
        {analyses.loading && !analyses.data ? <Loading /> : <CropMix rows={analyses.data?.rows || []} />}
      </Card>

      <div className="mb-4 inline-flex rounded-xl border border-leaf-100 bg-white p-1">
        {[
          ['analyses', 'Analyses'],
          ['predictions', 'Predictions'],
        ].map(([k, label]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition ${tab === k ? 'bg-leaf-600 text-white' : 'text-slate-600 hover:text-leaf-800'}`}
          >
            {label}
          </button>
        ))}
      </div>

      <Card subtitle={`${active.data?.total ?? 0} records · click a row to open the full report`}>
        {active.error && <ErrorBox message={active.error} onRetry={active.reload} />}
        {active.loading && !active.data ? <Loading /> : <HistoryTable rows={rows} onOpen={(id) => navigate(`/analysis/${id}`)} />}
      </Card>
    </>
  );
}

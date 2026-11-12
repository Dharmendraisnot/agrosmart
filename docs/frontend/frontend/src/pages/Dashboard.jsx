import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Play, RefreshCw, ArrowRight } from 'lucide-react';
import { PageHeader, Card, Loading, ErrorBox, Empty } from '../components/ui';
import StatCard from '../components/StatCard';
import TrendChart from '../components/TrendChart';
import RecommendationGrid from '../components/RecommendationGrid';
import { useLatestReading, useSensorHistory, useLatestPrediction } from '../hooks/useData';
import { METRIC_BY_KEY, fmtDateTime } from '../utils/metrics';

const HEADLINE = ['moisture', 'temperature', 'humidity', 'ph'];
const NPK = ['nitrogen', 'phosphorus', 'potassium'];

export default function Dashboard() {
  const navigate = useNavigate();
  const latest = useLatestReading(10000);
  const history = useSensorHistory(48);
  const pred = useLatestPrediction();
  const [chartKey, setChartKey] = useState('moisture');

  const reading = latest.data;
  const refresh = () => {
    latest.reload();
    history.reload();
    pred.reload();
  };

  return (
    <>
      <PageHeader
        title="Farm Dashboard"
        subtitle={reading?.timestamp ? `Last reading: ${fmtDateTime(reading.timestamp)} · auto-refreshes every 10 s` : 'Real-time soil intelligence from your Raspberry Pi'}
        actions={
          <>
            <button className="btn-ghost" onClick={refresh}>
              <RefreshCw size={16} /> Refresh
            </button>
            <button className="btn-primary" onClick={() => navigate('/analysis', { state: { autorun: true } })}>
              <Play size={16} /> Run Analysis
            </button>
          </>
        }
      />

      {latest.error && <ErrorBox message={latest.error} onRetry={latest.reload} />}
      {latest.loading && !reading && <Loading label="Reading sensors…" />}

      {reading && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {HEADLINE.map((k) => (
              <StatCard key={k} metric={METRIC_BY_KEY[k]} value={reading[k]} />
            ))}
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <Card
              className="lg:col-span-2"
              title="Sensor Trend"
              subtitle="Last 48 readings"
              action={
                <select className="input !w-auto !py-1.5" value={chartKey} onChange={(e) => setChartKey(e.target.value)}>
                  {Object.values(METRIC_BY_KEY).map((m) => (
                    <option key={m.key} value={m.key}>
                      {m.label}
                    </option>
                  ))}
                </select>
              }
            >
              {history.loading && !history.data ? <Loading /> : <TrendChart readings={history.data?.readings || []} metric={METRIC_BY_KEY[chartKey]} />}
            </Card>

            <Card title="Soil Nutrients (NPK)" subtitle="Current levels vs. optimal band">
              <div className="space-y-4">
                {NPK.map((k) => (
                  <StatCard key={k} metric={METRIC_BY_KEY[k]} value={reading[k]} compact />
                ))}
              </div>
            </Card>
          </div>
        </>
      )}

      <div className="mt-8 mb-3 flex items-center justify-between">
        <h2 className="text-lg font-extrabold text-leaf-900">Latest AI Recommendation</h2>
        {pred.data?.id && (
          <Link to={`/analysis/${pred.data.id}`} className="flex items-center gap-1 text-sm font-semibold text-leaf-700 hover:underline">
            Full report <ArrowRight size={14} />
          </Link>
        )}
      </div>
      {pred.loading && !pred.data ? (
        <Loading label="Loading predictions…" />
      ) : pred.data ? (
        <>
          <p className="mb-3 text-xs text-slate-500">Generated {fmtDateTime(pred.data.timestamp)}</p>
          <RecommendationGrid analysis={pred.data} />
        </>
      ) : (
        <Card>
          <Empty message="No analysis yet — click “Run Analysis” to generate your first recommendation." />
        </Card>
      )}
    </>
  );
}

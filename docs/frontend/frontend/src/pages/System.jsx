import { ArrowDown, Cpu, Database, Server, Wifi } from 'lucide-react';
import { PageHeader, Card, Loading, ErrorBox, Badge } from '../components/ui';
import { useHealth } from '../hooks/useData';
import { useDemoMode } from '../services/status';

const MODELS = [
  { name: 'Crop Recommendation', algo: 'Random Forest (100 trees)', data: 'Kaggle / AgroSmart', file: 'crop_rf_v1.pkl' },
  { name: 'Fertilizer Recommendation', algo: 'Decision Tree (prototype)', data: 'Kaggle', file: 'fertilizer_dt_prototype.pkl' },
  { name: 'Soil Classification', algo: 'MobileNetV2 CNN', data: 'Soil image dataset', file: '.h5' },
  { name: 'Irrigation Advice', algo: 'Rule engine', data: '—', file: 'recommendation_service.py' },
];

const ENDPOINTS = [
  ['GET', '/api/health', 'System health + sensor mode'],
  ['GET', '/api/sensors/latest', 'Fresh sensor reading'],
  ['GET', '/api/sensors/history', 'Paginated sensor history'],
  ['POST', '/api/sensors/reading', 'Manual sensor submit'],
  ['POST', '/api/analysis/run', 'Run full AI pipeline'],
  ['GET', '/api/analysis/<id>', 'Get one analysis'],
  ['GET', '/api/analysis/history', 'Analysis history'],
  ['GET', '/api/predictions/latest', 'Latest predictions'],
  ['GET', '/api/predictions/history', 'Prediction history'],
  ['POST', '/api/images/upload', 'Upload soil image (CNN)'],
  ['GET', '/api/images/<filename>', 'Serve uploaded image'],
];

const PIPE = [
  { icon: Cpu, title: 'Sensors', sub: 'Simulator or Raspberry Pi 5' },
  { icon: Database, title: 'sensor_service → SQLite', sub: 'Stores every reading' },
  { icon: Server, title: 'analysis_service', sub: 'RF · Decision Tree · MobileNetV2 · rules' },
  { icon: Wifi, title: 'Flask REST API → React', sub: 'This dashboard' },
];

export default function System() {
  const { data: health, loading, error, reload } = useHealth();
  const demo = useDemoMode();

  return (
    <>
      <PageHeader title="System" subtitle="Backend health, models and architecture" />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Backend Health" className="lg:col-span-1">
          {error && <ErrorBox message={error} onRetry={reload} />}
          {loading && !health ? (
            <Loading />
          ) : health ? (
            <dl className="space-y-3 text-sm">
              {[
                ['API status', <Badge key="s" tone={health.status === 'ok' || health.status === 'healthy' ? 'optimal' : 'low'}>{health.status}</Badge>],
                ['Sensor mode', <Badge key="m" tone="info">{health.sensorMode}</Badge>],
                ['Data source', <Badge key="d" tone={demo ? 'low' : 'optimal'}>{demo ? 'Demo data' : 'Live backend'}</Badge>],
                ...(health.database ? [['Database', String(health.database)]] : []),
                ...(health.version ? [['Version', String(health.version)]] : []),
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between border-b border-slate-50 pb-2">
                  <dt className="text-slate-500">{k}</dt>
                  <dd className="font-semibold text-slate-800">{v}</dd>
                </div>
              ))}
              {health.models && typeof health.models === 'object' && (
                <div className="pt-1">
                  <dt className="mb-2 text-slate-500">Models loaded</dt>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(health.models).map(([k, v]) => (
                      <Badge key={k} tone={v ? 'optimal' : 'high'}>
                        {k}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </dl>
          ) : null}
        </Card>

        <Card title="Data Flow" subtitle="From soil probe to recommendation" className="lg:col-span-2">
          <div className="flex flex-col items-stretch gap-2">
            {PIPE.map(({ icon: Icon, title, sub }, i) => (
              <div key={title}>
                <div className="flex items-center gap-4 rounded-xl border border-leaf-100 bg-leaf-50/50 px-4 py-3">
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-600 text-white">
                    <Icon size={18} />
                  </span>
                  <div>
                    <p className="font-bold text-leaf-900">{title}</p>
                    <p className="text-xs text-slate-500">{sub}</p>
                  </div>
                </div>
                {i < PIPE.length - 1 && <ArrowDown size={16} className="mx-auto mt-2 text-leaf-400" />}
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Machine Learning Models" subtitle="Accuracy is computed by evaluate_models.py after training and is never hard-coded" className="mt-6">
        <div className="-mx-5 overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead className="border-b border-slate-100">
              <tr>
                <th className="th">Model</th>
                <th className="th">Algorithm</th>
                <th className="th">Dataset</th>
                <th className="th">Artifact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {MODELS.map((m) => (
                <tr key={m.name}>
                  <td className="td font-semibold text-leaf-900">{m.name}</td>
                  <td className="td">{m.algo}</td>
                  <td className="td">{m.data}</td>
                  <td className="td font-mono text-xs text-slate-500">{m.file}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="REST API" subtitle="Endpoints this dashboard talks to (proxied from :3000 to :5000)" className="mt-6">
        <ul className="divide-y divide-slate-50">
          {ENDPOINTS.map(([method, path, desc]) => (
            <li key={method + path} className="flex flex-wrap items-center gap-3 py-2.5 text-sm">
              <span className={`w-14 rounded-md px-2 py-0.5 text-center text-xs font-bold ${method === 'GET' ? 'bg-sky-100 text-sky-800' : 'bg-leaf-100 text-leaf-800'}`}>{method}</span>
              <code className="font-mono text-xs text-slate-700">{path}</code>
              <span className="text-slate-500">{desc}</span>
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}

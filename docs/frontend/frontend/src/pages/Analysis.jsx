import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { CheckCircle2, Loader2, Play } from 'lucide-react';
import { PageHeader, Card, Loading, ErrorBox } from '../components/ui';
import RecommendationGrid from '../components/RecommendationGrid';
import StatCard from '../components/StatCard';
import { api, errorMessage } from '../services/api';
import { normalizeAnalysis } from '../utils/normalize';
import { METRIC_BY_KEY, fmtDateTime } from '../utils/metrics';

const STEPS = [
  'Reading latest soil sensors',
  'Classifying soil type (CNN)',
  'Predicting best crop (Random Forest)',
  'Recommending fertilizer (Decision Tree)',
  'Applying irrigation rules',
];

const SNAPSHOT = ['moisture', 'temperature', 'humidity', 'ph', 'nitrogen', 'phosphorus', 'potassium', 'rainfall'];

function PipelineProgress({ step }) {
  return (
    <ol className="space-y-3">
      {STEPS.map((label, i) => {
        const done = i < step;
        const active = i === step;
        return (
          <li key={label} className="flex items-center gap-3 text-sm">
            {done ? (
              <CheckCircle2 size={18} className="text-leaf-600" />
            ) : active ? (
              <Loader2 size={18} className="animate-spin text-leaf-600" />
            ) : (
              <span className="h-[18px] w-[18px] rounded-full border-2 border-slate-200" />
            )}
            <span className={done || active ? 'font-semibold text-slate-800' : 'text-slate-400'}>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}

export default function Analysis() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [loadingOne, setLoadingOne] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(0);
  const autoRan = useRef(false);

  // Animate the pipeline steps while the request is in flight.
  useEffect(() => {
    if (!running) return undefined;
    setStep(0);
    const t = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 700);
    return () => clearInterval(t);
  }, [running]);

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = normalizeAnalysis(await api.runAnalysis());
      setStep(STEPS.length);
      await new Promise((r) => setTimeout(r, 350));
      setResult(res);
      if (res?.id) navigate(`/analysis/${res.id}`, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setRunning(false);
    }
  };

  // Open a saved analysis by id.
  useEffect(() => {
    if (!id) return undefined;
    let alive = true;
    setLoadingOne(true);
    setError(null);
    api
      .getAnalysis(id)
      .then((r) => alive && setResult(normalizeAnalysis(r)))
      .catch((e) => alive && setError(errorMessage(e)))
      .finally(() => alive && setLoadingOne(false));
    return () => {
      alive = false;
    };
  }, [id]);

  // Triggered from the dashboard "Run Analysis" button.
  useEffect(() => {
    if (location.state?.autorun && !autoRan.current && !id) {
      autoRan.current = true;
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <PageHeader
        title="AI Analysis"
        subtitle="Runs the full pipeline on the latest sensor reading: soil type, crop, fertilizer and irrigation"
        actions={
          <button className="btn-primary" onClick={run} disabled={running}>
            <Play size={16} /> {running ? 'Running…' : id ? 'Run new analysis' : 'Run full analysis'}
          </button>
        }
      />

      {error && <ErrorBox message={error} onRetry={run} />}

      {running && (
        <Card title="Running AI pipeline" subtitle="This usually takes a few seconds">
          <PipelineProgress step={step} />
        </Card>
      )}

      {loadingOne && !running && <Loading label="Loading analysis…" />}

      {!running && !loadingOne && !result && !error && (
        <Card>
          <div className="py-8 text-center">
            <p className="text-lg font-bold text-leaf-900">Ready when you are</p>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
              The analysis uses the most recent sensor reading and returns crop, fertilizer, soil type and irrigation advice in one go.
            </p>
            <button className="btn-primary mt-5" onClick={run}>
              <Play size={16} /> Run full analysis
            </button>
          </div>
        </Card>
      )}

      {!running && result && (
        <div className="space-y-6">
          <p className="text-xs text-slate-500">
            Analysis {result.id ? `#${result.id} · ` : ''}
            {fmtDateTime(result.timestamp)}
          </p>
          <RecommendationGrid analysis={result} />

          {result.reading && (
            <Card title="Sensor snapshot used" subtitle="Input values given to the models">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {SNAPSHOT.map((k) => (
                  <StatCard key={k} metric={METRIC_BY_KEY[k]} value={result.reading[k]} compact />
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </>
  );
}

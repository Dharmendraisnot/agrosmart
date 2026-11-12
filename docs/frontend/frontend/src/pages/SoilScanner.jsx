import { useEffect, useRef, useState } from 'react';
import { ImagePlus, Loader2, ScanSearch, Trash2 } from 'lucide-react';
import { PageHeader, Card, ErrorBox, Badge } from '../components/ui';
import { api, errorMessage } from '../services/api';
import { normalizeUpload } from '../utils/normalize';

const MAX_MB = 8;

export default function SoilScanner() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  const choose = (f) => {
    setError(null);
    setResult(null);
    if (!f) return;
    if (!f.type.startsWith('image/')) return setError('Please choose an image file (JPG, PNG, WebP).');
    if (f.size > MAX_MB * 1024 * 1024) return setError(`Image is larger than ${MAX_MB} MB.`);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const clear = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const classify = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setResult(normalizeUpload(await api.uploadImage(file)));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const soil = result?.soil;

  return (
    <>
      <PageHeader title="Soil Scanner" subtitle="Upload a photo of your soil — the MobileNetV2 CNN identifies the soil type" />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="1. Choose a soil image">
          {!preview ? (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDrag(true);
              }}
              onDragLeave={() => setDrag(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDrag(false);
                choose(e.dataTransfer.files?.[0]);
              }}
              onClick={() => inputRef.current?.click()}
              className={`flex h-72 cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed text-center transition ${
                drag ? 'border-leaf-500 bg-leaf-50' : 'border-leaf-200 bg-soil-50 hover:bg-leaf-50/60'
              }`}
            >
              <ImagePlus size={36} className="text-leaf-600" />
              <p className="font-semibold text-leaf-900">Drag &amp; drop or click to upload</p>
              <p className="text-xs text-slate-500">JPG / PNG / WebP · up to {MAX_MB} MB</p>
            </div>
          ) : (
            <div className="relative overflow-hidden rounded-2xl border border-leaf-100">
              <img src={preview} alt="Soil preview" className="h-72 w-full object-cover" />
              <button onClick={clear} className="absolute right-3 top-3 rounded-full bg-white/90 p-2 text-red-600 shadow hover:bg-white" aria-label="Remove image">
                <Trash2 size={16} />
              </button>
            </div>
          )}
          <input ref={inputRef} type="file" accept="image/*" hidden onChange={(e) => choose(e.target.files?.[0])} />

          {error && (
            <div className="mt-4">
              <ErrorBox message={error} />
            </div>
          )}

          <button className="btn-primary mt-4 w-full" disabled={!file || busy} onClick={classify}>
            {busy ? <Loader2 size={16} className="animate-spin" /> : <ScanSearch size={16} />} {busy ? 'Analyzing image…' : 'Classify soil'}
          </button>
        </Card>

        <Card title="2. Result">
          {!soil ? (
            <div className="flex h-72 flex-col items-center justify-center gap-2 text-center text-sm text-slate-400">
              <ScanSearch size={32} />
              Upload an image and press “Classify soil”.
            </div>
          ) : (
            <div className="fade-up">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Detected soil type</p>
              <p className="mt-1 text-4xl font-extrabold text-leaf-900">{soil.name}</p>
              {soil.confidence !== null && (
                <div className="mt-2">
                  <Badge tone={soil.confidence >= 70 ? 'optimal' : 'low'}>{soil.confidence.toFixed(1)}% confidence</Badge>
                  {soil.confidence < 70 && <p className="mt-2 text-xs text-amber-700">Low confidence — try a clearer, well-lit close-up of bare soil.</p>}
                </div>
              )}

              {soil.alternatives?.length > 0 && (
                <div className="mt-6">
                  <p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Class probabilities</p>
                  <ul className="space-y-3">
                    {soil.alternatives.map((a) => (
                      <li key={a.name}>
                        <div className="mb-1 flex justify-between text-sm">
                          <span className="font-semibold text-slate-700">{a.name}</span>
                          <span className="text-slate-500">{(a.confidence ?? 0).toFixed(1)}%</span>
                        </div>
                        <div className="h-2.5 rounded-full bg-slate-100">
                          <div
                            className={`h-2.5 rounded-full ${a.name === soil.name ? 'bg-leaf-500' : 'bg-soil-400/60'}`}
                            style={{ width: `${Math.min(100, a.confidence ?? 0)}%`, transition: 'width .8s ease' }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.filename && <p className="mt-6 text-xs text-slate-400">Saved as {result.filename}</p>}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

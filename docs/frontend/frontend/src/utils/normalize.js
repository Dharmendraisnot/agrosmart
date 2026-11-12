// Maps backend responses (or demo data) into one stable shape for the UI.
// Backend key names can differ slightly, so each field accepts a few aliases.

const pick = (o, keys, d = null) => {
  if (!o || typeof o !== 'object') return d;
  for (const k of keys) if (o[k] !== undefined && o[k] !== null) return o[k];
  return d;
};

const num = (v) => {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};

const pct = (v) => {
  const n = num(v);
  if (n === null) return null;
  return n <= 1 ? n * 100 : n;
};

export function unwrap(payload) {
  if (payload && typeof payload === 'object' && !Array.isArray(payload) && payload.data !== undefined && payload.data !== null) {
    return payload.data;
  }
  return payload;
}

export function toList(payload) {
  const p = unwrap(payload);
  if (Array.isArray(p)) return { items: p, total: p.length };
  const items = pick(p, ['items', 'results', 'readings', 'analyses', 'predictions', 'history', 'data'], []);
  return { items: Array.isArray(items) ? items : [], total: num(pick(p, ['total', 'count'])) ?? (Array.isArray(items) ? items.length : 0) };
}

export function normalizeReading(raw) {
  const r = unwrap(raw);
  if (!r || typeof r !== 'object') return null;
  const src = pick(r, ['reading', 'sensor_reading', 'sensors'], r);
  return {
    id: pick(src, ['id', 'reading_id']),
    timestamp: pick(src, ['timestamp', 'created_at', 'recorded_at', 'time']),
    moisture: num(pick(src, ['soil_moisture', 'moisture'])),
    temperature: num(pick(src, ['temperature', 'soil_temperature', 'temp'])),
    humidity: num(pick(src, ['humidity', 'air_humidity'])),
    ph: num(pick(src, ['ph', 'soil_ph', 'pH'])),
    nitrogen: num(pick(src, ['nitrogen', 'N', 'n'])),
    phosphorus: num(pick(src, ['phosphorus', 'P', 'p'])),
    potassium: num(pick(src, ['potassium', 'K', 'k'])),
    rainfall: num(pick(src, ['rainfall', 'rain'])),
  };
}

function normalizeAlternatives(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw
      .map((x) => ({
        name: String(pick(x, ['crop', 'name', 'label', 'class', 'fertilizer'], '')),
        confidence: pct(pick(x, ['probability', 'confidence', 'score'])),
      }))
      .filter((x) => x.name);
  }
  if (typeof raw === 'object') {
    return Object.entries(raw)
      .map(([name, v]) => ({ name, confidence: pct(v) }))
      .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
  }
  return [];
}

function normalizePrediction(raw) {
  if (raw === null || raw === undefined) return null;
  if (typeof raw === 'string') return { name: raw, confidence: null, alternatives: [], model: null };
  return {
    name: String(pick(raw, ['name', 'label', 'crop', 'fertilizer', 'recommendation', 'prediction', 'soil_type', 'class'], '—')),
    confidence: pct(pick(raw, ['confidence', 'probability', 'score'])),
    alternatives: normalizeAlternatives(pick(raw, ['top_k', 'top3', 'top_predictions', 'alternatives', 'probabilities'])),
    model: pick(raw, ['model', 'model_label', 'model_version']),
  };
}

function normalizeIrrigation(raw) {
  if (raw === null || raw === undefined) return null;
  if (typeof raw === 'string') return { advice: raw, priority: null, reason: null, water: null };
  return {
    advice: String(pick(raw, ['advice', 'recommendation', 'action', 'message'], '—')),
    priority: pick(raw, ['priority', 'urgency', 'level']),
    reason: pick(raw, ['reason', 'details', 'explanation', 'note']),
    water: num(pick(raw, ['water_mm', 'amount', 'volume_l', 'litres'])),
  };
}

export function normalizeAnalysis(raw) {
  const a = unwrap(raw);
  if (!a || typeof a !== 'object') return null;
  return {
    id: pick(a, ['id', 'analysis_id']),
    timestamp: pick(a, ['timestamp', 'created_at', 'time']),
    reading: normalizeReading(pick(a, ['reading', 'sensor_reading', 'sensors'], null)),
    crop: normalizePrediction(pick(a, ['crop', 'crop_recommendation', 'crop_prediction'])),
    fertilizer: normalizePrediction(pick(a, ['fertilizer', 'fertilizer_recommendation', 'fertilizer_prediction'])),
    soil: normalizePrediction(pick(a, ['soil_type', 'soil', 'soil_classification'])),
    irrigation: normalizeIrrigation(pick(a, ['irrigation', 'irrigation_advice'])),
  };
}

export function normalizeUpload(raw) {
  const u = unwrap(raw);
  if (!u || typeof u !== 'object') return null;
  const cls = normalizePrediction(pick(u, ['prediction', 'soil', 'result'], null)) || {
    name: String(pick(u, ['soil_type', 'label', 'class', 'prediction'], '—')),
    confidence: pct(pick(u, ['confidence', 'probability', 'score'])),
    alternatives: [],
  };
  const probs = normalizeAlternatives(pick(u, ['probabilities', 'class_probabilities', 'top_k', 'scores']));
  return {
    filename: pick(u, ['filename', 'file_name', 'image']),
    soil: { ...cls, alternatives: probs.length ? probs : cls.alternatives },
  };
}

export function normalizeHealth(raw) {
  const h = unwrap(raw) || {};
  return {
    status: String(pick(h, ['status'], 'unknown')),
    sensorMode: String(pick(h, ['sensor_mode', 'mode', 'SENSOR_MODE'], '—')),
    version: pick(h, ['version']),
    database: pick(h, ['database', 'db']),
    models: pick(h, ['models_loaded', 'models'], null),
  };
}

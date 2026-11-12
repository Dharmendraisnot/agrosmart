// Demo data used only when the Flask backend cannot be reached.
// Shapes intentionally mimic what the real API is expected to return;
// utils/normalize.js maps both mock and real responses to one UI shape.

const rnd = (a, b) => a + Math.random() * (b - a);
const r1 = (n) => Math.round(n * 10) / 10;

export const CROPS = ['rice', 'maize', 'cotton', 'jute', 'chickpea', 'banana', 'mango', 'coffee', 'lentil', 'watermelon'];
export const FERTILIZERS = ['Urea', 'DAP', '14-35-14', '28-28', '17-17-17', '20-20', '10-26-26'];
export const SOIL_TYPES = ['Alluvial', 'Black', 'Clay', 'Red'];

let counter = 1000;

export function makeReading(minutesAgo = 0, i = 0) {
  const t = new Date(Date.now() - minutesAgo * 60000);
  return {
    id: counter++,
    timestamp: t.toISOString(),
    soil_moisture: r1(42 + 12 * Math.sin(i / 6) + rnd(-2, 2)),
    temperature: r1(27 + 4 * Math.sin(i / 8) + rnd(-0.5, 0.5)),
    humidity: r1(64 + 9 * Math.cos(i / 7) + rnd(-2, 2)),
    ph: Math.round((6.6 + rnd(-0.2, 0.2)) * 100) / 100,
    nitrogen: Math.round(78 + rnd(-6, 6)),
    phosphorus: Math.round(48 + rnd(-4, 4)),
    potassium: Math.round(44 + rnd(-4, 4)),
    rainfall: r1(rnd(85, 125)),
  };
}

const sensorHistory = Array.from({ length: 72 }, (_, i) => makeReading((71 - i) * 20, i)).reverse(); // newest first
let tick = 72;

function irrigationFor(moisture) {
  if (moisture < 30)
    return { advice: 'Irrigate now', priority: 'high', reason: 'Soil moisture is below the safe range for most crops.', water_mm: 25 };
  if (moisture < 42)
    return { advice: 'Irrigate within 24 hours', priority: 'medium', reason: 'Moisture is trending low; a light irrigation will keep the root zone comfortable.', water_mm: 12 };
  return { advice: 'No irrigation needed', priority: 'low', reason: 'Moisture is within the optimal band.', water_mm: 0 };
}

function pickCrops(r) {
  const wet = r.soil_moisture > 48;
  const warm = r.temperature > 26;
  const order = wet ? ['rice', 'jute', 'banana'] : warm ? ['maize', 'cotton', 'mango'] : ['chickpea', 'lentil', 'maize'];
  const p1 = rnd(0.62, 0.86);
  const p2 = rnd(0.07, 1 - p1 - 0.05);
  const p3 = Math.max(0.02, 1 - p1 - p2 - 0.03);
  return [
    { crop: order[0], probability: p1 },
    { crop: order[1], probability: p2 },
    { crop: order[2], probability: p3 },
  ];
}

const analyses = [];
export function makeAnalysis(reading) {
  const crops = pickCrops(reading);
  const soil = SOIL_TYPES[Math.floor(Math.random() * SOIL_TYPES.length)];
  const fert = FERTILIZERS[Math.floor(Math.random() * FERTILIZERS.length)];
  const a = {
    id: counter++,
    timestamp: new Date().toISOString(),
    reading,
    crop: { name: crops[0].crop, confidence: crops[0].probability, top_k: crops },
    fertilizer: { name: fert, confidence: rnd(0.7, 0.93), model: 'prototype_kaggle_v1.0' },
    soil_type: { label: soil, confidence: rnd(0.72, 0.95) },
    irrigation: irrigationFor(reading.soil_moisture),
  };
  analyses.unshift(a);
  return a;
}
// seed a few past analyses
for (let i = 0; i < 6; i++) {
  const rd = makeReading((i + 1) * 180, i * 3);
  const a = makeAnalysis(rd);
  a.timestamp = rd.timestamp;
}

const page = (list, { page: p = 1, per_page = 10, limit } = {}) => {
  const size = Number(limit || per_page);
  const start = (Number(p) - 1) * size;
  return { items: list.slice(start, start + size), total: list.length, page: Number(p), per_page: size };
};

export const mock = {
  health: () => ({ status: 'ok', sensor_mode: 'simulator', version: 'demo', database: 'sqlite', models_loaded: { crop: true, fertilizer: true, soil_cnn: true } }),
  latestSensor: () => {
    const r = makeReading(0, tick++);
    sensorHistory.unshift(r);
    return r;
  },
  sensorHistory: (params) => page(sensorHistory, params),
  submitReading: (body) => {
    const r = { ...makeReading(0, tick++), ...body };
    sensorHistory.unshift(r);
    return r;
  },
  runAnalysis: () => makeAnalysis(sensorHistory[0] || makeReading()),
  getAnalysis: (id) => analyses.find((a) => String(a.id) === String(id)) || analyses[0],
  analysisHistory: (params) => page(analyses, params),
  latestPredictions: () => analyses[0],
  predictionHistory: (params) => page(analyses, params),
  uploadImage: () => {
    const raw = SOIL_TYPES.map(() => Math.random() ** 2.2);
    const sum = raw.reduce((a, b) => a + b, 0);
    const probs = Object.fromEntries(SOIL_TYPES.map((s, i) => [s, raw[i] / sum]));
    const best = Object.entries(probs).sort((a, b) => b[1] - a[1])[0];
    return { filename: `demo_${Date.now()}.jpg`, soil_type: best[0], confidence: best[1], probabilities: probs };
  },
};

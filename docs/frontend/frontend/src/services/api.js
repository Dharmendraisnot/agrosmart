import axios from 'axios';
import { mock } from './mockData';
import { setDemo } from './status';

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 20000,
});

const FORCE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// True when the backend itself is down: no response at all, a gateway error,
// or the empty 500 the Vite dev proxy returns on ECONNREFUSED.
// A real Flask error (JSON/HTML body) is NOT treated as "down".
function backendUnreachable(err) {
  const res = err.response;
  if (!res) return true;
  if ([502, 503, 504].includes(res.status)) return true;
  if (res.status === 500) {
    const body = res.data;
    return body === '' || body === null || body === undefined;
  }
  return false;
}

// Try the real backend; if it is unreachable, fall back to demo data
// so the UI is still presentable.
async function call(realFn, mockFn) {
  if (FORCE_MOCK) {
    setDemo(true);
    return mockFn();
  }
  try {
    const res = await realFn();
    setDemo(false);
    return res.data;
  } catch (err) {
    if (backendUnreachable(err)) {
      setDemo(true);
      return mockFn();
    }
    throw err;
  }
}

export const api = {
  health: () => call(() => http.get('/health'), mock.health),
  latestSensor: () => call(() => http.get('/sensors/latest'), mock.latestSensor),
  sensorHistory: (params) => call(() => http.get('/sensors/history', { params }), () => mock.sensorHistory(params)),
  submitReading: (body) => call(() => http.post('/sensors/reading', body), () => mock.submitReading(body)),
  runAnalysis: (body = {}) => call(() => http.post('/analysis/run', body), mock.runAnalysis),
  getAnalysis: (id) => call(() => http.get(`/analysis/${id}`), () => mock.getAnalysis(id)),
  analysisHistory: (params) => call(() => http.get('/analysis/history', { params }), () => mock.analysisHistory(params)),
  latestPredictions: () => call(() => http.get('/predictions/latest'), mock.latestPredictions),
  predictionHistory: (params) => call(() => http.get('/predictions/history', { params }), () => mock.predictionHistory(params)),
  uploadImage: (file) => {
    const form = new FormData();
    form.append('image', file);
    form.append('file', file); // backend field name may be either
    return call(() => http.post('/images/upload', form), mock.uploadImage);
  },
  imageUrl: (filename) => `${http.defaults.baseURL}/images/${encodeURIComponent(filename)}`,
};

export function errorMessage(err) {
  return (
    err?.response?.data?.error ||
    err?.response?.data?.message ||
    err?.message ||
    'Something went wrong'
  );
}

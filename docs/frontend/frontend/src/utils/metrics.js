import { Droplets, Thermometer, Wind, FlaskConical, Leaf, CloudRain } from 'lucide-react';

// Display scale + "optimal band" for each sensor parameter.
export const METRICS = [
  { key: 'moisture', label: 'Soil Moisture', unit: '%', min: 0, max: 100, lo: 30, hi: 60, icon: Droplets, color: '#0ea5e9' },
  { key: 'temperature', label: 'Temperature', unit: '°C', min: 0, max: 50, lo: 15, hi: 35, icon: Thermometer, color: '#f97316' },
  { key: 'humidity', label: 'Humidity', unit: '%', min: 0, max: 100, lo: 40, hi: 80, icon: Wind, color: '#06b6d4' },
  { key: 'ph', label: 'Soil pH', unit: '', min: 3, max: 10, lo: 6, hi: 7.5, icon: FlaskConical, color: '#8b5cf6', decimals: 2 },
  { key: 'nitrogen', label: 'Nitrogen (N)', unit: 'kg/ha', min: 0, max: 140, lo: 40, hi: 120, icon: Leaf, color: '#16a34a' },
  { key: 'phosphorus', label: 'Phosphorus (P)', unit: 'kg/ha', min: 0, max: 145, lo: 25, hi: 100, icon: Leaf, color: '#d97706' },
  { key: 'potassium', label: 'Potassium (K)', unit: 'kg/ha', min: 0, max: 205, lo: 30, hi: 150, icon: Leaf, color: '#db2777' },
  { key: 'rainfall', label: 'Rainfall', unit: 'mm', min: 0, max: 300, lo: 50, hi: 250, icon: CloudRain, color: '#3b82f6' },
];

export const METRIC_BY_KEY = Object.fromEntries(METRICS.map((m) => [m.key, m]));

export function statusOf(metric, value) {
  if (value === null || value === undefined) return 'unknown';
  if (value < metric.lo) return 'low';
  if (value > metric.hi) return 'high';
  return 'optimal';
}

export function formatValue(metric, value) {
  if (value === null || value === undefined) return '—';
  const d = metric.decimals ?? (Number.isInteger(value) ? 0 : 1);
  return Number(value).toFixed(d);
}

export const fmtTime = (ts) => {
  if (!ts) return '';
  const d = new Date(ts);
  return isNaN(d) ? String(ts) : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export const fmtDateTime = (ts) => {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d)
    ? String(ts)
    : d.toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

export const capitalize = (s) => (s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : s);

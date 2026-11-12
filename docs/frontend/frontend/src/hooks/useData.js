import { api } from '../services/api';
import { useAsync } from './useAsync';
import { normalizeReading, normalizeAnalysis, normalizeHealth, toList } from '../utils/normalize';

export function useHealth() {
  const s = useAsync(async () => normalizeHealth(await api.health()), [], { poll: 30000 });
  return s;
}

export function useLatestReading(poll = 0) {
  return useAsync(async () => normalizeReading(await api.latestSensor()), [], { poll });
}

// Oldest -> newest, ready for charts.
export function useSensorHistory(limit = 48) {
  return useAsync(async () => {
    const { items, total } = toList(await api.sensorHistory({ limit, per_page: limit, page: 1 }));
    const readings = items.map(normalizeReading).filter(Boolean);
    readings.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    return { readings, total };
  }, [limit]);
}

export function useSensorPage(page, perPage = 10) {
  return useAsync(async () => {
    const { items, total } = toList(await api.sensorHistory({ page, per_page: perPage, limit: perPage }));
    return { rows: items.map(normalizeReading).filter(Boolean), total };
  }, [page, perPage]);
}

export function useLatestPrediction() {
  return useAsync(async () => normalizeAnalysis(await api.latestPredictions()), []);
}

export function useAnalysisHistory(limit = 25) {
  return useAsync(async () => {
    const { items, total } = toList(await api.analysisHistory({ limit, per_page: limit, page: 1 }));
    return { rows: items.map(normalizeAnalysis).filter(Boolean), total };
  }, [limit]);
}

export function usePredictionHistory(limit = 25) {
  return useAsync(async () => {
    const { items, total } = toList(await api.predictionHistory({ limit, per_page: limit, page: 1 }));
    return { rows: items.map(normalizeAnalysis).filter(Boolean), total };
  }, [limit]);
}

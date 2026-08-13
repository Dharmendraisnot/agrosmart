/**
 * api.js — Axios instance + all API call functions.
 *
 * All backend communication goes through this file.
 * Base URL is read from the Vite proxy (relative /api) in development,
 * or from VITE_API_BASE_URL in production builds.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = () => api.get('/health')

// ── Sensors ───────────────────────────────────────────────────────────────────
export const getLatestReading = () => api.get('/sensors/latest')

export const getSensorHistory = (page = 1, perPage = 50) =>
  api.get('/sensors/history', { params: { page, per_page: perPage } })

export const postManualReading = (data) => api.post('/sensors/reading', data)

// ── Analysis ──────────────────────────────────────────────────────────────────
export const runAnalysis = (readingId = null) =>
  api.post('/analysis/run', readingId ? { reading_id: readingId } : {})

export const getAnalysis = (id) => api.get(`/analysis/${id}`)

export const getAnalysisHistory = (page = 1, perPage = 20) =>
  api.get('/analysis/history', { params: { page, per_page: perPage } })

// ── Predictions ───────────────────────────────────────────────────────────────
export const getLatestPredictions = () => api.get('/predictions/latest')

export const getPrediction = (id) => api.get(`/predictions/${id}`)

export const getPredictionHistory = (page = 1, perPage = 20, type = null) =>
  api.get('/predictions/history', {
    params: { page, per_page: perPage, ...(type ? { prediction_type: type } : {}) },
  })

// ── Images ────────────────────────────────────────────────────────────────────
export const uploadImage = (file) => {
  const form = new FormData()
  form.append('image', file)
  return api.post('/images/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getImageUrl = (filename) => `${BASE_URL}/images/${filename}`

export default api

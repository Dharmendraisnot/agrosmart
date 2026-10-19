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
// ── Analysis ──────────────────────────────────────────────────────────────────
export const runAnalysis = (params = {}) => {
  // Support legacy signature runAnalysis(123)
  if (typeof params === 'number') {
    return api.post('/analysis/run', { reading_id: params })
  }
  const {
    reading_id = null,
    readingId = null,
    sensor_data = null,
    sensorData = null,
    soil_type = null,
    soilType = null,
    confirmed_soil_texture = null,
    confirmedSoilTexture = null,
    image_path = null,
    imagePath = null,
    notes = null,
  } = params || {}

  const payload = {}
  const rid = reading_id ?? readingId
  if (rid) payload.reading_id = rid

  const sdata = sensor_data ?? sensorData
  if (sdata) payload.sensor_data = sdata

  const stype = soil_type ?? soilType
  if (stype) payload.soil_type = stype

  const ctexture = confirmed_soil_texture ?? confirmedSoilTexture
  if (ctexture) payload.confirmed_soil_texture = ctexture

  const ipath = image_path ?? imagePath
  if (ipath) payload.image_path = ipath

  if (notes) payload.notes = notes

  return api.post('/analysis/run', payload)
}

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
export const uploadImage = (file, options = {}) => {
  const form = new FormData()
  form.append('image', file)
  if (options.runAnalysis || options.run_analysis) {
    form.append('run_analysis', 'true')
  }
  const texture = options.confirmedSoilTexture || options.confirmed_soil_texture
  if (texture) {
    form.append('confirmed_soil_texture', texture)
  }
  return api.post('/images/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getImageUrl = (filename) => `${BASE_URL}/images/${filename}`

export default api

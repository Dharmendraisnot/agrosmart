/**
 * AnalysisForm.jsx — Manual soil & weather input form with preset loader,
 * validation, confirmed texture selection for Alluvial soils, and execution controls.
 */
import { useState, useEffect } from 'react'
import { FlaskConical, Loader2, Sparkles, Sliders, Cpu, HelpCircle, AlertCircle } from 'lucide-react'
import { SOIL_PRESETS, VALID_SOIL_TEXTURES } from '../../utils/constants'

const DEFAULT_VALUES = {
  nitrogen: 50,
  phosphorus: 30,
  potassium: 160,
  ph: 6.5,
  soil_temperature: 24.0,
  air_temperature: 26.0,
  air_humidity: 60.0,
  rainfall: 100.0,    // Meteorological precipitation in mm
  moisture: 48.0,    // Volumetric soil water content in %
}

export default function AnalysisForm({
  onRun,
  loading,
  detectedSoilType = null,
  imagePath = null,
}) {
  const [mode, setMode] = useState('manual') // 'manual' | 'simulator'
  const [formValues, setFormValues] = useState(DEFAULT_VALUES)
  const [selectedSoilType, setSelectedSoilType] = useState('')
  const [confirmedTexture, setConfirmedTexture] = useState('')
  const [notes, setNotes] = useState('')
  const [validationErrors, setValidationErrors] = useState({})

  // If CNN classified soil, synchronize default selector
  useEffect(() => {
    if (detectedSoilType) {
      setSelectedSoilType(detectedSoilType)
    }
  }, [detectedSoilType])

  const isAlluvial = (selectedSoilType || detectedSoilType || '').toLowerCase() === 'alluvial'

  const handleInputChange = (field, rawVal) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: rawVal,
    }))
    // Clear validation error when user edits
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  const applyPreset = (preset) => {
    setFormValues(preset.values)
    setValidationErrors({})
  }

  const validate = () => {
    const errors = {}
    if (mode === 'manual') {
      const {
        nitrogen, phosphorus, potassium, ph,
        soil_temperature, air_temperature, air_humidity,
        rainfall, moisture,
      } = formValues

      if (nitrogen === '' || isNaN(Number(nitrogen)) || Number(nitrogen) < 0 || Number(nitrogen) > 500) {
        errors.nitrogen = 'Nitrogen must be between 0 and 500 mg/kg'
      }
      if (phosphorus === '' || isNaN(Number(phosphorus)) || Number(phosphorus) < 0 || Number(phosphorus) > 300) {
        errors.phosphorus = 'Phosphorus must be between 0 and 300 mg/kg'
      }
      if (potassium === '' || isNaN(Number(potassium)) || Number(potassium) < 0 || Number(potassium) > 600) {
        errors.potassium = 'Potassium must be between 0 and 600 mg/kg'
      }
      if (ph === '' || isNaN(Number(ph)) || Number(ph) < 0 || Number(ph) > 14) {
        errors.ph = 'pH must be between 0.0 and 14.0'
      }
      if (soil_temperature === '' || isNaN(Number(soil_temperature)) || Number(soil_temperature) < -20 || Number(soil_temperature) > 65) {
        errors.soil_temperature = 'Soil temperature must be between -20 and 65 °C'
      }
      if (air_temperature === '' || isNaN(Number(air_temperature)) || Number(air_temperature) < -30 || Number(air_temperature) > 65) {
        errors.air_temperature = 'Air temperature must be between -30 and 65 °C'
      }
      if (air_humidity === '' || isNaN(Number(air_humidity)) || Number(air_humidity) < 0 || Number(air_humidity) > 100) {
        errors.air_humidity = 'Air humidity must be between 0 and 100%'
      }
      if (rainfall === '' || isNaN(Number(rainfall)) || Number(rainfall) < 0 || Number(rainfall) > 5000) {
        errors.rainfall = 'Rainfall must be between 0 and 5000 mm'
      }
      if (moisture === '' || isNaN(Number(moisture)) || Number(moisture) < 0 || Number(moisture) > 100) {
        errors.moisture = 'Soil moisture must be between 0 and 100%'
      }
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return

    if (mode === 'simulator') {
      onRun({
        reading_id: null,
        soil_type: selectedSoilType || detectedSoilType || null,
        confirmed_soil_texture: confirmedTexture || null,
        image_path: imagePath || null,
        notes: notes || null,
      })
    } else {
      const numericData = {
        nitrogen:         Number(formValues.nitrogen),
        phosphorus:       Number(formValues.phosphorus),
        potassium:        Number(formValues.potassium),
        ph:               Number(formValues.ph),
        soil_temperature: Number(formValues.soil_temperature),
        air_temperature:  Number(formValues.air_temperature),
        air_humidity:     Number(formValues.air_humidity),
        rainfall:         Number(formValues.rainfall),
        moisture:         Number(formValues.moisture),
        source:           'manual',
      }

      onRun({
        sensor_data: numericData,
        soil_type: selectedSoilType || detectedSoilType || null,
        confirmed_soil_texture: confirmedTexture || null,
        image_path: imagePath || null,
        notes: notes || null,
      })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card space-y-6">
      {/* ── Mode selector header ───────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-100">
        <div>
          <h3 className="text-gray-800 flex items-center gap-2">
            <Sliders size={18} className="text-agro-green" />
            Analysis Parameters
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Software-driven pipeline: provide manual field measurements or sample a software-simulated reading.
          </p>
        </div>

        {/* Mode Toggle Buttons */}
        <div className="flex items-center p-1 bg-gray-100 rounded-xl text-xs font-medium">
          <button
            type="button"
            onClick={() => setMode('manual')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              mode === 'manual'
                ? 'bg-white text-agro-green shadow-sm font-semibold'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Manual Soil Input
          </button>
          <button
            type="button"
            onClick={() => setMode('simulator')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              mode === 'simulator'
                ? 'bg-white text-agro-green shadow-sm font-semibold'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            <Cpu size={13} />
            Software Simulator
          </button>
        </div>
      </div>

      {mode === 'manual' ? (
        <div className="space-y-5">
          {/* Preset Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-400 font-medium flex items-center gap-1">
              <Sparkles size={13} className="text-amber-500" /> Presets:
            </span>
            {SOIL_PRESETS.map((preset) => (
              <button
                key={preset.name}
                type="button"
                onClick={() => applyPreset(preset)}
                className="text-xs px-2.5 py-1 rounded-lg border border-gray-200 bg-gray-50 hover:bg-agro-green-pale hover:border-agro-green/40 hover:text-agro-green transition-all"
                title={preset.description}
              >
                {preset.name}
              </button>
            ))}
          </div>

          {/* 8 Parameters Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Nitrogen */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Nitrogen (N) <span className="text-gray-400 font-normal">mg/kg</span>
              </label>
              <input
                type="number"
                step="any"
                value={formValues.nitrogen}
                onChange={(e) => handleInputChange('nitrogen', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.nitrogen ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="0 - 300"
              />
              {validationErrors.nitrogen && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.nitrogen}</p>
              )}
            </div>

            {/* Phosphorus */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Phosphorus (P) <span className="text-gray-400 font-normal">mg/kg</span>
              </label>
              <input
                type="number"
                step="any"
                value={formValues.phosphorus}
                onChange={(e) => handleInputChange('phosphorus', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.phosphorus ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="0 - 150"
              />
              {validationErrors.phosphorus && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.phosphorus}</p>
              )}
            </div>

            {/* Potassium */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Potassium (K) <span className="text-gray-400 font-normal">mg/kg</span>
              </label>
              <input
                type="number"
                step="any"
                value={formValues.potassium}
                onChange={(e) => handleInputChange('potassium', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.potassium ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="0 - 400"
              />
              {validationErrors.potassium && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.potassium}</p>
              )}
            </div>

            {/* pH */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Soil pH <span className="text-gray-400 font-normal">(0 - 14)</span>
              </label>
              <input
                type="number"
                step="0.1"
                value={formValues.ph}
                onChange={(e) => handleInputChange('ph', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.ph ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="6.5"
              />
              {validationErrors.ph && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.ph}</p>
              )}
            </div>

            {/* Soil Temperature */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Soil Temperature <span className="text-gray-400 font-normal">°C</span>
              </label>
              <input
                type="number"
                step="0.1"
                value={formValues.soil_temperature}
                onChange={(e) => handleInputChange('soil_temperature', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.soil_temperature ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="24.0"
              />
              {validationErrors.soil_temperature && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.soil_temperature}</p>
              )}
            </div>

            {/* Air Temperature */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Air Temperature <span className="text-gray-400 font-normal">°C</span>
              </label>
              <input
                type="number"
                step="0.1"
                value={formValues.air_temperature}
                onChange={(e) => handleInputChange('air_temperature', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.air_temperature ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="26.0"
              />
              {validationErrors.air_temperature && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.air_temperature}</p>
              )}
            </div>

            {/* Air Humidity */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Air Humidity <span className="text-gray-400 font-normal">%</span>
              </label>
              <input
                type="number"
                step="0.1"
                value={formValues.air_humidity}
                onChange={(e) => handleInputChange('air_humidity', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.air_humidity ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="60.0"
              />
              {validationErrors.air_humidity && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.air_humidity}</p>
              )}
            </div>

            {/* Soil Moisture (volumetric soil water content) */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Soil Moisture <span className="text-gray-400 font-normal">% vol</span>
              </label>
              <input
                type="number"
                step="0.1"
                value={formValues.moisture}
                onChange={(e) => handleInputChange('moisture', e.target.value)}
                className={`w-full px-3 py-2 rounded-xl border text-sm ${
                  validationErrors.moisture ? 'border-red-400 bg-red-50/40' : 'border-gray-200 focus:border-agro-green'
                }`}
                placeholder="45.0"
              />
              {validationErrors.moisture && (
                <p className="text-xs text-red-500 mt-1">{validationErrors.moisture}</p>
              )}
            </div>

            {/* Rainfall (precipitation in mm) - separate from moisture */}
            <div className="sm:col-span-2 lg:col-span-4 bg-sky-50/40 border border-sky-100 rounded-xl p-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-sky-900 mb-0.5">
                    Meteorological Rainfall <span className="text-sky-600 font-normal">(Precipitation in mm)</span>
                  </label>
                  <p className="text-xs text-sky-700">
                    Precipitation parameter used by the Random Forest crop recommendation model (independent of soil volumetric water content).
                  </p>
                </div>
                <div className="w-full sm:w-48">
                  <input
                    type="number"
                    step="0.1"
                    value={formValues.rainfall}
                    onChange={(e) => handleInputChange('rainfall', e.target.value)}
                    className={`w-full px-3 py-2 rounded-xl border text-sm bg-white ${
                      validationErrors.rainfall ? 'border-red-400' : 'border-sky-200 focus:border-sky-500'
                    }`}
                    placeholder="100.0"
                  />
                  {validationErrors.rainfall && (
                    <p className="text-xs text-red-500 mt-1">{validationErrors.rainfall}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-600">
          <p className="font-semibold text-gray-800 mb-1 flex items-center gap-1.5">
            <Cpu size={16} className="text-agro-green" />
            Software Simulator Mode Active
          </p>
          <p className="text-xs leading-relaxed text-gray-500">
            Analysis will capture a fresh reading from the backend software simulator.
            No physical IoT hardware or sensors are required.
          </p>
        </div>
      )}

      {/* ── Contextual Soil Classification & Texture Section ──────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-gray-100">
        {/* Soil Type Selection / CNN Tag */}
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">
            Soil Classification <span className="text-gray-400 font-normal">(Genetic / Order)</span>
          </label>
          <select
            value={selectedSoilType}
            onChange={(e) => setSelectedSoilType(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm bg-white focus:border-agro-green"
          >
            <option value="">Auto-Detect (from uploaded image or sensor heuristic)</option>
            <option value="Alluvial">Alluvial (Fluvial floodplain deposits)</option>
            <option value="Black">Black Soil (Vertisol / Regur)</option>
            <option value="Clay">Clay Soil (Heavy / Fine-grained)</option>
            <option value="Red">Red Soil (Ferruginous / Alfisol)</option>
            <option value="Loamy">Loamy Soil (Balanced agricultural loam)</option>
            <option value="Sandy">Sandy Soil (Coarse / High drainage)</option>
          </select>
          {detectedSoilType && (
            <p className="text-xs text-agro-green mt-1">
              Detected by MobileNetV2: <strong>{detectedSoilType}</strong>
            </p>
          )}
        </div>

        {/* Confirmed Physical Soil Texture (Crucial for Alluvial) */}
        <div className={`${isAlluvial ? 'p-3 rounded-xl bg-amber-50/70 border border-amber-200' : ''}`}>
          <label className="block text-xs font-semibold text-gray-700 mb-1 flex items-center gap-1">
            Confirmed Physical Soil Texture
            {isAlluvial && <span className="text-amber-700 font-bold">*Required for Alluvial</span>}
          </label>
          <select
            value={confirmedTexture}
            onChange={(e) => setConfirmedTexture(e.target.value)}
            className={`w-full px-3 py-2 rounded-xl border text-sm bg-white ${
              isAlluvial && !confirmedTexture
                ? 'border-amber-400 focus:border-amber-500'
                : 'border-gray-200 focus:border-agro-green'
            }`}
          >
            <option value="">{isAlluvial ? '-- Select confirmed texture --' : 'Auto / Not specified'}</option>
            {VALID_SOIL_TEXTURES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-400 mt-1">
            {isAlluvial
              ? 'Alluvial soils vary from coarse sand to dense clay. Selecting texture enables fertilizer advice.'
              : 'Physical particle size distribution (sand/silt/clay ratio), distinct from genetic soil class.'}
          </p>
        </div>
      </div>

      {/* Optional Field Notes */}
      <div>
        <label className="block text-xs font-semibold text-gray-700 mb-1">
          Field Notes <span className="text-gray-400 font-normal">(optional)</span>
        </label>
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g., North field trial block #2, before sowing"
          className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm focus:border-agro-green"
        />
      </div>

      {/* ── Submit Button ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <p className="text-xs text-gray-400">
          Runs Crop RF, Fertilizer Decision Tree, Irrigation Rules, and Soil Health Scoring.
        </p>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary flex items-center gap-2 whitespace-nowrap w-full sm:w-auto justify-center"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Running Software Pipeline…
            </>
          ) : (
            <>
              <FlaskConical size={16} />
              Run Software Analysis
            </>
          )}
        </button>
      </div>
    </form>
  )
}

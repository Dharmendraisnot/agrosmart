/**
 * constants.js — sensor display ranges, thresholds and colours.
 */

// Colour thresholds for each sensor.
// Each entry: { low, high, unit, label }
// Value <= low  → red (poor)
// Value <= high → amber (fair)
// Value > high  → green (good)
export const SENSOR_THRESHOLDS = {
  moisture:         { low: 25,  high: 65,  unit: '%',     label: 'Soil Moisture'     },
  rainfall:         { low: 20,  high: 250, unit: ' mm',   label: 'Rainfall (Precipitation)' },
  ph:               { low: 5.5, high: 7.5, unit: '',      label: 'Soil pH'           },
  soil_temperature: { low: 10,  high: 35,  unit: '°C',    label: 'Soil Temperature'  },
  air_temperature:  { low: 10,  high: 38,  unit: '°C',    label: 'Air Temperature'   },
  air_humidity:     { low: 30,  high: 85,  unit: '%',     label: 'Air Humidity'      },
  nitrogen:         { low: 10,  high: 80,  unit: ' mg/kg',label: 'Nitrogen (N)'      },
  phosphorus:       { low: 5,   high: 50,  unit: ' mg/kg',label: 'Phosphorus (P)'    },
  potassium:        { low: 40,  high: 280, unit: ' mg/kg',label: 'Potassium (K)'     },
}

export const SENSOR_KEYS = Object.keys(SENSOR_THRESHOLDS)

// Valid physical soil texture categories supported by the fertilizer model
// Note: Genetic soil classification (e.g. Alluvial) is distinct from physical particle texture.
export const VALID_SOIL_TEXTURES = [
  { value: 'Loamy',  label: 'Loamy (Medium / Silt-Loam alluvium)' },
  { value: 'Clayey', label: 'Clayey (Fine / Heavy clay alluvium)' },
  { value: 'Sandy',  label: 'Sandy (Coarse / Sandy alluvium)' },
  { value: 'Black',  label: 'Black (Deep Vertisol-like alluvium)' },
  { value: 'Red',    label: 'Red (Ferruginous / Red alluvium)' },
]

// Educational soil parameter presets for testing and learning
export const SOIL_PRESETS = [
  {
    name: 'Balanced Loam (Optimal)',
    description: 'Good NPK balance, neutral pH, moderate moisture',
    values: {
      nitrogen: 65, phosphorus: 35, potassium: 180, ph: 6.8,
      soil_temperature: 24, air_temperature: 26, air_humidity: 60,
      rainfall: 120, moisture: 50,
    },
  },
  {
    name: 'Acidic High-Moisture Clay',
    description: 'Low pH, heavy soil moisture, high organic matter',
    values: {
      nitrogen: 80, phosphorus: 20, potassium: 120, ph: 5.2,
      soil_temperature: 20, air_temperature: 22, air_humidity: 80,
      rainfall: 220, moisture: 75,
    },
  },
  {
    name: 'Arid Sandy Field',
    description: 'Low moisture, alkaline pH, deficient NPK',
    values: {
      nitrogen: 20, phosphorus: 12, potassium: 90, ph: 7.9,
      soil_temperature: 34, air_temperature: 36, air_humidity: 35,
      rainfall: 25, moisture: 20,
    },
  },
]

// Map health_status to Tailwind badge class
export const HEALTH_BADGE = {
  Good: 'badge-good',
  Fair: 'badge-fair',
  Poor: 'badge-poor',
}

// Map irrigation urgency to colours
export const URGENCY_COLOR = {
  critical: 'text-red-600 bg-red-50 border-red-200',
  high:     'text-orange-600 bg-orange-50 border-orange-200',
  medium:   'text-yellow-700 bg-yellow-50 border-yellow-200',
  low:      'text-green-700 bg-green-50 border-green-200',
  none:     'text-blue-700 bg-blue-50 border-blue-200',
  unknown:  'text-gray-600 bg-gray-50 border-gray-200',
}

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
  ph:               { low: 5.5, high: 7.5, unit: '',      label: 'Soil pH'           },
  soil_temperature: { low: 10,  high: 35,  unit: '°C',    label: 'Soil Temperature'  },
  air_temperature:  { low: 10,  high: 38,  unit: '°C',    label: 'Air Temperature'   },
  air_humidity:     { low: 30,  high: 85,  unit: '%',     label: 'Air Humidity'      },
  nitrogen:         { low: 10,  high: 80,  unit: ' mg/kg',label: 'Nitrogen (N)'      },
  phosphorus:       { low: 5,   high: 50,  unit: ' mg/kg',label: 'Phosphorus (P)'    },
  potassium:        { low: 40,  high: 280, unit: ' mg/kg',label: 'Potassium (K)'     },
}

export const SENSOR_KEYS = Object.keys(SENSOR_THRESHOLDS)

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

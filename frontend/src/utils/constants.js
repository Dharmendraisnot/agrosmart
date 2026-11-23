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

// 22 supported crops partitioned into Horticultural & Orchard vs Field Crops & Legumes
export const CROP_GROUPS = [
  {
    group: 'Horticultural & Orchard Crops (12)',
    crops: [
      { value: 'mango',       label: 'Mango (Mangifera indica)',            isTree: true  },
      { value: 'apple',       label: 'Apple (Malus domestica)',             isTree: true  },
      { value: 'orange',      label: 'Orange / Citrus (Citrus sinensis)',   isTree: true  },
      { value: 'pomegranate', label: 'Pomegranate (Punica granatum)',       isTree: true  },
      { value: 'coconut',     label: 'Coconut (Cocos nucifera)',            isTree: true  },
      { value: 'banana',      label: 'Banana (Musa acuminata)',             isTree: false },
      { value: 'grapes',      label: 'Grapes (Vitis vinifera)',             isTree: false },
      { value: 'papaya',      label: 'Papaya (Carica papaya)',              isTree: false },
      { value: 'coffee',      label: 'Coffee (Coffea arabica / canephora)', isTree: false },
      { value: 'jute',        label: 'Jute (Corchorus olitorius)',          isTree: false },
      { value: 'watermelon',  label: 'Watermelon (Citrullus lanatus)',      isTree: false },
      { value: 'muskmelon',   label: 'Muskmelon (Cucumis melo)',            isTree: false },
    ],
  },
  {
    group: 'Field Crops & Legumes (10)',
    crops: [
      { value: 'rice',        label: 'Rice / Paddy (Oryza sativa)' },
      { value: 'maize',       label: 'Maize / Corn (Zea mays)' },
      { value: 'cotton',      label: 'Cotton (Gossypium hirsutum)' },
      { value: 'chickpea',    label: 'Chickpea / Gram (Cicer arietinum)' },
      { value: 'kidneybeans', label: 'Kidney Beans / Rajma (Phaseolus vulgaris)' },
      { value: 'pigeonpeas',  label: 'Pigeon Peas / Arhar (Cajanus cajan)' },
      { value: 'mothbeans',   label: 'Moth Beans (Vigna aconitifolia)' },
      { value: 'mungbean',    label: 'Mung Bean / Green Gram (Vigna radiata)' },
      { value: 'blackgram',   label: 'Black Gram / Urad (Vigna mungo)' },
      { value: 'lentil',      label: 'Lentil / Masoor (Lens culinaris)' },
    ],
  },
]

// Perennial orchard crops supporting progressive annual tree age dosage scaling
export const TREE_AGE_SUPPORTED_CROPS = ['mango', 'apple', 'orange', 'pomegranate', 'coconut']

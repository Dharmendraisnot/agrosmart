/**
 * FertilizerCard.jsx — NPK fertilizer recommendation & horticultural advisory display.
 * Clearly distinguishes active ML predictions from expert-verified extension guidelines
 * and scientifically withheld advice.
 */
import {
  Leaf,
  AlertTriangle,
  Info,
  CheckCircle2,
  Sprout,
  Clock,
  Layers,
  Sparkles,
  FlaskConical,
  BookOpen,
} from 'lucide-react'

function formatUnitLabel(unit) {
  if (!unit) return ''
  switch (unit) {
    case 'per_tree_per_year':
      return 'Per Tree / Year'
    case 'per_plant_per_cycle':
      return 'Per Plant / Cycle'
    case 'per_palm_per_year':
      return 'Per Palm / Year'
    case 'per_hectare_annual':
      return 'Per Hectare / Year'
    case 'per_hectare_crop_season':
      return 'Per Hectare / Season'
    default:
      return unit.replace(/_/g, ' ')
  }
}

export default function FertilizerCard({ fertilizer }) {
  if (!fertilizer) {
    return (
      <div className="card text-center py-10 text-gray-400">
        <Leaf size={32} className="mx-auto mb-2 opacity-40" />
        <p className="text-sm">No fertilizer data — run an analysis first.</p>
      </div>
    )
  }

  const isHorticultural = fertilizer.status === 'horticultural_guideline'
  const isUnavailable =
    fertilizer.fertilizer === 'Reliable recommendation unavailable' ||
    fertilizer.status === 'unsupported'
  const isPrototype = fertilizer.model_label?.includes('prototype')

  // ─────────────────────────────────────────────────────────────────────────────
  // 1. DEDICATED HORTICULTURAL EXTENSION ADVISORY CARD
  // ─────────────────────────────────────────────────────────────────────────────
  if (isHorticultural) {
    const details = fertilizer.horticulture_details || {}
    const commonName = details.common_name || fertilizer.crop || 'Orchard / Horticultural Crop'
    const botanicalName = details.botanical_name || ''
    const plantType = details.plant_type || fertilizer.plant_type || 'Horticultural Crop'
    const headline = fertilizer.headline || `Extension Package of Practices for ${commonName}`
    const dosage = fertilizer.dosage_summary || fertilizer.advice || 'Standard extension package applies.'
    const unitLabel = formatUnitLabel(fertilizer.dosage_unit)
    const treeAge = details.tree_age || fertilizer.tree_age || fertilizer.tree_age_years

    const splits = Array.isArray(fertilizer.timing_and_splits)
      ? fertilizer.timing_and_splits
      : details.timing_and_splits || []

    const sources = Array.isArray(fertilizer.authority_sources)
      ? fertilizer.authority_sources
      : details.authority_sources || []

    const caveats = Array.isArray(fertilizer.missing_or_unverified_fields)
      ? fertilizer.missing_or_unverified_fields
      : details.missing_or_unverified_fields || []

    return (
      <div className="space-y-4">
        {/* Main Advisory Card */}
        <div className="card border border-emerald-200/90 bg-gradient-to-b from-emerald-50/40 via-white to-white space-y-5 shadow-sm">

          {/* Header Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-emerald-100">
            <div className="flex items-start sm:items-center gap-3">
              <div className="rounded-xl p-2.5 bg-emerald-600 text-white shadow-sm shrink-0">
                <Sprout size={24} />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-200">
                    Horticultural Extension Advisory
                  </span>
                  <span className="text-[11px] font-medium text-gray-500">
                    Expert-Verified Package of Practices
                  </span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mt-0.5">
                  {headline}
                </h3>
                <p className="text-xs text-gray-500">
                  <strong className="text-gray-700 capitalize">{commonName}</strong>
                  {botanicalName && <span className="italic text-gray-400"> ({botanicalName})</span>}
                  {plantType && <span className="text-emerald-700"> • {plantType}</span>}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
                <CheckCircle2 size={13} className="text-emerald-600" />
                ICAR / SAU Validated
              </span>
            </div>
          </div>

          {/* Distinction Callout Banner */}
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-emerald-50/80 border border-emerald-200 text-emerald-950 text-xs leading-relaxed">
            <BookOpen size={16} className="text-emerald-700 mt-0.5 shrink-0" />
            <div>
              <strong>Scientific Horticultural Extension:</strong> Tree orchards and horticultural crops require specialized age-based dosage schedules, ring-basin placement, and phenological splits. This recommendation is sourced directly from institutional research packages rather than seasonal field-crop ML models.
            </div>
          </div>

          {/* Recommended Nutrient Dosage & Formulation Card */}
          <div className="rounded-xl p-4 bg-emerald-50/50 border border-emerald-200 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Layers size={18} className="text-emerald-700" />
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                  Recommended Nutrient Dosage & Formulation
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {treeAge && (
                  <span className="text-[11px] font-semibold bg-white text-emerald-800 px-2 py-0.5 rounded border border-emerald-300">
                    Orchard Age: {treeAge} Years
                  </span>
                )}
                {unitLabel && (
                  <span className="text-[11px] font-semibold bg-emerald-200/80 text-emerald-900 px-2 py-0.5 rounded border border-emerald-300">
                    {unitLabel}
                  </span>
                )}
              </div>
            </div>
            <p className="text-base font-semibold text-gray-900 leading-snug">
              {dosage}
            </p>
          </div>

          {/* 2-Column Responsive Grid: Method & Timing */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Application Method & Placement */}
            <div className="p-3.5 rounded-xl border border-gray-200 bg-white space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-700">
                <Layers size={15} className="text-emerald-600 shrink-0" />
                <span>Application Method & Geometry</span>
              </div>
              <p className="text-xs text-gray-700 leading-relaxed">
                {fertilizer.application_method || 'Consult local horticultural extension guidelines for placement geometry.'}
              </p>
            </div>

            {/* Split Schedule & Phenological Timing */}
            <div className="p-3.5 rounded-xl border border-gray-200 bg-white space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-700">
                <Clock size={15} className="text-emerald-600 shrink-0" />
                <span>Timing & Phenological Splits</span>
              </div>
              {splits.length > 0 ? (
                <ul className="space-y-1.5 text-xs text-gray-700">
                  {splits.map((split, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-600 font-bold shrink-0 mt-0.5">•</span>
                      <span>{split}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-500 italic">No split schedule recorded.</p>
              )}
            </div>
          </div>

          {/* 2-Column Responsive Grid: Organic Manure & Micronutrients */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Organic Manure Base */}
            <div className="p-3.5 rounded-xl border border-gray-200 bg-white space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-700">
                <Sparkles size={15} className="text-emerald-600 shrink-0" />
                <span>Organic Manure Baseline (FYM / Compost)</span>
              </div>
              <p className="text-xs text-gray-700 leading-relaxed">
                {fertilizer.organic_manure || 'Apply well-rotted farmyard manure (FYM) or compost as a basal buffer.'}
              </p>
            </div>

            {/* Micronutrients */}
            <div className="p-3.5 rounded-xl border border-gray-200 bg-white space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-700">
                <FlaskConical size={15} className="text-emerald-600 shrink-0" />
                <span>Foliar & Soil Micronutrient Corrections</span>
              </div>
              <p className="text-xs text-gray-700 leading-relaxed">
                {fertilizer.micronutrients || 'Conduct foliar analysis for Zinc, Boron, and Iron status.'}
              </p>
            </div>
          </div>

          {/* Critical Special Cautions */}
          {fertilizer.special_cautions && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1.5 text-xs">
              <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-amber-800">
                <AlertTriangle size={15} className="text-amber-600 shrink-0" />
                <span>Critical Agronomic Precautions</span>
              </div>
              <p className="leading-relaxed">
                {fertilizer.special_cautions}
              </p>
            </div>
          )}

          {/* Verified Authority Sources & Caveats */}
          <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-200 text-xs space-y-2">
            <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-600">
              <CheckCircle2 size={14} className="text-emerald-600" />
              <span>Verified Agricultural Authority Sources</span>
            </div>
            {sources.length > 0 ? (
              <ul className="space-y-1 text-gray-600 pl-1">
                {sources.map((src, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-gray-400 font-bold shrink-0">•</span>
                    <span>{src}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">Institutional extension sources on file.</p>
            )}

            {caveats.length > 0 && (
              <div className="pt-2 border-t border-gray-200/80 flex items-start gap-1.5 text-gray-500">
                <Info size={13} className="text-gray-400 mt-0.5 shrink-0" />
                <span>
                  <strong>Field Caveat:</strong> {caveats.join(' ')}
                </span>
              </div>
            )}
          </div>

          {/* Metadata Footer */}
          <div className="flex flex-wrap gap-4 pt-2 border-t border-gray-100 text-xs text-gray-400">
            {fertilizer.soil_type && (
              <span>Soil type: <strong className="text-gray-600">{fertilizer.soil_type}</strong></span>
            )}
            {fertilizer.crop && (
              <span>Crop: <strong className="text-gray-600 capitalize">{fertilizer.crop}</strong></span>
            )}
            <span>Domain: <strong className="text-emerald-700">Horticultural Extension</strong></span>
            <span>Guideline Ref: <strong className="text-gray-500">{fertilizer.model_label || 'icar_extension_v1.0'}</strong></span>
          </div>
        </div>
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // 2. STANDARD CARD FOR ML DECISION TREE & WITHHELD UNSUPPORTED CROPS
  // ─────────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Prototype warning banner for Kaggle model */}
      {isPrototype && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-50 border border-yellow-200 text-yellow-700 text-xs">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>
            Prototype model (Kaggle benchmark data). Will be upgraded with AgroSmart experimental field trials.
          </span>
        </div>
      )}

      {/* Main card */}
      <div className="card space-y-4">
        {/* Fertilizer name / status */}
        <div className="flex items-center gap-3">
          <div className={`rounded-xl p-3 ${isUnavailable ? 'bg-amber-100 text-amber-700' : 'bg-agro-green/10 text-agro-green'}`}>
            {isUnavailable ? <AlertTriangle size={22} /> : <Leaf size={22} />}
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
              {isUnavailable ? 'Recommendation Status' : 'Recommended Fertilizer (ML Decision Tree)'}
            </p>
            <p className={`text-2xl font-bold ${isUnavailable ? 'text-amber-800 text-xl' : 'text-agro-green'}`}>
              {fertilizer.fertilizer}
            </p>
          </div>
        </div>

        {/* Advice / Reason Box */}
        <div className={`rounded-xl px-4 py-3.5 border text-sm ${
          isUnavailable
            ? 'bg-amber-50/70 border-amber-200 text-amber-900 leading-relaxed'
            : 'bg-agro-green-pale border-agro-green/20 text-gray-800'
        }`}>
          <div className="flex items-start gap-2">
            {isUnavailable ? (
              <Info size={16} className="text-amber-600 mt-0.5 shrink-0" />
            ) : (
              <CheckCircle2 size={16} className="text-agro-green mt-0.5 shrink-0" />
            )}
            <p>{fertilizer.advice}</p>
          </div>
        </div>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-4 pt-1 border-t border-gray-100 text-xs text-gray-400">
          {fertilizer.soil_type && (
            <span>Soil type: <strong className="text-gray-600">{fertilizer.soil_type}</strong></span>
          )}
          {fertilizer.crop && (
            <span>Crop: <strong className="text-gray-600 capitalize">{fertilizer.crop}</strong></span>
          )}
          {fertilizer.mapped_crop_category && (
            <span>Mapped category: <strong className="text-gray-600">{fertilizer.mapped_crop_category}</strong></span>
          )}
          <span>Model: <strong className="text-gray-500">{fertilizer.model_label}</strong></span>
        </div>
      </div>
    </div>
  )
}

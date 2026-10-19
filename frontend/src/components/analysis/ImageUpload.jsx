/**
 * ImageUpload.jsx — drag-and-drop soil image uploader.
 * Calls POST /api/images/upload and returns the CNN result.
 */
import { useState, useRef } from 'react'
import { uploadImage } from '../../services/api'
import { Upload, Image as ImageIcon, CheckCircle, AlertCircle, Info, X } from 'lucide-react'

export default function ImageUpload({ onResult, onClear }) {
  const [dragging,  setDragging]  = useState(false)
  const [preview,   setPreview]   = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result,    setResult]    = useState(null)
  const [error,     setError]     = useState(null)
  const inputRef = useRef(null)

  const ACCEPTED = 'image/jpeg,image/png,image/webp'

  const handleFile = async (file) => {
    if (!file) return
    setError(null)
    setResult(null)
    setPreview(URL.createObjectURL(file))
    setUploading(true)
    try {
      const { data } = await uploadImage(file)
      setResult(data)
      if (onResult) onResult(data)
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleClear = (e) => {
    e.stopPropagation()
    setPreview(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
    if (onClear) onClear()
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const onInputChange = (e) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const isAlluvial = result?.soil_type?.toLowerCase() === 'alluvial'

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-6 flex flex-col items-center
          justify-center gap-3 cursor-pointer transition-colors ${
          dragging
            ? 'border-agro-green bg-agro-green-pale'
            : 'border-gray-200 hover:border-agro-green/50 hover:bg-gray-50'
        }`}
      >
        <input
          ref={inputRef} type="file" accept={ACCEPTED}
          className="hidden" onChange={onInputChange}
        />

        {preview ? (
          <div className="relative">
            <img
              src={preview} alt="Soil preview"
              className="w-36 h-36 object-cover rounded-xl shadow-sm border border-gray-100"
            />
            <button
              type="button"
              onClick={handleClear}
              className="absolute -top-2 -right-2 bg-white text-gray-500 hover:text-red-600 rounded-full p-1 shadow-md border border-gray-200 transition-colors"
              title="Remove image"
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <div className="bg-gray-100 rounded-full p-4">
            <ImageIcon size={28} className="text-gray-400" />
          </div>
        )}

        <div className="text-center">
          <p className="text-sm font-medium text-gray-700">
            {preview ? 'Click or drop to replace image' : 'Drop a soil image here, or browse'}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">JPEG, PNG or WebP (max 10 MB)</p>
        </div>

        {uploading && (
          <div className="absolute inset-0 bg-white/80 rounded-2xl flex items-center justify-center">
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 border-4 border-agro-green border-t-transparent rounded-full animate-spin" />
              <p className="text-xs font-medium text-agro-green">Classifying with MobileNetV2…</p>
            </div>
          </div>
        )}
      </div>

      {/* Result Card */}
      {result && (
        <div className={`p-4 rounded-xl border space-y-3 ${
          result.cnn_status === 'ok'
            ? 'bg-green-50/60 border-green-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-start gap-3">
            {result.cnn_status === 'ok'
              ? <CheckCircle size={18} className="text-green-600 mt-0.5 shrink-0" />
              : <AlertCircle size={18} className="text-yellow-600 mt-0.5 shrink-0" />
            }
            <div className="flex-1">
              {result.cnn_status === 'ok' ? (
                <>
                  <p className="text-sm font-semibold text-green-900">
                    MobileNetV2 Classification: <span className="text-agro-green font-bold text-base">{result.soil_type} Soil</span>
                  </p>
                  {result.confidence != null && (
                    <p className="text-xs text-green-700 mt-0.5 font-medium">
                      Model Confidence: {(result.confidence * 100).toFixed(1)}%
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-yellow-800">
                  CNN model unavailable — software heuristic will estimate soil type from soil moisture and pH.
                </p>
              )}
            </div>
          </div>

          {/* Conditional Class Probability Breakdown - only if backend returns all_classes */}
          {result.cnn_status === 'ok' && Array.isArray(result.all_classes) && result.all_classes.length > 0 && (
            <div className="pt-2 border-t border-green-200/60 space-y-1.5">
              <p className="text-xs font-semibold text-green-900 uppercase tracking-wide">
                Class Probabilities:
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {result.all_classes.map((item) => (
                  <div key={item.class} className="bg-white/80 rounded-lg p-2 border border-green-100">
                    <div className="flex justify-between text-xs text-gray-700 mb-1">
                      <span className="font-medium">{item.class}</span>
                      <span>{(item.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-agro-green h-1.5 rounded-full"
                        style={{ width: `${Math.min(100, Math.max(0, item.confidence * 100))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alluvial Soil Guided Explanation */}
          {isAlluvial && (
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-xs">
              <Info size={15} className="mt-0.5 shrink-0 text-blue-600" />
              <span>
                <strong>Alluvial Soil Detected:</strong> Alluvial soils are broad genetic fluvial deposits ranging in physical particle texture from coarse sand to dense clay. To generate accurate fertilizer recommendations, please confirm the physical soil texture in the form below.
              </span>
            </div>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          {error}
        </p>
      )}
    </div>
  )
}

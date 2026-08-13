/**
 * ImageUpload.jsx — drag-and-drop soil image uploader.
 * Calls POST /api/images/upload and returns the CNN result.
 */
import { useState, useRef } from 'react'
import { uploadImage } from '../../services/api'
import { Upload, Image as ImageIcon, CheckCircle, AlertCircle } from 'lucide-react'

export default function ImageUpload({ onResult }) {
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
      setError(err?.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
    }
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

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center
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
          <img
            src={preview} alt="Soil preview"
            className="w-32 h-32 object-cover rounded-xl"
          />
        ) : (
          <div className="bg-gray-100 rounded-full p-4">
            <ImageIcon size={28} className="text-gray-400" />
          </div>
        )}

        <div className="text-center">
          <p className="text-sm font-medium text-gray-600">
            {preview ? 'Click or drop to replace' : 'Drop a soil image here'}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">JPG, PNG or WebP</p>
        </div>

        {uploading && (
          <div className="absolute inset-0 bg-white/80 rounded-2xl flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-agro-green border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Result */}
      {result && (
        <div className={`flex items-start gap-3 p-4 rounded-xl border ${
          result.cnn_status === 'ok'
            ? 'bg-green-50 border-green-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          {result.cnn_status === 'ok'
            ? <CheckCircle size={18} className="text-green-600 mt-0.5 shrink-0" />
            : <AlertCircle size={18} className="text-yellow-600 mt-0.5 shrink-0" />
          }
          <div>
            {result.cnn_status === 'ok' ? (
              <>
                <p className="text-sm font-semibold text-green-800">
                  Soil classified: <span className="text-green-600">{result.soil_type}</span>
                </p>
                <p className="text-xs text-green-600 mt-0.5">
                  Confidence: {(result.confidence * 100).toFixed(1)}%
                </p>
              </>
            ) : (
              <p className="text-sm text-yellow-800">
                CNN model not available — soil type will be estimated from sensors.
              </p>
            )}
          </div>
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

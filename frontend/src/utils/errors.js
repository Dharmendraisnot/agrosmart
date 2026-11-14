/**
 * errors.js — defensive error message extraction for API and runtime errors.
 */

/**
 * Extracts a human-readable, displayable string from an error of unknown shape.
 *
 * Handles:
 * - Backend standard JSON envelope: { error: { code, message } }
 * - Backend string error envelope:  { error: "Error message" }
 * - Backend detail envelope:        { detail: "Error detail" }
 * - Plain string HTTP response data
 * - Standard Error instance:        err.message
 * - Raw string errors:              "Something failed"
 * - Fallback default
 *
 * Always returns a non-empty string suitable for direct React rendering.
 *
 * @param {unknown} err - The caught error object, exception, or string
 * @param {string} [fallback] - Safe default fallback message
 * @returns {string} Guaranteed safe display string
 */
export function getErrorMessage(err, fallback = 'An unexpected error occurred. Please try again.') {
  if (!err) return fallback

  // If already a non-empty string
  if (typeof err === 'string' && err.trim().length > 0) {
    return err.trim()
  }

  // Check Axios response data structure
  const data = err?.response?.data
  if (data) {
    // 1. Backend standard: { success: false, error: { code: '...', message: '...' } }
    if (data.error && typeof data.error === 'object' && typeof data.error.message === 'string' && data.error.message.trim().length > 0) {
      return data.error.message.trim()
    }
    // 2. String error property: { error: '...' }
    if (typeof data.error === 'string' && data.error.trim().length > 0) {
      return data.error.trim()
    }
    // 3. Detail property: { detail: '...' }
    if (typeof data.detail === 'string' && data.detail.trim().length > 0) {
      return data.detail.trim()
    }
    // 4. Plain text response body
    if (typeof data === 'string' && data.trim().length > 0) {
      return data.trim()
    }
  }

  // Standard JavaScript Error instance with .message
  if (typeof err.message === 'string' && err.message.trim().length > 0) {
    return err.message.trim()
  }

  return fallback
}

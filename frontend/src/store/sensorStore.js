/**
 * sensorStore.js — Zustand global store for live sensor state.
 *
 * Holds the most recent sensor reading and connection status.
 * Components subscribe to this store; the useSensorData hook populates it.
 */
import { create } from 'zustand'

const useSensorStore = create((set) => ({
  // Latest sensor reading dict (or null if not yet fetched)
  reading: null,

  // Connection state: 'connecting' | 'live' | 'error'
  status: 'connecting',

  // Error message if status === 'error'
  errorMessage: null,

  // Timestamp of last successful fetch
  lastUpdated: null,

  // Actions
  setReading: (reading) =>
    set({
      reading,
      status: 'live',
      errorMessage: null,
      lastUpdated: new Date(),
    }),

  setError: (message) =>
    set({ status: 'error', errorMessage: message }),

  setConnecting: () =>
    set({ status: 'connecting' }),
}))

export default useSensorStore

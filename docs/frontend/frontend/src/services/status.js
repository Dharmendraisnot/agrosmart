// Tiny store that tells the UI whether we are running on demo data
// (backend unreachable) or on the real Flask API.
import { useSyncExternalStore } from 'react';

let demo = false;
const listeners = new Set();

export function setDemo(value) {
  if (demo === value) return;
  demo = value;
  listeners.forEach((l) => l());
}

const subscribe = (cb) => {
  listeners.add(cb);
  return () => listeners.delete(cb);
};

export function useDemoMode() {
  return useSyncExternalStore(subscribe, () => demo);
}

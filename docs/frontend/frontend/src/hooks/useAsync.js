import { useCallback, useEffect, useRef, useState } from 'react';
import { errorMessage } from '../services/api';

// Generic data-fetching hook with optional polling.
//   const { data, loading, error, reload } = useAsync(() => api.latestSensor(), [], { poll: 10000 });
export function useAsync(fn, deps = [], { poll = 0, enabled = true } = {}) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const alive = useRef(true);

  const run = useCallback(async (silent = false) => {
    if (!silent) setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fnRef.current();
      if (alive.current) setState({ data, loading: false, error: null });
    } catch (err) {
      if (alive.current) setState((s) => ({ ...s, loading: false, error: errorMessage(err) }));
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    if (!enabled) return undefined;
    run(false);
    let timer;
    if (poll > 0) timer = setInterval(() => run(true), poll);
    return () => {
      alive.current = false;
      if (timer) clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, poll, enabled]);

  return { ...state, reload: () => run(false) };
}

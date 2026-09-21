import { useEffect, useState } from 'react';
import { fetchHealth } from '../services/api';
import { HealthStatus } from '../types';

export function useHealth(pollIntervalMs: number = 10000) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function check() {
      try {
        const data = await fetchHealth();
        if (isMounted) {
          setHealth(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Backend offline');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    check();
    const timer = setInterval(check, pollIntervalMs);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, [pollIntervalMs]);

  return { health, isOnline: !error && health !== null, loading, error };
}

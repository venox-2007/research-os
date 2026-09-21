import { useCallback, useEffect, useRef, useState } from 'react';
import { getResearchRun, startResearchRun } from '../services/api';
import { ResearchRunResponse } from '../types';

export function useResearchRun(initialRun?: ResearchRunResponse | null) {
  const [currentRun, setCurrentRun] = useState<ResearchRunResponse | null>(initialRun || null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  const startRun = useCallback(async (
    question: string,
    discipline?: string,
    constraints: string[] = [],
    maxIterations: number = 2,
  ) => {
    setLoading(true);
    setError(null);
    try {
      const run = await startResearchRun(question, discipline, constraints, maxIterations);
      setCurrentRun(run);
      return run;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshRun = useCallback(async (runId: string) => {
    try {
      const updated = await getResearchRun(runId);
      setCurrentRun(updated);
      return updated;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      return null;
    }
  }, []);

  // Background polling while run is in progress
  useEffect(() => {
    if (
      currentRun &&
      currentRun.status !== 'completed' &&
      currentRun.status !== 'failed'
    ) {
      const timer = window.setInterval(async () => {
        await refreshRun(currentRun.run_id);
      }, 2500);
      pollTimerRef.current = timer;
      return () => clearInterval(timer);
    } else if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
    }
  }, [currentRun?.status, currentRun?.run_id, refreshRun]);

  return {
    currentRun,
    setCurrentRun,
    startRun,
    refreshRun,
    loading,
    error,
    isRunning: Boolean(
      currentRun &&
      currentRun.status !== 'completed' &&
      currentRun.status !== 'failed'
    ),
  };
}

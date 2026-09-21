import React, { useState } from 'react';
import { ExperimentRun } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { MetricsChart } from '../components/MetricsChart';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { runExperiment } from '../services/api';

interface ExperimentsPageProps {
  experimentRuns: ExperimentRun[];
  onAddExperimentRun: (run: ExperimentRun) => void;
  isDemo?: boolean;
}

const CATALOG_ROUTINES = [
  {
    routine_id: 'ranking_evaluation',
    title: 'Ranking Evaluation (RRF vs BM25)',
    description: 'Benchmarks Reciprocal Rank Fusion against BM25 alone across MRR@10, NDCG@10, and Recall@20.',
    defaultParams: { k: 60, top_k: 20 },
  },
  {
    routine_id: 'chunking_benchmark',
    title: 'Chunk Size Ablation (256 vs 512 vs 1024)',
    description: 'Measures retrieval precision vs token efficiency across different chunk boundary sizes.',
    defaultParams: { chunk_sizes: [256, 512, 1024], overlap: 64 },
  },
  {
    routine_id: 'retrieval_comparison',
    title: 'Dense vs Hybrid Latency & Recall',
    description: 'Computes query latency (ms) and recall curves for purely dense FAISS vs hybrid BM25+FAISS.',
    defaultParams: { query_count: 50, rerank: true },
  },
];

export const ExperimentsPage: React.FC<ExperimentsPageProps> = ({
  experimentRuns,
  onAddExperimentRun,
}) => {
  const [selectedRoutine, setSelectedRoutine] = useState(CATALOG_ROUTINES[0].routine_id);
  const [hypothesis, setHypothesis] = useState(
    'Reciprocal Rank Fusion with k=60 achieves statistically significant higher MRR than BM25 alone.'
  );
  const [isExecuting, setIsExecuting] = useState(false);
  const [selectedRun, setSelectedRun] = useState<ExperimentRun | null>(
    experimentRuns.length > 0 ? experimentRuns[0] : null
  );

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isExecuting) return;

    setIsExecuting(true);
    try {
      const routine = CATALOG_ROUTINES.find((r) => r.routine_id === selectedRoutine);
      const res = await runExperiment(
        selectedRoutine,
        routine ? routine.defaultParams : {},
        'synthetic_benchmark',
        42
      );
      onAddExperimentRun(res);
      setSelectedRun(res);
    } catch (err) {
      console.error('Experiment execution failed:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleExportJSON = (run: ExperimentRun) => {
    const blob = new Blob([JSON.stringify(run, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `experiment-${run.run_id || run.id || 'result'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Experiment Engine</span>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800">
              Sandboxed / Deterministic
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical hypothesis testing, benchmark routines, metric logging, and artifact generation.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Total Executions: <span className="text-cyan-400 font-bold">{experimentRuns.length}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Launcher & Catalog */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              <span>Design & Launch Experiment</span>
            </h2>

            <form onSubmit={handleLaunch} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Benchmarking Routine
                </label>
                <select
                  value={selectedRoutine}
                  onChange={(e) => {
                    setSelectedRoutine(e.target.value);
                    const found = CATALOG_ROUTINES.find((r) => r.routine_id === e.target.value);
                    if (found) setHypothesis(`Testing ${found.title} under empirical controls.`);
                  }}
                  disabled={isExecuting}
                  className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2.5 focus:outline-none focus:border-cyan-500 transition font-mono"
                >
                  {CATALOG_ROUTINES.map((r) => (
                    <option key={r.routine_id} value={r.routine_id}>
                      {r.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Research Hypothesis
                </label>
                <textarea
                  value={hypothesis}
                  onChange={(e) => setHypothesis(e.target.value)}
                  rows={3}
                  disabled={isExecuting}
                  required
                  placeholder="Formulate an empirical hypothesis to validate..."
                  className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2.5 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Execution Sandbox:</span>
                  <span className="text-emerald-400">Strict Isolated Local</span>
                </div>
                <div className="flex justify-between">
                  <span>Timeout Budget:</span>
                  <span className="text-slate-300">10.0 seconds</span>
                </div>
                <div className="flex justify-between">
                  <span>External Network:</span>
                  <span className="text-amber-400">Disabled (0 egress)</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={isExecuting || !hypothesis.trim()}
                className="w-full py-2 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-semibold transition disabled:opacity-40 flex items-center justify-center space-x-2"
              >
                {isExecuting ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Executing Safe Benchmark...</span>
                  </>
                ) : (
                  <span>Launch Safe Experiment &rarr;</span>
                )}
              </button>
            </form>
          </div>

          {/* Past Executions List */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-2">
              Executed Runs ({experimentRuns.length})
            </span>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {experimentRuns.map((run) => {
                const isSelected = selectedRun?.id === run.id;
                const routineTitle = run.routine_name || run.config?.target_routine || run.id;
                return (
                  <button
                    key={run.id}
                    type="button"
                    onClick={() => setSelectedRun(run)}
                    className={`w-full text-left p-2.5 rounded-lg border transition ${
                      isSelected
                        ? 'border-cyan-500/60 bg-cyan-950/30 text-white'
                        : 'border-slate-800 bg-slate-950/40 hover:bg-slate-900 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono text-[11px] text-cyan-400 font-bold truncate max-w-[160px]">
                        {routineTitle}
                      </span>
                      <StatusBadge status={run.status} />
                    </div>
                    <p className="text-[11px] text-slate-400 truncate">
                      Run: {run.run_id} &bull; {run.duration_seconds ? `${run.duration_seconds.toFixed(2)}s` : 'Completed'}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Selected Experiment Results, Metrics & Artifacts */}
        <div className="lg:col-span-7 space-y-4">
          {selectedRun ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-5">
              <div className="flex items-start justify-between pb-3 border-b border-slate-800 gap-2">
                <div>
                  <span className="font-mono text-[10px] text-slate-400 uppercase">
                    Run ID: {selectedRun.run_id}
                  </span>
                  <h2 className="text-base font-semibold text-slate-100 mt-0.5">
                    {selectedRun.routine_name || selectedRun.config?.target_routine || selectedRun.id}
                  </h2>
                </div>
                <div className="flex items-center space-x-2">
                  <StatusBadge status={selectedRun.status} />
                  <button
                    type="button"
                    onClick={() => handleExportJSON(selectedRun)}
                    className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition"
                    title="Export experiment run as JSON"
                  >
                    Export JSON
                  </button>
                </div>
              </div>

              {/* Chart of Metrics */}
              {selectedRun.metrics && Object.keys(selectedRun.metrics).length > 0 && (
                <MetricsChart
                  metrics={selectedRun.metrics}
                  title="Empirical Evaluation Metrics"
                />
              )}

              {/* Key Metrics Grid */}
              {selectedRun.metrics && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center font-mono">
                  {Object.entries(selectedRun.metrics).map(([key, val]) => (
                    <div key={key} className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                      <div className="text-base font-bold text-emerald-400 truncate">
                        {typeof val === 'number' ? val.toFixed(3) : String(val)}
                      </div>
                      <div className="text-[10px] text-slate-400 uppercase truncate">
                        {key.replace(/_/g, ' ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Artifacts / Output logs */}
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                  Execution Artifacts & Parameters
                </span>
                <pre className="text-[11px] font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 overflow-x-auto max-h-48">
                  {JSON.stringify(
                    {
                      config: selectedRun.config,
                      artifacts: selectedRun.artifacts,
                      duration_seconds: selectedRun.duration_seconds,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No Experiment Selected"
              description="Launch a benchmark routine from the left panel or select an existing execution to view metrics."
            />
          )}
        </div>
      </div>
    </div>
  );
};

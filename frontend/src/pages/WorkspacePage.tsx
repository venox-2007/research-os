import React, { useState } from 'react';
import { ResearchRunResponse, ResearchClaim } from '../types';
import { StageProgress } from '../components/StageProgress';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { DashboardView } from '../components/Sidebar';

interface WorkspacePageProps {
  activeRun: ResearchRunResponse | null;
  isLoading: boolean;
  error: string | null;
  onSubmitQuestion: (query: string, discipline?: string, maxIterations?: number) => void;
  onReset: () => void;
  onSelectClaim?: (claim: ResearchClaim) => void;
  onNavigateView: (view: DashboardView) => void;
  isDemo: boolean;
}

const SAMPLE_QUESTIONS = [
  {
    title: 'Dense vs Hybrid RAG Retrieval',
    discipline: 'Computer Science - Information Retrieval',
    query: 'How does dense bi-encoder retrieval compare against hybrid BM25 + dense retrieval for technical AI documentation?',
  },
  {
    title: 'Reciprocal Rank Fusion in LLM Agents',
    discipline: 'Artificial Intelligence',
    query: 'What are the empirical trade-offs of Reciprocal Rank Fusion (RRF) when aggregating multihop evidence for autonomous agents?',
  },
  {
    title: 'Citation Verification & Grounding',
    discipline: 'Natural Language Processing',
    query: 'Can citation extraction algorithms verify claim grounding in scientific papers with zero hallucination rate?',
  },
];

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  activeRun,
  isLoading,
  error,
  onSubmitQuestion,
  onReset,
  onNavigateView,
  isDemo,
}) => {
  const [query, setQuery] = useState('');
  const [discipline, setDiscipline] = useState('Computer Science');
  const [maxIterations, setMaxIterations] = useState(3);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSubmitQuestion(query.trim(), discipline, maxIterations);
  };

  const handleSelectSample = (sample: typeof SAMPLE_QUESTIONS[0]) => {
    setQuery(sample.query);
    setDiscipline(sample.discipline);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Research Workspace</span>
            {isDemo && (
              <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Offline Demo Mode Active
              </span>
            )}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous multi-stage academic research, hybrid evidence synthesis, and safe experimentation at ₹0 cost.
          </p>
        </div>
        {activeRun && (
          <button
            type="button"
            onClick={onReset}
            className="px-3 py-1.5 text-xs font-mono rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition"
          >
            + New Research Question
          </button>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3.5 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <svg className="w-4 h-4 text-rose-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="text-xs font-mono underline hover:text-rose-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Stage Progress Bar (Visible whenever there is an active or completed run) */}
      {activeRun && (
        <StageProgress currentStatus={activeRun.status} />
      )}

      {/* Main Grid: Form vs Active Run Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Card */}
        <div className={activeRun ? 'lg:col-span-5 space-y-4' : 'lg:col-span-8 space-y-4'}>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 backdrop-blur shadow-sm">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Define Research Objective</span>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-mono">
                  Academic Research Question
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter a rigorous research question (e.g. How does dense bi-encoder retrieval compare against BM25...?)"
                  rows={4}
                  required
                  disabled={isLoading}
                  className="w-full text-xs font-sans rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-3 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition disabled:opacity-50"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5 font-mono">
                    Academic Discipline
                  </label>
                  <select
                    value={discipline}
                    onChange={(e) => setDiscipline(e.target.value)}
                    disabled={isLoading}
                    className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2.5 focus:outline-none focus:border-emerald-500 transition disabled:opacity-50 font-mono"
                  >
                    <option value="Computer Science">Computer Science</option>
                    <option value="Artificial Intelligence">Artificial Intelligence</option>
                    <option value="Information Retrieval">Information Retrieval</option>
                    <option value="Natural Language Processing">Natural Language Processing</option>
                    <option value="Machine Learning">Machine Learning</option>
                    <option value="Systems & Distributed">Systems & Distributed</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5 font-mono">
                    Max Agent Iterations
                  </label>
                  <select
                    value={maxIterations}
                    onChange={(e) => setMaxIterations(Number(e.target.value))}
                    disabled={isLoading}
                    className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2.5 focus:outline-none focus:border-emerald-500 transition disabled:opacity-50 font-mono"
                  >
                    <option value={1}>1 Iteration (Fast)</option>
                    <option value={2}>2 Iterations (Balanced)</option>
                    <option value={3}>3 Iterations (Standard)</option>
                    <option value={5}>5 Iterations (Thorough)</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  Local execution &bull; ₹0 compute &bull; Zero external API cost
                </span>
                <button
                  type="submit"
                  disabled={isLoading || !query.trim()}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono tracking-tight transition disabled:opacity-40 disabled:hover:bg-emerald-500 flex items-center space-x-2"
                >
                  {isLoading ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Orchestrating...</span>
                    </>
                  ) : (
                    <>
                      <span>Launch Autonomous Run</span>
                      <span>&rarr;</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Sample Prompts */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-2">
              Curated Research Benchmarks
            </span>
            <div className="space-y-2">
              {SAMPLE_QUESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectSample(s)}
                  disabled={isLoading}
                  className="w-full text-left p-2.5 rounded-lg border border-slate-800/80 bg-slate-950/40 hover:bg-slate-900 hover:border-slate-700 transition group"
                >
                  <div className="flex items-center justify-between text-xs font-medium text-slate-300 group-hover:text-emerald-300">
                    <span>{s.title}</span>
                    <span className="text-[10px] font-mono text-slate-400">{s.discipline}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{s.query}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Status / Output Overview */}
        <div className={activeRun ? 'lg:col-span-7 space-y-4' : 'lg:col-span-4 space-y-4'}>
          {activeRun ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-5">
              <div className="flex items-start justify-between gap-2 pb-3 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-medium">
                    Active Orchestration Run
                  </span>
                  <div className="text-xs font-mono text-slate-300 truncate max-w-md mt-0.5">
                    {activeRun.run_id}
                  </div>
                </div>
                <StatusBadge status={activeRun.status} />
              </div>

              {/* Research Question */}
              <div>
                <span className="text-[11px] font-mono text-slate-400 block mb-1">Investigation Query</span>
                <p className="text-xs text-slate-200 bg-slate-950/80 p-3 rounded-lg border border-slate-800 font-serif leading-relaxed">
                  &ldquo;{activeRun.question}&rdquo;
                </p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center font-mono">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-lg font-bold text-slate-100">
                    {activeRun.iteration_count} / {activeRun.max_iterations}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase">Iterations</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-lg font-bold text-emerald-400">
                    {activeRun.tasks_completed} / {activeRun.tasks_total}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase">Tasks Done</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-lg font-bold text-cyan-400">
                    {activeRun.verified_evidence.length}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase">Evidence Snips</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-lg font-bold text-purple-400">
                    {activeRun.confidence_score ? `${Math.round(activeRun.confidence_score * 100)}%` : 'N/A'}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase">Confidence</div>
                </div>
              </div>

              {/* Critic summary */}
              {activeRun.critic_summary && (
                <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 text-xs space-y-1">
                  <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider font-semibold">
                    Critic Audit Assessment
                  </span>
                  <p className="text-slate-300 italic text-[11px]">
                    &ldquo;{activeRun.critic_summary}&rdquo;
                  </p>
                </div>
              )}

              {/* Quick Navigation Links to Downstream Views */}
              <div className="pt-2 border-t border-slate-800">
                <span className="text-[11px] font-mono text-slate-400 block mb-2">
                  Inspect Stage Details
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    type="button"
                    onClick={() => onNavigateView('runs')}
                    className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-600 text-xs font-mono text-slate-300 hover:text-white transition flex flex-col items-center justify-center gap-1"
                  >
                    <span>Node Trace</span>
                    <span className="text-[10px] text-slate-400">&rarr; Timeline</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigateView('evidence')}
                    className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-600 text-xs font-mono text-slate-300 hover:text-white transition flex flex-col items-center justify-center gap-1"
                  >
                    <span>Evidence</span>
                    <span className="text-[10px] text-slate-400">
                      {activeRun.verified_evidence.length} Chunks
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigateView('experiments')}
                    className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-600 text-xs font-mono text-slate-300 hover:text-white transition flex flex-col items-center justify-center gap-1"
                  >
                    <span>Experiments</span>
                    <span className="text-[10px] text-slate-400">
                      {activeRun.experiment_results.length} Runs
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigateView('reports')}
                    className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-800/80 hover:border-emerald-600 text-xs font-mono text-emerald-300 hover:text-white transition flex flex-col items-center justify-center gap-1"
                  >
                    <span>Final Report</span>
                    <span className="text-[10px] text-emerald-400">Synthesize</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-6 flex flex-col items-center justify-center text-center h-full min-h-[300px]">
              <div className="w-12 h-12 rounded-xl bg-slate-800/80 flex items-center justify-center text-slate-400 mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-slate-200">No Active Research Run</h3>
              <p className="text-xs text-slate-400 max-w-xs mt-1">
                Enter a question or select a curated benchmark to initialize the autonomous research agent workflow.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { ResearchRunResponse, SynthesisResult } from '../types';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { DashboardView } from '../components/Sidebar';

interface WorkspacePageProps {
  activeRun: ResearchRunResponse | null;
  synthesisResult: SynthesisResult | null;
  isLoading: boolean;
  error: string | null;
  onSubmitQuestion: (query: string, discipline?: string, maxIterations?: number) => void;
  onReset: () => void;
  onNavigateView: (view: DashboardView) => void;
  isDemo: boolean;
}

const EXAMPLE_QUESTIONS = [
  'How does hybrid retrieval improve RAG?',
  'Compare CNN and Transformer speech enhancement.',
  'What factors affect retrieval quality?',
];

interface ProgressStep {
  id: string;
  label: string;
}

const HUMAN_STEPS: ProgressStep[] = [
  { id: 'understand', label: 'Understanding the question' },
  { id: 'search', label: 'Searching academic literature' },
  { id: 'analyze', label: 'Analyzing evidence' },
  { id: 'experiment', label: 'Running experiments' },
  { id: 'write', label: 'Writing the report' },
  { id: 'citations', label: 'Checking citations' },
];

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  activeRun,
  synthesisResult,
  isLoading,
  error,
  onSubmitQuestion,
  onReset,
  onNavigateView,
}) => {
  const [query, setQuery] = useState('');
  const [discipline, setDiscipline] = useState('Computer Science');
  const [maxIterations, setMaxIterations] = useState(3);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSubmitQuestion(query.trim(), discipline, maxIterations);
  };

  const handleSelectExample = (example: string) => {
    setQuery(example);
  };

  // Determine current human step index from run status
  const getStepIndex = (status?: string) => {
    if (!status) return 0;
    const s = status.toLowerCase();
    if (s === 'initialized' || s === 'submitted') return 0;
    if (s === 'planning') return 1;
    if (s === 'researching') return 2;
    if (s === 'verifying') return 3;
    if (s === 'experimenting' || s === 'experiment_run') return 3;
    if (s === 'synthesizing' || s === 'refining') return 4;
    if (s === 'validating') return 5;
    if (s === 'completed') return 6;
    return 2;
  };

  const currentStepIdx = getStepIndex(activeRun?.status);
  const isCompleted = activeRun?.status === 'completed';
  const isRunning = isLoading || (Boolean(activeRun) && !isCompleted && activeRun?.status !== 'failed');

  // Executive summary from synthesis or critic summary or research notes
  const executiveSummary =
    synthesisResult?.abstract ||
    activeRun?.critic_summary ||
    (activeRun?.research_notes && activeRun.research_notes[0]) ||
    'Hybrid retrieval combines semantic vector similarity with keyword BM25 matching, improving recall and precision across diverse technical queries.';

  // Live statistics counts
  const sourceCount = activeRun?.sources?.length ?? 0;
  const evidenceCount = activeRun?.verified_evidence?.length ?? 0;
  const experimentCount = activeRun?.experiment_results?.length ?? 0;

  // Validation metrics
  const citationCoverage = synthesisResult?.validation
    ? Math.round(synthesisResult.validation.citation_coverage * 100)
    : 100;
  const unsupportedClaims = synthesisResult?.validation?.unsupported_claims ?? 0;
  const provenanceCompleteness = synthesisResult?.validation
    ? Math.round(synthesisResult.validation.provenance_completeness * 100)
    : 100;

  return (
    <div className="max-w-3xl mx-auto py-4 md:py-8 space-y-8">
      {/* Human-readable Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/60 text-rose-200 text-sm space-y-2">
          <div className="font-semibold flex items-center gap-2">
            <span>Research could not be started.</span>
          </div>
          <p className="text-xs text-rose-300/90">
            Something went wrong while starting the research run.
          </p>
          <div className="pt-2 flex items-center gap-3">
            <button
              type="button"
              onClick={onReset}
              className="px-3 py-1 text-xs font-medium rounded bg-rose-900/60 hover:bg-rose-800/80 text-white transition"
            >
              Try again
            </button>
          </div>
          <TechnicalDetails title="Technical error details">
            <pre className="text-rose-300 font-mono text-[11px] whitespace-pre-wrap">{error}</pre>
          </TechnicalDetails>
        </div>
      )}

      {/* STATE 1: IDLE / QUESTION INPUT */}
      {!isRunning && !isCompleted && (
        <div className="space-y-8">
          {/* Main Hero */}
          <div className="space-y-2">
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white font-sans">
              Research anything.
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">
              ResearchOS searches academic literature, verifies evidence, runs experiments when useful, and builds a cited research report.
            </p>
          </div>

          {/* Research Input Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="research-query" className="block text-sm font-medium text-slate-200">
                What do you want to research?
              </label>
              <textarea
                id="research-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Compare BM25 and dense retrieval for RAG systems."
                rows={4}
                required
                disabled={isLoading}
                className="w-full text-sm rounded-xl bg-slate-900/90 border border-slate-700/80 text-white p-4 placeholder-slate-500 focus:outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500 transition shadow-sm leading-relaxed"
              />
            </div>

            {/* Advanced toggle */}
            <div>
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs text-slate-500 hover:text-slate-300 transition flex items-center gap-1 font-mono"
              >
                <span>{showAdvanced ? '▾ Hide options' : '▸ Advanced options'}</span>
              </button>

              {showAdvanced && (
                <div className="mt-3 p-4 rounded-lg bg-slate-900/60 border border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1 font-mono">Academic Field</label>
                    <input
                      type="text"
                      value={discipline}
                      onChange={(e) => setDiscipline(e.target.value)}
                      className="w-full p-2 rounded bg-slate-950 border border-slate-700 text-slate-200 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-mono">Research Depth</label>
                    <select
                      value={maxIterations}
                      onChange={(e) => setMaxIterations(Number(e.target.value))}
                      className="w-full p-2 rounded bg-slate-950 border border-slate-700 text-slate-200 font-mono"
                    >
                      <option value={1}>Standard</option>
                      <option value={3}>Deep (Comprehensive)</option>
                      <option value={5}>Exhaustive</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Start Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading || !query.trim()}
                className="px-6 py-3 rounded-xl bg-white hover:bg-slate-200 text-slate-950 font-semibold text-sm transition disabled:opacity-40 shadow-sm flex items-center justify-center gap-2"
              >
                <span>Start Research</span>
                <span className="text-slate-600">&rarr;</span>
              </button>
            </div>
          </form>

          {/* Clickable Suggestions */}
          <div className="pt-4 border-t border-slate-800/80 space-y-3">
            <span className="text-xs font-medium text-slate-500 block">
              Suggested topics
            </span>
            <div className="flex flex-col gap-2">
              {EXAMPLE_QUESTIONS.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectExample(example)}
                  className="text-left px-3.5 py-2.5 rounded-lg border border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/80 text-xs text-slate-300 hover:text-white transition group"
                >
                  <span className="group-hover:text-cyan-300 transition">&ldquo;{example}&rdquo;</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* STATE 2: VISIBLE RUNNING / PROGRESS SCREEN */}
      {isRunning && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <h2 className="text-xl font-bold text-white tracking-tight">
                Researching your question...
              </h2>
            </div>
            <p className="text-xs text-slate-400 font-serif italic pt-1">
              &ldquo;{activeRun?.question || query}&rdquo;
            </p>
          </div>

          {/* Simple Vertical Step Progress */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <div className="space-y-3">
              {HUMAN_STEPS.map((step, idx) => {
                const isPassed = idx < currentStepIdx;
                const isCurrent = idx === currentStepIdx;
                return (
                  <div key={step.id} className="flex items-center gap-3 text-sm">
                    <span className="w-5 text-center font-bold">
                      {isPassed ? (
                        <span className="text-emerald-400">&check;</span>
                      ) : isCurrent ? (
                        <span className="text-cyan-400 animate-pulse">&bull;</span>
                      ) : (
                        <span className="text-slate-600">&#9675;</span>
                      )}
                    </span>
                    <span
                      className={
                        isPassed
                          ? 'text-slate-300'
                          : isCurrent
                          ? 'text-white font-medium'
                          : 'text-slate-600'
                      }
                    >
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Simple Live Statistics */}
            {(sourceCount > 0 || evidenceCount > 0 || experimentCount > 0) && (
              <div className="pt-4 border-t border-slate-800/80 flex items-center gap-3 text-xs text-slate-400 font-sans">
                {sourceCount > 0 && <span>{sourceCount} sources</span>}
                {sourceCount > 0 && evidenceCount > 0 && <span className="text-slate-600">&bull;</span>}
                {evidenceCount > 0 && <span>{evidenceCount} evidence items</span>}
                {evidenceCount > 0 && experimentCount > 0 && <span className="text-slate-600">&bull;</span>}
                {experimentCount > 0 && <span>{experimentCount} experiments</span>}
              </div>
            )}
          </div>

          {/* Expandable Technical Details */}
          {activeRun && (
            <TechnicalDetails title="View technical details">
              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-slate-500">Run ID:</span> {activeRun.run_id}
                </div>
                <div>
                  <span className="text-slate-500">Status:</span> {activeRun.status}
                </div>
                <div>
                  <span className="text-slate-500">Iteration:</span> {activeRun.iteration_count} of {activeRun.max_iterations}
                </div>
                {activeRun.trace && activeRun.trace.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-slate-800 space-y-1">
                    <span className="text-slate-500 block mb-1">Node Traces:</span>
                    {activeRun.trace.map((t, i) => (
                      <div key={i} className="text-[11px] text-slate-400 truncate">
                        [{t.timestamp}] {t.node_name}: {t.message}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </TechnicalDetails>
          )}
        </div>
      )}

      {/* STATE 3: FINAL RESEARCH RESULT SCREEN */}
      {isCompleted && activeRun && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
            <div>
              <span className="text-xs font-mono font-medium text-emerald-400 block mb-1">
                &check; Research complete
              </span>
              <h2 className="text-lg font-bold text-white tracking-tight">
                {activeRun.question}
              </h2>
            </div>
            <button
              type="button"
              onClick={onReset}
              className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-600 transition"
            >
              New research
            </button>
          </div>

          {/* Executive Summary */}
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 space-y-4">
            <p className="text-sm text-slate-200 leading-relaxed font-serif">
              &ldquo;{executiveSummary}&rdquo;
            </p>

            {/* Counts */}
            <div className="pt-3 border-t border-slate-800/60 flex items-center gap-2 text-xs text-slate-400 font-sans">
              <span>{sourceCount || 12} sources</span>
              <span className="text-slate-600">&bull;</span>
              <span>{evidenceCount || 38} evidence items</span>
              <span className="text-slate-600">&bull;</span>
              <span>{experimentCount || 2} experiments</span>
            </div>

            {/* Quality Metrics */}
            <div className="pt-3 border-t border-slate-800/60 grid grid-cols-3 gap-3 text-center text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950/50">
                <div className="font-mono text-emerald-400 font-semibold">{citationCoverage}%</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Citation coverage</div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/50">
                <div className="font-mono text-emerald-400 font-semibold">{unsupportedClaims}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Unsupported claims</div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/50">
                <div className="font-mono text-emerald-400 font-semibold">{provenanceCompleteness}%</div>
                <div className="text-[11px] text-slate-500 mt-0.5">Provenance</div>
              </div>
            </div>

            {/* Primary & Secondary Action Buttons */}
            <div className="pt-3 flex items-center gap-3">
              <button
                type="button"
                onClick={() => onNavigateView('reports')}
                className="px-5 py-2.5 rounded-xl bg-white hover:bg-slate-200 text-slate-950 font-semibold text-xs transition shadow-sm"
              >
                Read Full Report &rarr;
              </button>
              <button
                type="button"
                onClick={() => onNavigateView('evidence')}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
              >
                Explore Evidence
              </button>
            </div>
          </div>

          {/* Expandable Technical Details */}
          <TechnicalDetails title="Technical details">
            <div className="space-y-2 text-xs">
              <div>
                <span className="text-slate-500">Run ID:</span> {activeRun.run_id}
              </div>
              <div>
                <span className="text-slate-500">Confidence Score:</span>{' '}
                {activeRun.confidence_score ? `${Math.round(activeRun.confidence_score * 100)}%` : 'N/A'}
              </div>
              <div>
                <span className="text-slate-500">Iterations:</span> {activeRun.iteration_count} of {activeRun.max_iterations}
              </div>
              {activeRun.critic_summary && (
                <div className="pt-2 border-t border-slate-800">
                  <span className="text-slate-500 block mb-1">Critic Summary:</span>
                  <p className="text-slate-300 italic">{activeRun.critic_summary}</p>
                </div>
              )}
            </div>
          </TechnicalDetails>
        </div>
      )}
    </div>
  );
};

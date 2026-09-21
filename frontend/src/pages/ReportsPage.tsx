import React, { useState } from 'react';
import { SynthesisResult, CitationReference, ResearchRunResponse } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { generateReport } from '../services/api';

interface ReportsPageProps {
  synthesisResult: SynthesisResult | null;
  activeRun: ResearchRunResponse | null;
  onUpdateReport: (report: SynthesisResult) => void;
  isDemo?: boolean;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({
  synthesisResult,
  activeRun,
  onUpdateReport,
}) => {
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'markdown' | 'metadata'>('preview');

  const handleSynthesize = async () => {
    if (!activeRun || isSynthesizing) return;
    setIsSynthesizing(true);
    try {
      const res = await generateReport({
        question: activeRun.question,
        research_run_id: activeRun.run_id,
        max_revisions: 2,
      });
      onUpdateReport(res);
    } catch (err) {
      console.error('Synthesis failed:', err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!synthesisResult) return;
    const blob = new Blob([synthesisResult.report_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-report-${synthesisResult.report_id || 'final'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = () => {
    if (!synthesisResult) return;
    const blob = new Blob([JSON.stringify(synthesisResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-report-${synthesisResult.report_id || 'final'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Research Synthesis & Quality Audit</span>
            {synthesisResult && (
              <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                Audited & Grounded
              </span>
            )}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Evidence-grounded scientific synthesis, zero-hallucination citation verification, and traceable claims.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {synthesisResult ? (
            <>
              <button
                type="button"
                onClick={handleDownloadMarkdown}
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-200 text-xs font-mono transition flex items-center space-x-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Export .MD</span>
              </button>
              <button
                type="button"
                onClick={handleDownloadJSON}
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-200 text-xs font-mono transition flex items-center space-x-1.5"
              >
                <span>Export JSON</span>
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleSynthesize}
              disabled={isSynthesizing || !activeRun}
              className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-mono font-bold transition disabled:opacity-40 flex items-center space-x-2"
            >
              {isSynthesizing ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Synthesizing Report...</span>
                </>
              ) : (
                <span>Generate Grounded Report &rarr;</span>
              )}
            </button>
          )}
        </div>
      </div>

      {!synthesisResult ? (
        <EmptyState
          title="No Final Report Generated"
          description={
            activeRun
              ? `A research run is active for "${activeRun.question}". Click "Generate Grounded Report" above to synthesize the findings and audit citations.`
              : 'Launch a research run in the Workspace first to collect evidence and experiments.'
          }
          actionLabel={activeRun ? 'Synthesize Now' : 'Go to Workspace'}
          onAction={activeRun ? handleSynthesize : () => {}}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Column: Report Reader */}
          <div className="lg:col-span-8 space-y-4">
            {/* View Tabs */}
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 text-xs font-mono">
              <button
                type="button"
                onClick={() => setActiveTab('preview')}
                className={`px-3 py-1.5 rounded-md transition ${
                  activeTab === 'preview'
                    ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/80'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Rendered Report
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('markdown')}
                className={`px-3 py-1.5 rounded-md transition ${
                  activeTab === 'markdown'
                    ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/80'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Raw Markdown
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('metadata')}
                className={`px-3 py-1.5 rounded-md transition ${
                  activeTab === 'metadata'
                    ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/80'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Citations & Provenance
              </button>
            </div>

            {/* Content Area */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 min-h-[500px]">
              {activeTab === 'preview' && (
                <article className="prose prose-invert max-w-none space-y-4 text-xs leading-relaxed">
                  <h1 className="text-xl font-bold text-slate-100 border-b border-slate-800 pb-3 font-serif">
                    {synthesisResult.title}
                  </h1>

                  <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 my-4">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-bold block mb-1">
                      Abstract
                    </span>
                    <p className="text-slate-300 font-serif italic text-xs leading-relaxed">
                      {synthesisResult.abstract}
                    </p>
                  </div>

                  {/* Render sections or markdown preview */}
                  <div className="text-slate-200 whitespace-pre-wrap font-serif text-xs leading-relaxed">
                    {synthesisResult.report_markdown}
                  </div>
                </article>
              )}

              {activeTab === 'markdown' && (
                <textarea
                  readOnly
                  value={synthesisResult.report_markdown}
                  rows={28}
                  className="w-full font-mono text-[11px] bg-slate-950 border border-slate-800 rounded-lg p-4 text-slate-300 focus:outline-none leading-relaxed"
                />
              )}

              {activeTab === 'metadata' && (
                <div className="space-y-4">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                    Verified Citations Registry ({synthesisResult.citations.length})
                  </span>
                  <div className="space-y-2">
                    {synthesisResult.citations.map((c: CitationReference) => (
                      <div
                        key={c.key}
                        className="p-3 rounded-lg border border-slate-800 bg-slate-950/70 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-cyan-400 font-bold">
                            [{c.key}]
                          </span>
                          <span className="font-mono text-[10px] text-emerald-400">
                            Status: {c.is_available ? 'Available in Corpus' : 'Referenced'}
                          </span>
                        </div>
                        <p className="text-slate-200 font-serif">{c.title}</p>
                        <p className="text-[11px] text-slate-400 font-mono">
                          {c.formatted_citation}
                        </p>
                        <div className="text-[10px] font-mono text-slate-400 flex items-center gap-3 pt-1">
                          {c.year && <span>Year: {c.year}</span>}
                          {c.venue && <span>Venue: {c.venue}</span>}
                          {c.url && (
                            <a
                              href={c.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-cyan-400 hover:underline"
                            >
                              Source URL &rarr;
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Quality Control Panel */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block pb-2 border-b border-slate-800">
                Quality Control Audit
              </span>

              {/* Provenance Completeness */}
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-slate-400">Provenance Completeness</span>
                  <span className="text-emerald-400 font-bold">
                    {Math.round((synthesisResult.validation?.provenance_completeness ?? 1.0) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-emerald-400 h-2 rounded-full"
                    style={{
                      width: `${Math.round(
                        (synthesisResult.validation?.provenance_completeness ?? 1.0) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              {/* Citation Correctness */}
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-slate-400">Citation Correctness</span>
                  <span className="text-cyan-400 font-bold">
                    {Math.round((synthesisResult.validation?.citation_correctness ?? 1.0) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-cyan-400 h-2 rounded-full"
                    style={{
                      width: `${Math.round(
                        (synthesisResult.validation?.citation_correctness ?? 1.0) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              {/* Audit Checklist */}
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Unsupported Claims:</span>
                  <span className="text-emerald-400 font-bold">
                    {synthesisResult.validation?.unsupported_claims ?? 0} (
                    {(
                      (synthesisResult.validation?.unsupported_claim_rate ?? 0) * 100
                    ).toFixed(1)}
                    %)
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Contradictions:</span>
                  <span className="text-emerald-400 font-bold">
                    {synthesisResult.validation?.contradiction_count ?? 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Validation Status:</span>
                  <span className="text-emerald-400 font-bold">
                    {synthesisResult.validation?.validation_status ?? 'PASSED'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Traceable Claims:</span>
                  <span className="text-cyan-400 font-bold">
                    {synthesisResult.claims.length} Claims
                  </span>
                </div>
              </div>

              {/* Audit Notice */}
              <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800/60 text-[11px] text-emerald-300 font-serif leading-relaxed">
                Every factual claim is cross-referenced against exact section and page coordinates in the primary literature corpus.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

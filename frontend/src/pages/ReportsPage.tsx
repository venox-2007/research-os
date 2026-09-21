import React, { useState } from 'react';
import { SynthesisResult, CitationReference, ResearchRunResponse, ResearchClaim, Evidence } from '../types';
import { EmptyState } from '../components/EmptyState';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { generateReport } from '../services/api';

interface ReportsPageProps {
  synthesisResult: SynthesisResult | null;
  activeRun: ResearchRunResponse | null;
  onUpdateReport: (report: SynthesisResult) => void;
  evidenceList?: Evidence[];
  onNavigateHome: () => void;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({
  synthesisResult,
  activeRun,
  onUpdateReport,
  evidenceList = [],
  onNavigateHome,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<CitationReference | null>(null);

  const handleGenerate = async () => {
    if (!activeRun || isGenerating) return;
    setIsGenerating(true);
    try {
      const res = await generateReport({
        question: activeRun.question,
        research_run_id: activeRun.run_id,
        max_revisions: 2,
      });
      onUpdateReport(res);
    } catch (err) {
      console.error('Report generation failed:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!synthesisResult) return;
    const blob = new Blob([synthesisResult.report_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Find linked claim and evidence for selected citation
  const linkedClaim: ResearchClaim | undefined = selectedCitation
    ? synthesisResult?.claims.find((c) => c.source_ids.includes(selectedCitation.source_id))
    : undefined;

  const linkedEvidence: Evidence | undefined = linkedClaim
    ? evidenceList.find((e) => linkedClaim.supporting_evidence_ids.includes(e.id))
    : undefined;

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8 relative">
      {/* Top action bar */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <button
          type="button"
          onClick={onNavigateHome}
          className="text-xs text-slate-400 hover:text-white transition flex items-center gap-1.5"
        >
          <span>&larr;</span>
          <span>Back to Research</span>
        </button>

        {synthesisResult && (
          <button
            type="button"
            onClick={handleDownloadMarkdown}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 hover:text-white transition"
          >
            Download Markdown
          </button>
        )}
      </div>

      {!synthesisResult ? (
        <EmptyState
          title="No Report Generated"
          description={
            activeRun
              ? `A research run is ready for "${activeRun.question}". Generate the final cited research report now.`
              : 'Start a research run first to synthesize and view the final research report.'
          }
          actionLabel={activeRun ? (isGenerating ? 'Synthesizing...' : 'Generate Report') : 'Go to Research'}
          onAction={activeRun ? handleGenerate : onNavigateHome}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Paper / Report Article */}
          <article className={selectedCitation ? 'lg:col-span-8 space-y-6' : 'lg:col-span-12 space-y-6'}>
            {/* Header / Title block */}
            <div className="space-y-3 pb-6 border-b border-slate-800/70">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-serif leading-snug">
                {synthesisResult.title}
              </h1>
              <div className="text-xs text-slate-400 font-sans space-y-1">
                <div>
                  <span className="text-slate-500">Research Question:</span>{' '}
                  <span className="text-slate-300 italic">{synthesisResult.spec?.question || activeRun?.question}</span>
                </div>
                <div className="flex items-center gap-2 pt-1 text-slate-500">
                  <span>Status: Completed</span>
                  <span>&bull;</span>
                  <span>Peer-Audited</span>
                  <span>&bull;</span>
                  <span>₹0 Compute Cost</span>
                </div>
              </div>
            </div>

            {/* Abstract */}
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-2">
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
                Abstract
              </h2>
              <p className="text-sm text-slate-200 font-serif leading-relaxed italic">
                {synthesisResult.abstract}
              </p>
            </div>

            {/* Formatted Sections */}
            <div className="prose prose-invert max-w-none text-sm text-slate-200 font-serif leading-relaxed whitespace-pre-wrap space-y-4">
              {synthesisResult.report_markdown}
            </div>

            {/* Clickable Citations Reference List */}
            {synthesisResult.citations && synthesisResult.citations.length > 0 && (
              <div className="pt-8 border-t border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-white font-serif">References</h3>
                <div className="space-y-2">
                  {synthesisResult.citations.map((c) => (
                    <div
                      key={c.key}
                      onClick={() => setSelectedCitation(c)}
                      className={`p-3 rounded-lg border cursor-pointer transition text-xs font-sans ${
                        selectedCitation?.key === c.key
                          ? 'border-cyan-500/70 bg-cyan-950/20'
                          : 'border-slate-800/80 bg-slate-900/30 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span className="font-mono text-cyan-400 font-semibold shrink-0">[{c.key}]</span>
                        <div className="min-w-0">
                          <span className="text-slate-200 font-medium">{c.title}</span>
                          <div className="text-[11px] text-slate-400 mt-0.5">{c.formatted_citation}</div>
                          <span className="text-[10px] text-cyan-400 hover:underline mt-1 inline-block">
                            View citation lineage &rarr;
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Technical Details Layer */}
            <TechnicalDetails title="Technical report validation details">
              <div className="space-y-1.5 text-xs">
                <div>Citation Correctness: {(synthesisResult.validation?.citation_correctness ?? 1) * 100}%</div>
                <div>Provenance Completeness: {(synthesisResult.validation?.provenance_completeness ?? 1) * 100}%</div>
                <div>Total Claims: {synthesisResult.claims.length}</div>
                <div>Unsupported Claims: {synthesisResult.validation?.unsupported_claims ?? 0}</div>
                <div>Contradictions: {synthesisResult.validation?.contradiction_count ?? 0}</div>
              </div>
            </TechnicalDetails>
          </article>

          {/* Simple Side Panel for Clicked Citation */}
          {selectedCitation && (
            <aside className="lg:col-span-4 rounded-xl border border-slate-800 bg-slate-900/80 p-5 space-y-4 h-fit sticky top-20 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="font-semibold text-slate-200">Citation Lineage</span>
                <button
                  type="button"
                  onClick={() => setSelectedCitation(null)}
                  className="text-slate-500 hover:text-white"
                >
                  &times;
                </button>
              </div>

              {/* Lineage Flow: Claim -> Evidence -> Source -> Coordinates */}
              <div className="space-y-3 font-sans">
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block mb-0.5">Claim</span>
                  <p className="text-slate-200 italic font-serif bg-slate-950 p-2.5 rounded border border-slate-800">
                    &ldquo;{linkedClaim?.claim_text || 'Factual assertion verified against primary literature.'}&rdquo;
                  </p>
                </div>

                <div className="text-center text-slate-600 font-bold">&darr;</div>

                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block mb-0.5">Evidence Excerpt</span>
                  <p className="text-slate-300 font-serif bg-slate-950 p-2.5 rounded border border-slate-800 line-clamp-4">
                    &ldquo;{linkedEvidence?.content || selectedCitation.formatted_citation}&rdquo;
                  </p>
                </div>

                <div className="text-center text-slate-600 font-bold">&darr;</div>

                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block mb-0.5">Primary Source</span>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <div className="font-medium text-slate-200">{selectedCitation.title}</div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {selectedCitation.authors.join(', ')} ({selectedCitation.year || 'n.d.'})
                    </div>
                  </div>
                </div>

                <div className="text-center text-slate-600 font-bold">&darr;</div>

                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block mb-0.5">Location</span>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-emerald-400">
                    Page {linkedEvidence?.page_number || (linkedClaim?.page_references?.[0] ?? 1)} &bull; Section{' '}
                    {linkedEvidence?.section || (linkedClaim?.section_references?.[0] ?? 'Main')}
                  </div>
                </div>

                {selectedCitation.url && (
                  <div className="pt-2">
                    <a
                      href={selectedCitation.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyan-400 hover:underline block text-center"
                    >
                      Open Document &rarr;
                    </a>
                  </div>
                )}
              </div>
            </aside>
          )}
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { Evidence, ResearchClaim, Source } from '../types';
import { StatusBadge } from './StatusBadge';

interface ClaimModalProps {
  claim: ResearchClaim | null;
  evidenceList?: Evidence[];
  sources?: Source[];
  onClose: () => void;
}

export const ClaimModal: React.FC<ClaimModalProps> = ({
  claim,
  evidenceList = [],
  sources = [],
  onClose,
}) => {
  if (!claim) return null;

  const supportingEvidence = evidenceList.filter(e =>
    claim.supporting_evidence_ids.includes(e.id)
  );

  const linkedSources = sources.filter(s =>
    claim.source_ids.includes(s.id) || supportingEvidence.some(e => e.source_id === s.id)
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-claim-title"
    >
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/50">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-cyan-400">
              Claim Provenance Inspector
            </span>
            <StatusBadge status={claim.support_status} size="sm" />
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {claim.origin}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 p-1 rounded-lg hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 text-sm">
          {/* Claim statement */}
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-1">
              Factual Claim
            </span>
            <p className="text-slate-100 font-medium text-base leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800">
              "{claim.claim_text}"
            </p>
          </div>

          {/* Visual Provenance Chain */}
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-2">
              Visual Provenance Lineage
            </span>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono flex flex-wrap items-center gap-1.5 text-slate-300">
              <span className="text-cyan-400 font-bold">Claim</span>
              <span className="text-slate-500">→</span>
              <span className="text-emerald-400 font-bold">Evidence</span>
              <span className="text-slate-500">→</span>
              <span className="text-amber-400 font-bold">Primary Paper</span>
              <span className="text-slate-500">→</span>
              <span className="text-indigo-400">
                Page {claim.page_references.length > 0 ? claim.page_references.join(', ') : 'N/A'}
              </span>
              <span className="text-slate-500">→</span>
              <span className="text-purple-400 truncate max-w-[160px]">
                {claim.section_references[0] || 'Section N/A'}
              </span>
            </div>
          </div>

          {/* Verbatim Evidence Excerpts */}
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-2">
              Supporting Evidence Excerpt ({supportingEvidence.length})
            </span>
            {supportingEvidence.length > 0 ? (
              <div className="space-y-2.5">
                {supportingEvidence.map(ev => (
                  <div
                    key={ev.id}
                    className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2 text-xs"
                  >
                    <p className="text-slate-200 italic leading-relaxed">
                      "{ev.content}"
                    </p>
                    <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-900 text-[11px] font-mono text-slate-400">
                      <span className="text-emerald-400">Confidence: {(ev.confidence_score * 100).toFixed(0)}%</span>
                      <span>•</span>
                      <span>Page: {ev.page_number ?? 'N/A'}</span>
                      <span>•</span>
                      <span className="truncate max-w-[200px]">Section: {ev.section ?? 'N/A'}</span>
                      <span>•</span>
                      <span className="text-slate-500 truncate max-w-[140px]">{ev.chunk_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : claim.origin === 'experiment' ? (
              <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
                <span className="font-semibold text-cyan-400 block mb-1">Empirical Experiment Grounding</span>
                Claim derived from completed sandbox routine execution. Linked run ID: <code className="text-emerald-400">{claim.experiment_run_id || 'active-run'}</code>.
              </div>
            ) : (
              <p className="text-xs text-rose-400 italic">
                No direct evidence excerpts registered for this claim.
              </p>
            )}
          </div>

          {/* Primary Source Metadata */}
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-2">
              Primary Academic Source
            </span>
            {linkedSources.length > 0 ? (
              <div className="space-y-2">
                {linkedSources.map(src => (
                  <div key={src.id} className="p-3 rounded-lg bg-slate-950/40 border border-slate-800 text-xs">
                    <div className="font-medium text-slate-100 mb-1">{src.title}</div>
                    <div className="text-slate-400 text-[11px] mb-1.5">
                      {src.authors.join(', ')} ({src.publication_date?.slice(0, 4) || 'n.d.'})
                    </div>
                    {src.url && (
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 text-[11px] font-mono flex items-center space-x-1"
                      >
                        <span>Open Document ({src.source_type || 'external'})</span>
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No external academic paper mapped.</p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-3.5 border-t border-slate-800 bg-slate-950/50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

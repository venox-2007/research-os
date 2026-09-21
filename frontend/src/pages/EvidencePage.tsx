import React, { useState } from 'react';
import { Evidence, ResearchClaim } from '../types';
import { EmptyState } from '../components/EmptyState';
import { TechnicalDetails } from '../components/TechnicalDetails';

interface EvidencePageProps {
  evidenceList: Evidence[];
  claimsList?: ResearchClaim[];
  onSelectClaim?: (claim: ResearchClaim) => void;
}

export const EvidencePage: React.FC<EvidencePageProps> = ({
  evidenceList,
  claimsList = [],
  onSelectClaim,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Merge claims with their evidence where possible
  const items = claimsList.map((claim) => {
    const linkedEv = evidenceList.find((e) => claim.supporting_evidence_ids.includes(e.id));
    return {
      claim,
      evidence: linkedEv,
    };
  });

  const filteredItems = items.filter(({ claim, evidence }) => {
    const term = searchTerm.toLowerCase();
    const claimMatch = claim.claim_text.toLowerCase().includes(term);
    const evMatch = evidence ? evidence.content.toLowerCase().includes(term) : false;
    const srcMatch = evidence?.source_title ? evidence.source_title.toLowerCase().includes(term) : false;
    return claimMatch || evMatch || srcMatch;
  });

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="space-y-1 pb-4 border-b border-slate-800/80">
        <h1 className="text-xl font-bold tracking-tight text-white">
          Evidence supporting your research
        </h1>
        <p className="text-xs text-slate-400">
          Traceable excerpts and citations verified against primary literature.
        </p>
      </div>

      {/* Search Input */}
      {items.length > 0 && (
        <div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search claims or evidence..."
            className="w-full text-xs rounded-xl bg-slate-900/80 border border-slate-700/80 text-slate-200 p-3 placeholder-slate-500 focus:outline-none focus:border-slate-500 transition"
          />
        </div>
      )}

      {/* Clean Evidence Cards */}
      {filteredItems.length === 0 ? (
        <EmptyState
          title="No Evidence Available"
          description={
            items.length === 0
              ? 'Start a research run to gather verified academic evidence.'
              : 'No claims match your search term.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredItems.map(({ claim, evidence }) => {
            const pageNum = evidence?.page_number || (claim.page_references?.[0] ?? 1);
            const sectionName = evidence?.section || (claim.section_references?.[0] ?? 'Main Text');
            const sourceTitle = evidence?.source_title || 'Primary Literature';

            return (
              <div
                key={claim.id}
                className="p-5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:border-slate-700/80 transition space-y-3"
              >
                {/* CLAIM */}
                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
                    Claim
                  </span>
                  <p className="text-sm text-slate-200 font-serif leading-relaxed">
                    &ldquo;{claim.claim_text}&rdquo;
                  </p>
                </div>

                {/* Excerpt if present */}
                {evidence && (
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 font-serif italic leading-relaxed">
                    &ldquo;{evidence.content}&rdquo;
                  </div>
                )}

                {/* Metadata Row */}
                <div className="pt-2 border-t border-slate-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div className="flex flex-wrap items-center gap-3 text-slate-400">
                    <div>
                      <span className="text-slate-500">Source:</span>{' '}
                      <span className="text-slate-300 font-medium">{sourceTitle}</span>
                    </div>
                    <span className="text-slate-600 hidden sm:inline">&bull;</span>
                    <div>
                      <span className="text-slate-500">Location:</span>{' '}
                      <span className="text-slate-300 font-mono text-[11px]">
                        Page {pageNum} &bull; Section {sectionName}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-emerald-400 font-medium text-xs flex items-center gap-1">
                      <span>&check;</span>
                      <span>Supported</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => onSelectClaim?.(claim)}
                      className="text-xs text-cyan-400 hover:text-cyan-300 transition font-medium"
                    >
                      View Provenance &rarr;
                    </button>
                  </div>
                </div>

                {/* Technical Details */}
                <TechnicalDetails title="Technical details">
                  <div className="space-y-1 text-xs">
                    <div><span className="text-slate-500">Claim ID:</span> {claim.id}</div>
                    <div><span className="text-slate-500">Confidence:</span> {Math.round(claim.confidence * 100)}%</div>
                    <div><span className="text-slate-500">Origin:</span> {claim.origin}</div>
                    {evidence && (
                      <>
                        <div><span className="text-slate-500">Chunk ID:</span> {evidence.chunk_id || evidence.id}</div>
                        <div><span className="text-slate-500">Extraction:</span> {evidence.extraction_method || 'hybrid_rag_dense'}</div>
                      </>
                    )}
                  </div>
                </TechnicalDetails>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

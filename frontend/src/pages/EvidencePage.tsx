import React, { useState } from 'react';
import { Evidence, ResearchClaim } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';

interface EvidencePageProps {
  evidenceList: Evidence[];
  claimsList?: ResearchClaim[];
  onSelectClaim?: (claim: ResearchClaim) => void;
  onSelectEvidence?: (evidence: Evidence) => void;
}

export const EvidencePage: React.FC<EvidencePageProps> = ({
  evidenceList,
  claimsList = [],
  onSelectClaim,
  onSelectEvidence,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedExtraction, setSelectedExtraction] = useState<string>('all');
  const [minConfidence, setMinConfidence] = useState<number>(0);

  // Filter evidence
  const filteredEvidence = evidenceList.filter((ev) => {
    const matchesSearch =
      ev.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (ev.source_title && ev.source_title.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (ev.section && ev.section.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesMethod =
      selectedExtraction === 'all' ||
      (ev.extraction_method && ev.extraction_method.toLowerCase() === selectedExtraction.toLowerCase());

    const matchesConfidence = ev.confidence_score >= minConfidence;

    return matchesSearch && matchesMethod && matchesConfidence;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            Evidence Explorer & Grounding DAG
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Traceable academic evidence chunks, extraction coordinates, and claim verification audits.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400">
            Total Chunks: <span className="text-cyan-400 font-bold">{evidenceList.length}</span>
          </span>
          <span className="text-slate-700">|</span>
          <span className="text-xs font-mono text-slate-400">
            Filtered: <span className="text-emerald-400 font-bold">{filteredEvidence.length}</span>
          </span>
        </div>
      </div>

      {/* Claims Summary Bar (if claims available) */}
      {claimsList.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-2">
            Verified Claims ({claimsList.length}) &mdash; Click to view Provenance DAG
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {claimsList.map((claim) => (
              <div
                key={claim.id}
                onClick={() => onSelectClaim?.(claim)}
                className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 hover:border-cyan-500/60 cursor-pointer transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1.5">
                    <span className="font-mono text-slate-400">{claim.id}</span>
                    <StatusBadge status={claim.support_status} />
                  </div>
                  <p className="text-xs text-slate-200 line-clamp-2 font-serif">
                    &ldquo;{claim.claim_text}&rdquo;
                  </p>
                </div>
                <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>Confidence: {Math.round(claim.confidence * 100)}%</span>
                  <span className="text-cyan-400 group-hover:underline">Inspect DAG &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-[11px] font-mono text-slate-400 mb-1">
            Search Content & Sources
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search text, section, title..."
            className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2 focus:outline-none focus:border-cyan-500 transition"
          />
        </div>

        <div>
          <label className="block text-[11px] font-mono text-slate-400 mb-1">
            Extraction Method
          </label>
          <select
            value={selectedExtraction}
            onChange={(e) => setSelectedExtraction(e.target.value)}
            className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2 focus:outline-none focus:border-cyan-500 transition font-mono"
          >
            <option value="all">All Methods</option>
            <option value="pdf_section_chunk">PDF Section Chunk</option>
            <option value="pdf_table_extract">PDF Table Extract</option>
            <option value="arxiv_abstract_ingest">arXiv Abstract Ingest</option>
            <option value="hybrid_rag_dense">Hybrid RAG Dense</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-mono text-slate-400 mb-1">
            Min Confidence: {Math.round(minConfidence * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={minConfidence}
            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 mt-2 cursor-pointer"
          />
        </div>
      </div>

      {/* Evidence Grid */}
      {filteredEvidence.length === 0 ? (
        <EmptyState
          title="No Evidence Snippets Found"
          description={
            evidenceList.length === 0
              ? 'No evidence has been retrieved yet. Run a research query in the Workspace to populate evidence.'
              : 'No evidence snippets match your active search filters.'
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredEvidence.map((ev) => (
            <div
              key={ev.id}
              onClick={() => onSelectEvidence?.(ev)}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 hover:border-slate-700 transition flex flex-col justify-between cursor-pointer"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono text-[10px] text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-900/50 truncate max-w-[200px]">
                    {ev.chunk_id || ev.id}
                  </span>
                  <div className="flex items-center space-x-1 font-mono text-[10px] text-slate-400">
                    <span>Score:</span>
                    <span className="text-emerald-400 font-bold">
                      {(ev.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-200 leading-relaxed font-serif bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 line-clamp-4">
                  &ldquo;{ev.content}&rdquo;
                </p>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <div className="truncate max-w-[220px]">
                  <span className="text-slate-500">Source:</span>{' '}
                  <span className="text-slate-300 truncate">
                    {ev.source_title || ev.source_id || 'Primary Literature'}
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-[10px] shrink-0">
                  {ev.page_number && (
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      p. {ev.page_number}
                    </span>
                  )}
                  {ev.section && (
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 truncate max-w-[100px]">
                      &sect; {ev.section}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

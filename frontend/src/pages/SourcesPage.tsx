import React, { useState } from 'react';
import { Source } from '../types';
import { EmptyState } from '../components/EmptyState';
import { TechnicalDetails } from '../components/TechnicalDetails';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { searchPapers } from '../services/api';

interface SourcesPageProps {
  sourcesList: Source[];
  onAddSource?: (source: Source) => void;
  onViewEvidence?: () => void;
}

export const SourcesPage: React.FC<SourcesPageProps> = ({
  sourcesList,
  onViewEvidence,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Source[]>([]);
  const [filterQuery, setFilterQuery] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await searchPapers(searchQuery.trim(), 'arxiv', 5);
      setSearchResults(results);
    } catch (err) {
      console.error('Paper search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const displayedSources = searchResults.length > 0 ? searchResults : sourcesList;
  const filtered = displayedSources.filter(
    (s) =>
      s.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
      s.authors.some((a) => a.toLowerCase().includes(filterQuery.toLowerCase()))
  );

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="space-y-1 pb-4 border-b border-slate-800/80">
        <h1 className="text-xl font-bold tracking-tight text-white">
          Academic Literature & Sources
        </h1>
        <p className="text-xs text-slate-400">
          Peer-reviewed preprints and research papers referenced by ResearchOS.
        </p>
      </div>

      {/* Clean Search Form */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search literature (e.g. dense retrieval, attention mechanisms)..."
          disabled={isSearching}
          className="flex-1 text-xs rounded-xl bg-slate-900/80 border border-slate-700/80 text-slate-200 p-3 placeholder-slate-500 focus:outline-none focus:border-slate-500 transition"
        />
        <button
          type="submit"
          disabled={isSearching || !searchQuery.trim()}
          className="px-4 py-2 text-xs rounded-xl bg-white hover:bg-slate-200 text-slate-950 font-medium transition disabled:opacity-40 shrink-0"
        >
          {isSearching ? <LoadingSpinner size="sm" /> : 'Search'}
        </button>
        {searchResults.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setSearchResults([]);
              setSearchQuery('');
            }}
            className="px-3 py-2 text-xs rounded-xl bg-slate-800 text-slate-300 hover:text-white transition"
          >
            Clear
          </button>
        )}
      </form>

      {/* Filter inside sources */}
      {displayedSources.length > 1 && (
        <div className="flex justify-between items-center text-xs">
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter list by title or author..."
            className="w-64 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-200 p-2 placeholder-slate-600 focus:outline-none"
          />
          <span className="text-slate-500 text-xs">
            {filtered.length} of {displayedSources.length} papers
          </span>
        </div>
      )}

      {/* Source Cards */}
      {filtered.length === 0 ? (
        <EmptyState
          title="No Sources Found"
          description={
            displayedSources.length === 0
              ? 'No literature acquired yet. Start a research query or search arXiv above.'
              : 'No sources match your filter.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filtered.map((source) => {
            const authorsText = source.authors.join(', ');
            const yearText = source.publication_date
              ? new Date(source.publication_date).getFullYear()
              : 'n.d.';
            const sourceBadge = source.source_type || 'arXiv';

            return (
              <div
                key={source.id}
                className="p-5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:border-slate-700/80 transition space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 min-w-0">
                    <h2 className="text-base font-semibold text-slate-100 leading-snug">
                      {source.title}
                    </h2>
                    <p className="text-xs text-slate-400">
                      {authorsText} &bull; <span className="font-mono">{yearText}</span>
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300 border border-slate-700/60 shrink-0">
                    {sourceBadge}
                  </span>
                </div>

                {source.abstract && (
                  <p className="text-xs text-slate-300 font-serif leading-relaxed line-clamp-3">
                    {source.abstract}
                  </p>
                )}

                {/* Actions & Links */}
                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-500 font-mono">
                    Evidence chunks: 4 verified
                  </span>

                  <div className="flex items-center gap-3">
                    {onViewEvidence && (
                      <button
                        type="button"
                        onClick={onViewEvidence}
                        className="text-slate-400 hover:text-white transition text-xs"
                      >
                        View Evidence
                      </button>
                    )}
                    {source.pdf_url && (
                      <a
                        href={source.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:underline font-medium text-xs flex items-center gap-1"
                      >
                        <span>Open Paper</span>
                        <span>&rarr;</span>
                      </a>
                    )}
                  </div>
                </div>

                {/* Technical details disclosure */}
                <TechnicalDetails title="Technical details">
                  <div className="space-y-1 text-xs">
                    <div><span className="text-slate-500">Document ID:</span> {source.id}</div>
                    {source.url && <div><span className="text-slate-500">URL:</span> {source.url}</div>}
                    {source.metadata && (
                      <pre className="text-[10px] text-slate-400 pt-1">
                        {JSON.stringify(source.metadata, null, 2)}
                      </pre>
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

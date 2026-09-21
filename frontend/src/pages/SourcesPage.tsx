import React, { useState } from 'react';
import { Source } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { searchPapers } from '../services/api';

interface SourcesPageProps {
  sourcesList: Source[];
  onAddSource?: (source: Source) => void;
  isDemo?: boolean;
}

export const SourcesPage: React.FC<SourcesPageProps> = ({
  sourcesList,
  onAddSource,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Source[]>([]);
  const [expandedAbstracts, setExpandedAbstracts] = useState<Record<string, boolean>>({});
  const [filterQuery, setFilterQuery] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await searchPapers(searchQuery.trim(), 'arxiv', 5);
      setSearchResults(results);
    } catch (err) {
      console.error('arXiv search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleAbstract = (id: string) => {
    setExpandedAbstracts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const displayedSources = searchResults.length > 0 ? searchResults : sourcesList;
  const filtered = displayedSources.filter((s) =>
    s.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
    s.authors.some((a) => a.toLowerCase().includes(filterQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            Literature & Academic Paper Acquisition
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Free arXiv API integration, PDF chunk parsing, and bibliographic metadata.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Sources Ingested: <span className="text-emerald-400 font-bold">{sourcesList.length}</span>
        </div>
      </div>

      {/* arXiv Discovery Search Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search arXiv papers (e.g. dense retrieval, reciprocal rank fusion, self-rag)..."
              disabled={isSearching}
              className="w-full text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-200 p-2.5 pl-9 focus:outline-none focus:border-cyan-500 transition"
            />
            <svg className="w-4 h-4 text-slate-400 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="px-4 py-2 text-xs font-mono font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition disabled:opacity-40 flex items-center justify-center space-x-2"
          >
            {isSearching ? (
              <>
                <LoadingSpinner size="sm" />
                <span>Querying arXiv...</span>
              </>
            ) : (
              <span>Discover on arXiv</span>
            )}
          </button>
          {searchResults.length > 0 && (
            <button
              type="button"
              onClick={() => {
                setSearchResults([]);
                setSearchQuery('');
              }}
              className="px-3 py-2 text-xs font-mono rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              Clear Search
            </button>
          )}
        </form>
      </div>

      {/* Filter / Search within listed */}
      {displayedSources.length > 0 && (
        <div className="flex items-center justify-between text-xs">
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter by title or author..."
            className="w-64 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-200 p-1.5 focus:outline-none focus:border-slate-600 font-mono"
          />
          <span className="text-slate-400 font-mono text-[11px]">
            Showing {filtered.length} of {displayedSources.length} sources
          </span>
        </div>
      )}

      {/* Sources Card List */}
      {filtered.length === 0 ? (
        <EmptyState
          title="No Sources Found"
          description={
            displayedSources.length === 0
              ? 'No academic sources in the repository yet. Use the arXiv search above or start a research run.'
              : 'No sources match your filter.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filtered.map((source) => {
            const isExpanded = expandedAbstracts[source.id];
            return (
              <div
                key={source.id}
                className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 hover:border-slate-700 transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-2">
                  <div>
                    <span className="font-mono text-[10px] text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-900/50">
                      {source.id}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-100 mt-1">
                      {source.title}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {source.authors.join(', ')}
                    </p>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    {source.pdf_url && (
                      <a
                        href={source.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 rounded bg-rose-950/50 border border-rose-800 text-rose-300 text-[11px] font-mono hover:bg-rose-900/60 transition flex items-center space-x-1"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <span>PDF</span>
                      </a>
                    )}
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-mono transition flex items-center space-x-1"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        <span>arXiv</span>
                      </a>
                    )}
                    {onAddSource && !sourcesList.some((s) => s.id === source.id) && (
                      <button
                        type="button"
                        onClick={() => onAddSource(source)}
                        className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-semibold text-[11px] font-mono transition"
                      >
                        + Ingest
                      </button>
                    )}
                  </div>
                </div>

                {source.abstract && (
                  <div className="mt-3 text-xs">
                    <p className={`text-slate-300 font-serif leading-relaxed ${isExpanded ? '' : 'line-clamp-2'}`}>
                      {source.abstract}
                    </p>
                    <button
                      type="button"
                      onClick={() => toggleAbstract(source.id)}
                      className="text-[11px] font-mono text-cyan-400 hover:underline mt-1 block"
                    >
                      {isExpanded ? 'Show less' : 'Read abstract...'}
                    </button>
                  </div>
                )}

                <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>Published: {source.publication_date || 'N/A'}</span>
                  <span>Type: {source.source_type || 'arXiv Preprint'}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

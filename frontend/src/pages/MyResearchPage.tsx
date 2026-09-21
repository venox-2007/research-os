import React from 'react';
import { ResearchRunResponse } from '../types';
import { EmptyState } from '../components/EmptyState';

interface MyResearchPageProps {
  runs: ResearchRunResponse[];
  onSelectRun: (run: ResearchRunResponse) => void;
  onNewResearch: () => void;
}

export const MyResearchPage: React.FC<MyResearchPageProps> = ({
  runs,
  onSelectRun,
  onNewResearch,
}) => {
  return (
    <div className="max-w-3xl mx-auto py-4 md:py-8 space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">My Research</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Previous research investigations and findings.
          </p>
        </div>
        <button
          type="button"
          onClick={onNewResearch}
          className="px-3.5 py-1.5 rounded-lg bg-white hover:bg-slate-200 text-slate-950 font-medium text-xs transition"
        >
          + New Research
        </button>
      </div>

      {runs.length === 0 ? (
        <EmptyState
          title="No research runs yet"
          description="Start your first research query to see past investigations here."
          actionLabel="Start Research"
          onAction={onNewResearch}
        />
      ) : (
        <div className="space-y-3">
          {runs.map((run) => {
            const isCompleted = run.status === 'completed';
            const sourcesCount = run.sources?.length ?? 0;
            const experimentsCount = run.experiment_results?.length ?? 0;
            const evidenceCount = run.verified_evidence?.length ?? 0;

            return (
              <div
                key={run.run_id}
                onClick={() => onSelectRun(run)}
                className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700 cursor-pointer transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
              >
                <div className="space-y-1 min-w-0">
                  <h2 className="text-sm font-semibold text-slate-200 group-hover:text-white transition truncate">
                    {run.question}
                  </h2>
                  <div className="flex items-center gap-2 text-xs text-slate-400 font-sans">
                    <span className="flex items-center gap-1 font-medium">
                      {isCompleted ? (
                        <span className="text-emerald-400">&check; Completed</span>
                      ) : (
                        <span className="text-cyan-400">&bull; In progress</span>
                      )}
                    </span>
                    <span className="text-slate-600">&bull;</span>
                    <span>{sourcesCount} sources</span>
                    <span className="text-slate-600">&bull;</span>
                    <span>{evidenceCount} evidence</span>
                    {experimentsCount > 0 && (
                      <>
                        <span className="text-slate-600">&bull;</span>
                        <span>{experimentsCount} experiments</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="text-xs text-slate-500 group-hover:text-slate-300 transition shrink-0 font-medium flex items-center gap-1">
                  <span>View result</span>
                  <span>&rarr;</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

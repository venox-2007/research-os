import React, { useState } from 'react';
import { ResearchRunResponse, TraceEvent, ResearchTask } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';

interface RunsPageProps {
  activeRun: ResearchRunResponse | null;
  historyRuns: ResearchRunResponse[];
  onSelectRun: (runId: string) => void;
}

export const RunsPage: React.FC<RunsPageProps> = ({
  activeRun,
  historyRuns,
  onSelectRun,
}) => {
  const [selectedTrace, setSelectedTrace] = useState<TraceEvent | null>(null);

  const runsToDisplay = activeRun
    ? [activeRun, ...historyRuns.filter((r) => r.run_id !== activeRun.run_id)]
    : historyRuns;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            Research Runs & Agent Telemetry
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic LangGraph node execution traces, plan decomposition, and state transitions.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Total Runs: <span className="text-emerald-400 font-bold">{runsToDisplay.length}</span>
        </div>
      </div>

      {runsToDisplay.length === 0 ? (
        <EmptyState
          title="No Research Runs Found"
          description="Initialize a new research run from the Workspace to view agent execution telemetry and node traces."
          actionLabel="Go to Workspace"
          onAction={() => {}}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Runs List + Plan Breakdown */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block mb-3">
                Execution History
              </span>
              <div className="space-y-2">
                {runsToDisplay.map((run) => {
                  const isSelected = activeRun?.run_id === run.run_id;
                  return (
                    <button
                      key={run.run_id}
                      type="button"
                      onClick={() => onSelectRun(run.run_id)}
                      className={`w-full text-left p-3 rounded-lg border transition ${
                        isSelected
                          ? 'border-emerald-500/50 bg-emerald-950/20 text-slate-100'
                          : 'border-slate-800 bg-slate-950/40 hover:bg-slate-900 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-mono text-[11px] text-slate-400 truncate max-w-[150px]">
                          {run.run_id}
                        </span>
                        <StatusBadge status={run.status} />
                      </div>
                      <p className="text-xs font-serif line-clamp-2 text-slate-200">
                        {run.question}
                      </p>
                      <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span>Iter: {run.iteration_count}/{run.max_iterations}</span>
                        <span>Evidence: {run.verified_evidence.length}</span>
                        <span>Tasks: {run.tasks_completed}/{run.tasks_total}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Plan Breakdown */}
            {activeRun?.plan && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 space-y-3">
                <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                  LangGraph Plan Decomposition
                </span>
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                    Objectives
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                    {activeRun.plan.objectives.map((obj, i) => (
                      <li key={i} className="text-slate-300 font-serif leading-relaxed">
                        {obj}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1.5">
                    Sub-Tasks ({activeRun.plan.tasks.length})
                  </span>
                  <div className="space-y-1.5">
                    {activeRun.plan.tasks.map((task: ResearchTask) => (
                      <div
                        key={task.id}
                        className="p-2 rounded bg-slate-950/70 border border-slate-800/80 flex items-start justify-between text-xs gap-2"
                      >
                        <div className="min-w-0">
                          <span className="font-mono text-[10px] text-slate-400 uppercase block">
                            [{task.task_type}]
                          </span>
                          <span className="text-slate-200 text-[11px] truncate block">
                            {task.title}
                          </span>
                        </div>
                        <StatusBadge status={task.status} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Node Execution Timeline / Trace Stream */}
          <div className="lg:col-span-8 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    Node Execution Timeline & Traces
                  </h2>
                  <span className="text-[11px] font-mono text-slate-400">
                    Run: {activeRun?.run_id || 'N/A'} &bull; State transitions
                  </span>
                </div>
                {activeRun?.trace && (
                  <span className="text-xs font-mono text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/50 border border-emerald-800">
                    {activeRun.trace.length} Trace Events
                  </span>
                )}
              </div>

              {activeRun?.trace && activeRun.trace.length > 0 ? (
                <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {activeRun.trace.map((event: TraceEvent) => {
                    const isSelected = selectedTrace?.event_id === event.event_id;
                    return (
                      <div
                        key={event.event_id}
                        onClick={() => setSelectedTrace(event)}
                        className={`relative p-3 rounded-lg border cursor-pointer transition ${
                          isSelected
                            ? 'border-cyan-500/80 bg-cyan-950/30'
                            : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                        }`}
                      >
                        {/* Node marker */}
                        <div className="absolute -left-[27px] top-3.5 w-3 h-3 rounded-full bg-slate-950 border-2 border-cyan-400 shadow-sm shadow-cyan-400/50" />

                        <div className="flex items-center justify-between text-xs mb-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-cyan-300 font-bold uppercase text-[11px]">
                              {event.node_name || 'Workflow'}
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                              iter {event.iteration}
                            </span>
                          </div>
                          <span className="font-mono text-[10px] text-slate-400">
                            {event.timestamp}
                          </span>
                        </div>

                        <p className="text-xs text-slate-200 mt-0.5">
                          {event.message}
                        </p>

                        {event.details && (
                          <div className="mt-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400">
                            <pre className="overflow-x-auto p-1.5 rounded bg-slate-950 text-slate-300">
                              {JSON.stringify(event.details, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No trace events recorded for this run.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

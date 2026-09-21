import React from 'react';

export interface Stage {
  id: string;
  label: string;
  description: string;
}

const STAGES: Stage[] = [
  { id: 'question', label: 'Question', description: 'Problem formulation' },
  { id: 'planning', label: 'Planning', description: 'Task decomposition' },
  { id: 'research', label: 'Research', description: 'Hybrid retrieval & tools' },
  { id: 'verification', label: 'Evidence Audit', description: 'Coordinate verification' },
  { id: 'experiments', label: 'Experiments', description: 'Sandboxed routines' },
  { id: 'synthesis', label: 'Synthesis', description: 'Evidence-first drafting' },
  { id: 'validation', label: 'Citation Audit', description: 'Anti-hallucination check' },
  { id: 'report', label: 'Final Report', description: 'Publication deliverable' },
];

interface StageProgressProps {
  currentStatus: string;
  onSelectStage?: (stageId: string) => void;
  activeStageId?: string;
}

export const StageProgress: React.FC<StageProgressProps> = ({
  currentStatus,
  onSelectStage,
  activeStageId,
}) => {
  // Map backend status to active stage index
  let activeIndex = 0;
  const s = currentStatus.toLowerCase();
  if (s === 'initialized' || s === 'submitted') activeIndex = 0;
  else if (s === 'planning') activeIndex = 1;
  else if (s === 'researching') activeIndex = 2;
  else if (s === 'verifying') activeIndex = 3;
  else if (s === 'experimenting' || s === 'experiment_run') activeIndex = 4;
  else if (s === 'synthesizing' || s === 'refining') activeIndex = 5;
  else if (s === 'validating') activeIndex = 6;
  else if (s === 'completed') activeIndex = 7;

  return (
    <div className="w-full bg-slate-900/80 dark:bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
          Autonomous Research Lifecycle
        </h3>
        <span className="text-xs font-mono text-cyan-400">
          Status: {currentStatus}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
        {STAGES.map((stage, idx) => {
          const isPassed = idx < activeIndex;
          const isCurrent = idx === activeIndex;
          const isSelected = activeStageId === stage.id;

          let cardBorder = 'border-slate-800 bg-slate-900/40 text-slate-500';
          let indicatorBg = 'bg-slate-700';

          if (isPassed) {
            cardBorder = 'border-emerald-800/50 bg-emerald-950/20 text-slate-200 hover:border-emerald-600/70';
            indicatorBg = 'bg-emerald-500';
          } else if (isCurrent) {
            cardBorder = 'border-cyan-500/80 bg-cyan-950/30 text-white shadow-sm shadow-cyan-500/10 animate-pulse';
            indicatorBg = 'bg-cyan-400';
          }

          if (isSelected) {
            cardBorder += ' ring-1 ring-cyan-400';
          }

          return (
            <button
              key={stage.id}
              type="button"
              onClick={() => onSelectStage?.(stage.id)}
              disabled={!onSelectStage}
              className={`flex flex-col text-left p-2.5 rounded-lg border transition-all text-xs ${cardBorder} ${
                onSelectStage ? 'cursor-pointer' : 'cursor-default'
              }`}
            >
              <div className="flex items-center space-x-1.5 mb-1">
                <span className={`w-2 h-2 rounded-full ${indicatorBg}`} />
                <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400">
                  0{idx + 1}
                </span>
              </div>
              <span className="font-medium truncate font-sans text-slate-100">
                {stage.label}
              </span>
              <span className="text-[10px] text-slate-400 truncate mt-0.5">
                {stage.description}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

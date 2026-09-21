import React from 'react';

interface MetricsChartProps {
  metrics: Record<string, number>;
  title?: string;
}

export const MetricsChart: React.FC<MetricsChartProps> = ({ metrics, title }) => {
  const entries = Object.entries(metrics).filter(([_, v]) => typeof v === 'number' && !isNaN(v));

  if (entries.length === 0) {
    return (
      <div className="text-xs text-slate-500 italic p-4 text-center border border-dashed border-slate-800 rounded-lg">
        No numerical metrics available for visualization.
      </div>
    );
  }

  const maxValue = Math.max(...entries.map(([_, v]) => Math.abs(v)), 1.0);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
      {title && (
        <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold mb-3">
          {title}
        </h4>
      )}
      <div className="space-y-3">
        {entries.map(([key, val]) => {
          const pct = Math.min(100, Math.max(0, (Math.abs(val) / maxValue) * 100));
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-mono text-slate-300 font-medium">{key}</span>
                <span className="font-mono text-cyan-400 font-semibold">
                  {typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(4)) : val}
                </span>
              </div>
              <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

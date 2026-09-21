import React from 'react';

export type DashboardView =
  | 'workspace'
  | 'runs'
  | 'evidence'
  | 'sources'
  | 'experiments'
  | 'reports'
  | 'architecture';

interface SidebarProps {
  activeView: DashboardView;
  onSelectView: (view: DashboardView) => void;
  evidenceCount?: number;
  sourcesCount?: number;
  experimentsCount?: number;
}

interface NavItem {
  id: DashboardView;
  label: string;
  icon: React.ReactNode;
  badge?: number;
  description: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onSelectView,
  evidenceCount = 0,
  sourcesCount = 0,
  experimentsCount = 0,
}) => {
  const navItems: NavItem[] = [
    {
      id: 'workspace',
      label: 'Workspace',
      description: 'Research question input & stage pipeline',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
    {
      id: 'runs',
      label: 'Research Runs',
      description: 'Execution timeline & agent node traces',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      id: 'evidence',
      label: 'Evidence Explorer',
      description: 'Grounding chunks & claim verification DAG',
      badge: evidenceCount > 0 ? evidenceCount : undefined,
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'sources',
      label: 'Literature / Sources',
      description: 'arXiv papers, web discovery & ingested PDFs',
      badge: sourcesCount > 0 ? sourcesCount : undefined,
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
    },
    {
      id: 'experiments',
      label: 'Experiment Engine',
      description: 'Sandboxed code, executions & metrics',
      badge: experimentsCount > 0 ? experimentsCount : undefined,
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
      ),
    },
    {
      id: 'reports',
      label: 'Research Reports',
      description: 'Evidence-backed synthesis & citations',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'architecture',
      label: 'System Architecture',
      description: 'LangGraph, hybrid RAG & local stack',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
        </svg>
      ),
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 p-3 flex flex-col justify-between shrink-0 select-none">
      <div>
        <div className="px-3 py-2 text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
          Autonomous Console
        </div>
        <nav className="space-y-1 mt-1">
          {navItems.map((item) => {
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectView(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition text-left group ${
                  isActive
                    ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-medium'
                    : 'text-slate-300 hover:bg-slate-900/80 hover:text-slate-100 border border-transparent'
                }`}
                title={item.description}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <span className={isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-300'}>
                    {item.icon}
                  </span>
                  <span className="truncate">{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800 text-slate-400 text-[11px] space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 font-medium">Stack Cost</span>
          <span className="font-mono text-emerald-400 font-semibold">₹0.00 / $0.00</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Architecture</span>
          <span className="font-mono text-slate-300">LangGraph 8-Stage</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Execution Mode</span>
          <span className="font-mono text-slate-300">Deterministic</span>
        </div>
      </div>
    </aside>
  );
};

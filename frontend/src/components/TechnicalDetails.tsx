import React, { useState } from 'react';

interface TechnicalDetailsProps {
  title?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export const TechnicalDetails: React.FC<TechnicalDetailsProps> = ({
  title = 'Technical details',
  children,
  defaultOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="mt-3 border border-slate-800/80 rounded-lg overflow-hidden bg-slate-950/40">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 text-[11px] font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 transition text-left select-none"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-1.5">
          <svg
            className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-90 text-cyan-400' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
          </svg>
          <span>{title}</span>
        </span>
        <span className="text-[10px] text-slate-500">{isOpen ? 'Hide' : 'Expand'}</span>
      </button>

      {isOpen && (
        <div className="p-3 border-t border-slate-800/80 text-xs font-mono bg-slate-950/70 text-slate-300 overflow-x-auto animate-in fade-in duration-150">
          {children}
        </div>
      )}
    </div>
  );
};

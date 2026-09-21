import React from 'react';
import { HealthStatus } from '../types';

interface NavbarProps {
  health: HealthStatus | null;
  isOnline: boolean;
  isDemo: boolean;
  onToggleDemo: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  isOnline,
  isDemo,
  onToggleDemo,
  theme,
  onToggleTheme,
}) => {
  return (
    <>
      <header className="h-14 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur sticky top-0 z-40 px-4 md:px-6 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-white text-xs tracking-tight">
            R
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-100 text-sm tracking-tight font-sans">
              ResearchOS
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              Autonomous Research
            </span>
          </div>
        </div>

        {/* Right controls */}
        <div className="flex items-center space-x-2.5">
          {/* Demo Mode Toggle */}
          <button
            type="button"
            onClick={onToggleDemo}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono transition border ${
              isDemo
                ? 'bg-amber-950/40 border-amber-700/60 text-amber-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle offline demo mode"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isDemo ? 'bg-amber-400' : 'bg-slate-600'}`} />
            <span>Demo Mode</span>
          </button>

          {/* Health indicator */}
          <div
            className="hidden sm:flex items-center space-x-1.5 px-2 py-1 rounded text-[11px] font-mono text-slate-400"
            title={isOnline ? `Backend connected (${health?.llm_provider || 'live'})` : 'Backend disconnected'}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isOnline ? 'bg-emerald-400' : 'bg-rose-500'
              }`}
            />
            <span>{isOnline ? 'Connected' : 'Offline'}</span>
          </div>

          {/* Theme toggle */}
          <button
            type="button"
            onClick={onToggleTheme}
            className="p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            aria-label="Toggle color theme"
          >
            {theme === 'dark' ? (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      {/* Demo Banner */}
      {isDemo && (
        <div className="bg-amber-950/30 border-b border-amber-900/40 px-4 py-1.5 text-center text-xs text-amber-300 font-sans">
          Using synthetic demo data — no live research performed.
        </div>
      )}
    </>
  );
};

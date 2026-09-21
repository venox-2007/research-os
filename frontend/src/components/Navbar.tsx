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
    <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-40 px-4 md:px-6 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-emerald-400 flex items-center justify-center font-bold text-slate-950 text-sm shadow-sm">
          ROS
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-100 text-sm tracking-tight font-mono">
              ResearchOS
            </span>
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 bg-slate-800 text-slate-400 border border-slate-700 rounded">
              v0.7.0
            </span>
          </div>
          <span className="text-[11px] text-slate-400 hidden sm:block">
            Autonomous AI Research Engineer (₹0 Cost)
          </span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center space-x-3">
        {/* Demo Mode Toggle */}
        <button
          type="button"
          onClick={onToggleDemo}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium border transition ${
            isDemo
              ? 'bg-amber-950/60 border-amber-600/70 text-amber-300 shadow-sm'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
          title="Toggle deterministic offline demo mode"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isDemo ? 'bg-amber-400 animate-ping' : 'bg-slate-600'}`} />
          <span>Demo Mode: {isDemo ? 'ON' : 'OFF'}</span>
        </button>

        {/* Health status badge */}
        <div className="hidden md:flex items-center space-x-2 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              isDemo ? 'bg-amber-400' : isOnline ? 'bg-emerald-400' : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-300">
            {isDemo ? 'Offline Demo' : isOnline ? `Live (${health?.llm_provider || 'connected'})` : 'Offline'}
          </span>
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
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        {/* GitHub link */}
        <a
          href="https://github.com/venox-2007/research-os"
          target="_blank"
          rel="noreferrer"
          className="p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
          title="View GitHub repository"
          aria-label="GitHub Repository"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
          </svg>
        </a>
      </div>
    </header>
  );
};

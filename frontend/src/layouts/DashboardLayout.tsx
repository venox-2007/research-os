import React from 'react';
import { Navbar } from '../components/Navbar';
import { Sidebar, DashboardView } from '../components/Sidebar';
import { HealthStatus } from '../types';

interface DashboardLayoutProps {
  children: React.ReactNode;
  activeView: DashboardView;
  onSelectView: (view: DashboardView) => void;
  health: HealthStatus | null;
  isOnline: boolean;
  isDemo: boolean;
  onToggleDemo: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  evidenceCount?: number;
  sourcesCount?: number;
  experimentsCount?: number;
  savedRunsCount?: number;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  activeView,
  onSelectView,
  health,
  isOnline,
  isDemo,
  onToggleDemo,
  theme,
  onToggleTheme,
  evidenceCount = 0,
  sourcesCount = 0,
  experimentsCount = 0,
  savedRunsCount = 0,
}) => {
  return (
    <div className={`min-h-screen flex flex-col bg-slate-950 text-slate-100 ${theme === 'dark' ? 'dark' : ''}`}>
      {/* Top Navigation */}
      <Navbar
        health={health}
        isOnline={isOnline}
        isDemo={isDemo}
        onToggleDemo={onToggleDemo}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      {/* Main Body with Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeView={activeView}
          onSelectView={onSelectView}
          evidenceCount={evidenceCount}
          sourcesCount={sourcesCount}
          experimentsCount={experimentsCount}
          savedRunsCount={savedRunsCount}
        />

        <main className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
          {children}
        </main>
      </div>
    </div>
  );
};

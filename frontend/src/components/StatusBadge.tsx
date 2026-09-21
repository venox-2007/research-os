import React from 'react';
import { SupportStatus, ValidationStatus } from '../types';

interface StatusBadgeProps {
  status: SupportStatus | ValidationStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  let colorClasses = 'bg-slate-700 text-slate-300 border-slate-600';

  // Support Statuses
  if (normalized === 'SUPPORTED' || normalized === 'COMPLETED' || normalized === 'PASSED') {
    colorClasses = 'bg-emerald-950/70 text-emerald-300 border-emerald-700/60';
  } else if (normalized === 'PARTIALLY_SUPPORTED' || normalized === 'WARNING') {
    colorClasses = 'bg-amber-950/70 text-amber-300 border-amber-700/60';
  } else if (normalized === 'UNSUPPORTED' || normalized === 'FAILED' || normalized === 'REJECTED' || normalized === 'TIMEOUT') {
    colorClasses = 'bg-rose-950/70 text-rose-300 border-rose-700/60';
  } else if (normalized === 'CONTRADICTED') {
    colorClasses = 'bg-purple-950/70 text-purple-300 border-purple-700/60';
  } else if (['RUNNING', 'IN_PROGRESS', 'RESEARCHING', 'PLANNING', 'VERIFYING', 'SYNTHESIZING'].includes(normalized)) {
    colorClasses = 'bg-sky-950/70 text-sky-300 border-sky-700/60 animate-pulse';
  }

  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded-md border ${sizeClasses} ${colorClasses}`}
      title={`Status: ${status}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {status}
    </span>
  );
};

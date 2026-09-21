/**
 * Centralized typed API client for the FastAPI backend.
 * Handles production endpoints and optional offline demo simulation.
 */

import {
  Evidence,
  ExperimentCatalog,
  ExperimentRun,
  HealthStatus,
  ReportArtifact,
  ReportValidation,
  ResearchClaim,
  ResearchRunResponse,
  Source,
  SynthesisResult,
} from '../types';
import {
  DEMO_CATALOG,
  DEMO_CLAIMS,
  DEMO_EVIDENCE,
  DEMO_EXPERIMENT_RUNS,
  DEMO_HEALTH,
  DEMO_RUN,
  DEMO_SOURCES,
  DEMO_SYNTHESIS_RESULT,
} from './mockData';

const API_BASE = '';

let _demoModeEnabled = false;

export function setDemoMode(enabled: boolean): void {
  _demoModeEnabled = enabled;
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('researchos_demo_mode', enabled ? 'true' : 'false');
  }
}

export function isDemoMode(): boolean {
  if (typeof window !== 'undefined') {
    return _demoModeEnabled || window.localStorage.getItem('researchos_demo_mode') === 'true';
  }
  return _demoModeEnabled;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.error || `HTTP ${res.status}: ${res.statusText}`);
    }

    return await res.json();
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(msg);
  }
}

export async function fetchHealth(): Promise<HealthStatus> {
  if (isDemoMode()) return DEMO_HEALTH;
  return request<HealthStatus>('/health');
}

export async function submitResearchQuestion(
  query: string,
  discipline?: string,
  constraints: string[] = [],
): Promise<{ id: string; query: string; status: string }> {
  if (isDemoMode()) {
    return { id: 'demo-q-001', query, status: 'submitted' };
  }
  return request('/api/v1/research/question', {
    method: 'POST',
    body: JSON.stringify({ query, discipline: discipline || undefined, constraints }),
  });
}

export async function startResearchRun(
  question: string,
  discipline?: string,
  constraints: string[] = [],
  max_iterations: number = 2,
): Promise<ResearchRunResponse> {
  if (isDemoMode()) {
    return { ...DEMO_RUN, question };
  }
  return request<ResearchRunResponse>('/api/v1/research/run', {
    method: 'POST',
    body: JSON.stringify({
      question,
      discipline: discipline || undefined,
      constraints,
      max_iterations,
    }),
  });
}

export async function getResearchRun(run_id: string): Promise<ResearchRunResponse> {
  if (isDemoMode()) return DEMO_RUN;
  return request<ResearchRunResponse>(`/api/v1/research/run/${run_id}`);
}

export async function searchPapers(
  query: string,
  provider: string = 'arxiv',
  limit: number = 5,
): Promise<Source[]> {
  if (isDemoMode()) {
    return DEMO_SOURCES.filter(s =>
      s.title.toLowerCase().includes(query.toLowerCase()) ||
      s.authors.some(a => a.toLowerCase().includes(query.toLowerCase()))
    );
  }
  return request<Source[]>(`/api/v1/papers/search?query=${encodeURIComponent(query)}&provider=${provider}&limit=${limit}`);
}

export async function ingestPaper(url: string, title?: string): Promise<{ document_id: string; message: string }> {
  if (isDemoMode()) {
    return { document_id: 'doc_demo_ingest', message: 'Paper ingested successfully (Demo Mode)' };
  }
  return request('/api/v1/papers/ingest', {
    method: 'POST',
    body: JSON.stringify({ url, title: title || undefined }),
  });
}

export async function getEvidenceList(limit: number = 20): Promise<Evidence[]> {
  if (isDemoMode()) return DEMO_EVIDENCE.slice(0, limit);
  return request<Evidence[]>(`/api/v1/evidence?limit=${limit}`);
}

export async function getEvidenceById(evidence_id: string): Promise<Evidence> {
  if (isDemoMode()) {
    const ev = DEMO_EVIDENCE.find(e => e.id === evidence_id);
    if (ev) return ev;
    return DEMO_EVIDENCE[0];
  }
  return request<Evidence>(`/api/v1/evidence/${evidence_id}`);
}

export async function getExperimentCatalog(): Promise<ExperimentCatalog> {
  if (isDemoMode()) return DEMO_CATALOG;
  return request<ExperimentCatalog>('/api/v1/experiments/catalog');
}

export async function runExperiment(
  routine_name: string,
  parameters: Record<string, unknown> = {},
  dataset_name: string = 'synthetic_classification',
  seed: number = 42,
): Promise<ExperimentRun> {
  if (isDemoMode()) {
    const run = DEMO_EXPERIMENT_RUNS.find(r => r.routine_name === routine_name) || DEMO_EXPERIMENT_RUNS[0];
    return { ...run, id: `demo-exp-${Date.now()}` };
  }
  return request<ExperimentRun>('/api/v1/experiments/run', {
    method: 'POST',
    body: JSON.stringify({
      routine_name,
      parameters,
      dataset_name,
      seed,
    }),
  });
}

export async function getExperimentRun(run_id: string): Promise<ExperimentRun> {
  if (isDemoMode()) {
    const run = DEMO_EXPERIMENT_RUNS.find(r => r.id === run_id || r.run_id === run_id);
    return run || DEMO_EXPERIMENT_RUNS[0];
  }
  return request<ExperimentRun>(`/api/v1/experiments/runs/${run_id}`);
}

export async function generateReport(payload: {
  question: string;
  discipline?: string;
  research_run_id?: string;
  max_revisions?: number;
}): Promise<SynthesisResult> {
  if (isDemoMode()) {
    return { ...DEMO_SYNTHESIS_RESULT, spec: { ...DEMO_SYNTHESIS_RESULT.spec, question: payload.question } };
  }
  return request<SynthesisResult>('/api/v1/reports/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getReport(report_id: string): Promise<SynthesisResult> {
  if (isDemoMode()) return DEMO_SYNTHESIS_RESULT;
  return request<SynthesisResult>(`/api/v1/reports/${report_id}`);
}

export async function getReportClaims(report_id: string): Promise<ResearchClaim[]> {
  if (isDemoMode()) return DEMO_CLAIMS;
  return request<ResearchClaim[]>(`/api/v1/reports/${report_id}/claims`);
}

export async function getReportValidation(report_id: string): Promise<ReportValidation> {
  if (isDemoMode()) return DEMO_SYNTHESIS_RESULT.validation;
  return request<ReportValidation>(`/api/v1/reports/${report_id}/validation`);
}

export async function getReportArtifacts(report_id: string): Promise<ReportArtifact[]> {
  if (isDemoMode()) return DEMO_SYNTHESIS_RESULT.artifacts;
  return request<ReportArtifact[]>(`/api/v1/reports/${report_id}/artifacts`);
}

export function getArtifactDownloadUrl(report_id: string, filename: string): string {
  return `${API_BASE}/api/v1/reports/${report_id}/artifacts/${encodeURIComponent(filename)}`;
}

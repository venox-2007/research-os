export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  environment: string;
  llm_provider: string;
  llm_available: boolean;
  timestamp: string;
}

export interface ResearchQuestionResponse {
  id: string;
  query: string;
  discipline?: string;
  constraints: string[];
  status: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

const API_BASE = '';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export async function submitResearchQuestion(
  query: string,
  discipline?: string,
): Promise<ResearchQuestionResponse> {
  const res = await fetch(`${API_BASE}/api/v1/research/question`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      discipline: discipline || undefined,
      constraints: [],
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

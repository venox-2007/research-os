/**
 * Domain TypeScript interfaces for ResearchOS.
 * Accurately mirror backend FastAPI Pydantic models.
 */

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  llm_provider: string;
  llm_available: boolean;
  timestamp: string;
}

export type ClaimType =
  | 'background'
  | 'finding'
  | 'comparison'
  | 'methodological'
  | 'experiment_result'
  | 'limitation'
  | 'conclusion';

export type ClaimOrigin = 'literature' | 'experiment';

export type SupportStatus =
  | 'SUPPORTED'
  | 'PARTIALLY_SUPPORTED'
  | 'UNSUPPORTED'
  | 'CONTRADICTED'
  | 'UNVERIFIED';

export type ValidationStatus = 'PASSED' | 'WARNING' | 'FAILED';

export interface Source {
  id: string;
  title: string;
  authors: string[];
  publication_date?: string | null;
  url?: string | null;
  source_type?: string;
  abstract?: string | null;
  bibtex?: string | null;
  metadata?: Record<string, unknown>;
  pdf_url?: string | null;
}

export interface Evidence {
  id: string;
  source_id?: string | null;
  chunk_id?: string | null;
  source_title?: string | null;
  content: string;
  section?: string | null;
  page_number?: number | null;
  page_numbers?: number[];
  confidence_score: number;
  extraction_method?: string;
  created_at?: string;
  provenance_summary?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ResearchTask {
  id: string;
  plan_id?: string | null;
  title: string;
  task_type: string;
  assigned_agent?: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  output?: Record<string, unknown> | null;
  created_at?: string;
}

export interface ResearchPlan {
  id: string;
  question_id: string;
  objectives: string[];
  tasks: ResearchTask[];
  status: string;
  created_at?: string;
}

export interface TraceEvent {
  event_id: string;
  event_type: string;
  node_name?: string | null;
  iteration: number;
  timestamp: string;
  message: string;
  details?: Record<string, unknown>;
  duration_ms?: number | null;
  error?: string | null;
}

export interface ResearchRunResponse {
  run_id: string;
  question: string;
  status: 'initialized' | 'planning' | 'researching' | 'verifying' | 'critiquing' | 'refining' | 'completed' | 'failed';
  iteration_count: number;
  max_iterations: number;
  plan?: ResearchPlan | null;
  tasks_completed: number;
  tasks_total: number;
  verified_evidence: Evidence[];
  sources: Source[];
  experiment_specs: Array<Record<string, unknown>>;
  experiment_results: Array<Record<string, unknown> | ExperimentRun>;
  contradictions: string[];
  research_notes: string[];
  critic_summary?: string | null;
  confidence_score: number;
  trace: TraceEvent[];
  errors: string[];
  final_context?: Record<string, unknown>;
}

export interface ResearchClaim {
  id: string;
  claim_text: string;
  claim_type: ClaimType;
  origin: ClaimOrigin;
  supporting_evidence_ids: string[];
  source_ids: string[];
  page_references: number[];
  section_references: string[];
  support_status: SupportStatus;
  confidence: number;
  is_contradicted: boolean;
  contradiction_notes?: string | null;
  experiment_run_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface CitationReference {
  key: string;
  source_id: string;
  title: string;
  authors: string[];
  year?: number | string | null;
  venue?: string | null;
  doi?: string | null;
  url?: string | null;
  paper_id?: string | null;
  formatted_citation: string;
  is_available: boolean;
}

export interface ReportSection {
  id: string;
  title: string;
  section_type: string;
  content: string;
  claim_ids: string[];
  citation_keys: string[];
  order: number;
  subsections?: ReportSection[];
}

export interface ReportArtifact {
  id: string;
  report_id: string;
  artifact_type: string;
  filename: string;
  file_path: string;
  file_hash: string;
  size_bytes: number;
  mime_type: string;
}

export interface ReportValidation {
  is_valid: boolean;
  total_claims: number;
  supported_claims: number;
  partially_supported_claims: number;
  unsupported_claims: number;
  contradicted_claims: number;
  citation_coverage: number;
  evidence_coverage: number;
  unsupported_claim_rate: number;
  provenance_completeness: number;
  contradiction_count: number;
  citation_correctness: number;
  validation_status: ValidationStatus;
  issues: string[];
  unsupported_claim_ids: string[];
  contradicted_claim_ids: string[];
  unresolved_questions: string[];
}

export interface ReportSpec {
  id?: string;
  question: string;
  title?: string | null;
  discipline?: string | null;
  target_audience?: string;
  format?: string;
  max_sections?: number;
  focus_areas?: string[];
  include_experiments?: boolean;
  constraints?: string[];
}

export interface SynthesisResult {
  id: string;
  report_id: string;
  spec: ReportSpec;
  title: string;
  abstract: string;
  sections: ReportSection[];
  claims: ResearchClaim[];
  citations: CitationReference[];
  validation: ReportValidation;
  report_markdown: string;
  report_json: Record<string, unknown>;
  artifacts: ReportArtifact[];
  created_at?: string;
}

export interface ExperimentCatalog {
  routines: Array<{
    name: string;
    description: string;
    allowed_parameters: string[];
  }>;
  datasets: Array<{
    name: string;
    description: string;
    format: string;
  }>;
}

export interface ExperimentRun {
  id: string;
  run_id: string;
  spec_id?: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'rejected';
  routine_name?: string;
  config?: {
    target_routine?: string;
    parameters?: Record<string, unknown>;
    seed?: number;
    timeout_seconds?: number;
  };
  metrics?: Record<string, number>;
  artifacts?: Array<{
    name: string;
    artifact_type?: string;
    mime_type?: string;
    file_path?: string;
  }>;
  duration_seconds?: number;
  created_at?: string;
  error_message?: string | null;
}

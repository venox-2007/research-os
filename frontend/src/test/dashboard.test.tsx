import { describe, it, expect, beforeEach } from 'vitest';
import { renderToString } from 'react-dom/server';

import {
  DEMO_HEALTH,
  DEMO_RUN,
  DEMO_SOURCES,
  DEMO_EVIDENCE,
  DEMO_CLAIMS,
  DEMO_EXPERIMENT_RUNS,
  DEMO_SYNTHESIS_RESULT,
} from '../services/mockData';
import {
  setDemoMode,
  isDemoMode,
  fetchHealth,
  getResearchRun,
  searchPapers,
  getExperimentCatalog,
  generateReport,
} from '../services/api';

import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';
import { StatusBadge } from '../components/StatusBadge';
import { StageProgress } from '../components/StageProgress';
import { ClaimModal } from '../components/ClaimModal';
import { MetricsChart } from '../components/MetricsChart';
import { EmptyState } from '../components/EmptyState';
import { WorkspacePage } from '../pages/WorkspacePage';
import { RunsPage } from '../pages/RunsPage';
import { EvidencePage } from '../pages/EvidencePage';
import { SourcesPage } from '../pages/SourcesPage';
import { ExperimentsPage } from '../pages/ExperimentsPage';
import { ReportsPage } from '../pages/ReportsPage';
import { ArchitecturePage } from '../pages/ArchitecturePage';

describe('ResearchOS Synthetic Benchmark Data', () => {
  it('contains valid ₹0-cost demo health configuration', () => {
    expect(DEMO_HEALTH.status).toBe('healthy');
    expect(DEMO_HEALTH.llm_provider).toBe('deterministic-offline-mock');
    expect(DEMO_HEALTH.llm_available).toBe(true);
  });

  it('contains full 8-stage demo research run with evidence and traces', () => {
    expect(DEMO_RUN.run_id).toContain('demo-run');
    expect(DEMO_RUN.verified_evidence.length).toBeGreaterThanOrEqual(4);
    expect(DEMO_RUN.sources.length).toBeGreaterThanOrEqual(3);
    expect(DEMO_RUN.confidence_score).toBeGreaterThan(0.9);
    expect(DEMO_RUN.trace.length).toBeGreaterThanOrEqual(5);
  });

  it('contains verifiable claims with citation provenance', () => {
    expect(DEMO_CLAIMS.length).toBeGreaterThanOrEqual(4);
    for (const claim of DEMO_CLAIMS) {
      expect(claim.id).toBeDefined();
      expect(claim.claim_text.length).toBeGreaterThan(10);
      expect(claim.confidence).toBeGreaterThanOrEqual(0.85);
      if (claim.origin === 'literature') {
        expect(claim.supporting_evidence_ids.length).toBeGreaterThan(0);
      } else {
        expect(claim.experiment_run_id).toBeDefined();
      }
    }
  });

  it('contains empirical experiment benchmarks', () => {
    expect(DEMO_EXPERIMENT_RUNS.length).toBeGreaterThanOrEqual(2);
    const firstExp = DEMO_EXPERIMENT_RUNS[0];
    expect(firstExp.metrics).toBeDefined();
    expect(firstExp.metrics?.['mrr']).toBeGreaterThan(0.8);
    expect(firstExp.metrics?.['recall_at_10']).toBeGreaterThan(0.9);
  });

  it('contains a grounded final research synthesis report', () => {
    expect(DEMO_SYNTHESIS_RESULT.report_markdown).toContain('# ');
    expect(DEMO_SYNTHESIS_RESULT.validation.citation_correctness).toBe(1.0);
    expect(DEMO_SYNTHESIS_RESULT.validation.unsupported_claims).toBe(0);
    expect(DEMO_SYNTHESIS_RESULT.citations.length).toBeGreaterThanOrEqual(3);
  });
});

describe('API Client & Demo Mode Simulation', () => {
  beforeEach(() => {
    setDemoMode(true);
  });

  it('correctly toggles demo mode state', () => {
    setDemoMode(true);
    expect(isDemoMode()).toBe(true);
    setDemoMode(false);
    expect(isDemoMode()).toBe(false);
    setDemoMode(true);
  });

  it('fetches health status in demo mode without HTTP traffic', async () => {
    const health = await fetchHealth();
    expect(health.status).toBe('healthy');
    expect(health.llm_provider).toBe('deterministic-offline-mock');
  });

  it('retrieves demo research run in demo mode', async () => {
    const run = await getResearchRun('any-id');
    expect(run.status).toBe('completed');
    expect(run.question).toContain('attention mechanisms');
  });

  it('filters academic sources by query in demo mode', async () => {
    const results = await searchPapers('attention');
    expect(results.length).toBeGreaterThanOrEqual(1);
    expect(results[0].title).toContain('Attention Is All You Need');
  });

  it('returns experiment catalog with supported sandboxed routines', async () => {
    const catalog = await getExperimentCatalog();
    expect(catalog.routines.length).toBeGreaterThanOrEqual(3);
    const routineNames = catalog.routines.map((r) => r.name);
    expect(routineNames).toContain('ranking_evaluation');
  });

  it('generates a synthetic final report in demo mode', async () => {
    const report = await generateReport({
      question: 'Evaluation of Reciprocal Rank Fusion',
      research_run_id: 'demo-run-001',
    });
    expect(report.title).toBeDefined();
    expect(report.validation.is_valid).toBe(true);
  });
});

describe('UI Component Server Rendering', () => {
  it('renders Navbar with brand, status, and demo mode switch', () => {
    const html = renderToString(
      <Navbar
        health={DEMO_HEALTH}
        isOnline={true}
        isDemo={true}
        onToggleDemo={() => {}}
        theme="dark"
        onToggleTheme={() => {}}
      />
    );
    expect(html).toContain('ResearchOS');
    expect(html).toContain('Demo Mode:');
    expect(html).toContain('Offline Demo');
  });

  it('renders Sidebar with all 7 primary dashboard tabs', () => {
    const html = renderToString(
      <Sidebar
        activeView="workspace"
        onSelectView={() => {}}
        evidenceCount={12}
        sourcesCount={5}
        experimentsCount={3}
      />
    );
    expect(html).toContain('Workspace');
    expect(html).toContain('Research Runs');
    expect(html).toContain('Evidence Explorer');
    expect(html).toContain('Literature / Sources');
    expect(html).toContain('Experiment Engine');
    expect(html).toContain('Research Reports');
    expect(html).toContain('System Architecture');
    expect(html).toContain('₹0.00 / $0.00');
  });

  it('renders StatusBadge for semantic statuses with proper labels', () => {
    const htmlCompleted = renderToString(<StatusBadge status="completed" />);
    expect(htmlCompleted).toContain('completed');

    const htmlRunning = renderToString(<StatusBadge status="running" />);
    expect(htmlRunning).toContain('running');

    const htmlVerified = renderToString(<StatusBadge status="SUPPORTED" />);
    expect(htmlVerified).toContain('SUPPORTED');

    const htmlFailed = renderToString(<StatusBadge status="failed" />);
    expect(htmlFailed).toContain('failed');
  });

  it('renders StageProgress across all 8 autonomous lifecycle stages', () => {
    const html = renderToString(<StageProgress currentStatus="completed" />);
    expect(html).toContain('Question');
    expect(html).toContain('Planning');
    expect(html).toContain('Research');
    expect(html).toContain('Evidence Audit');
    expect(html).toContain('Experiments');
    expect(html).toContain('Synthesis');
    expect(html).toContain('Citation Audit');
    expect(html).toContain('Final Report');
  });

  it('renders ClaimModal with provenance DAG hierarchy', () => {
    const claim = DEMO_CLAIMS[0];
    const html = renderToString(
      <ClaimModal
        claim={claim}
        evidenceList={DEMO_EVIDENCE}
        sources={DEMO_SOURCES}
        onClose={() => {}}
      />
    );
    expect(html).toContain('Claim Provenance Inspector');
    expect(html).toContain(claim.claim_text);
    expect(html).toContain('Visual Provenance Lineage');
    expect(html).toContain('Supporting Evidence Excerpt');
  });

  it('renders MetricsChart with empirical metrics data bars', () => {
    const metrics = { 'mrr@10': 0.892, 'ndcg@10': 0.914, 'latency_ms': 18.5 };
    const html = renderToString(
      <MetricsChart metrics={metrics} title="Benchmark Results" />
    );
    expect(html).toContain('Benchmark Results');
    expect(html).toContain('mrr@10');
    expect(html).toContain('0.8920');
    expect(html).toContain('latency_ms');
  });

  it('renders EmptyState with custom title, description, and action button', () => {
    const html = renderToString(
      <EmptyState
        title="No Evidence Available"
        description="Run a research query to gather evidence."
        actionLabel="Start Research"
        onAction={() => {}}
      />
    );
    expect(html).toContain('No Evidence Available');
    expect(html).toContain('Run a research query to gather evidence.');
    expect(html).toContain('Start Research');
  });
});

describe('Dashboard Page Views Server Rendering', () => {
  it('renders WorkspacePage with prompt card and sample benchmarks', () => {
    const html = renderToString(
      <WorkspacePage
        activeRun={DEMO_RUN}
        isLoading={false}
        error={null}
        onSubmitQuestion={() => {}}
        onReset={() => {}}
        onNavigateView={() => {}}
        isDemo={true}
      />
    );
    expect(html).toContain('Research Workspace');
    expect(html).toContain('Define Research Objective');
    expect(html).toContain('Curated Research Benchmarks');
    expect(html).toContain('Dense vs Hybrid RAG Retrieval');
    expect(html).toContain('Active Orchestration Run');
  });

  it('renders RunsPage with LangGraph node timeline and plan decomposition', () => {
    const html = renderToString(
      <RunsPage
        activeRun={DEMO_RUN}
        historyRuns={[DEMO_RUN]}
        onSelectRun={() => {}}
      />
    );
    expect(html).toContain('Research Runs &amp; Agent Telemetry');
    expect(html).toContain('Execution History');
    expect(html).toContain('LangGraph Plan Decomposition');
    expect(html).toContain('Node Execution Timeline &amp; Traces');
    expect(html).toContain('Decomposing research query');
  });

  it('renders EvidencePage with chunk cards and filtering controls', () => {
    const html = renderToString(
      <EvidencePage
        evidenceList={DEMO_EVIDENCE}
        claimsList={DEMO_CLAIMS}
      />
    );
    expect(html).toContain('Evidence Explorer &amp; Grounding DAG');
    expect(html).toContain('Verified Claims');
    expect(html).toContain('Search Content &amp; Sources');
    expect(html).toContain('Extraction Method');
    expect(html).toContain(DEMO_EVIDENCE[0].content.slice(0, 30));
  });

  it('renders SourcesPage with arXiv paper list and direct links', () => {
    const html = renderToString(
      <SourcesPage sourcesList={DEMO_SOURCES} />
    );
    expect(html).toContain('Literature &amp; Academic Paper Acquisition');
    expect(html).toContain('Discover on arXiv');
    expect(html).toContain('Attention Is All You Need');
    expect(html).toContain('PDF');
  });

  it('renders ExperimentsPage with sandbox routine launcher and metric graphs', () => {
    const html = renderToString(
      <ExperimentsPage
        experimentRuns={DEMO_EXPERIMENT_RUNS}
        onAddExperimentRun={() => {}}
      />
    );
    expect(html).toContain('Experiment Engine');
    expect(html).toContain('Sandboxed / Deterministic');
    expect(html).toContain('Design &amp; Launch Experiment');
    expect(html).toContain('Ranking Evaluation (RRF vs BM25)');
    expect(html).toContain('Empirical Evaluation Metrics');
  });

  it('renders ReportsPage with publication reader and quality control panel', () => {
    const html = renderToString(
      <ReportsPage
        synthesisResult={DEMO_SYNTHESIS_RESULT}
        activeRun={DEMO_RUN}
        onUpdateReport={() => {}}
      />
    );
    expect(html).toContain('Research Synthesis &amp; Quality Audit');
    expect(html).toContain('Quality Control Audit');
    expect(html).toContain('Provenance Completeness');
    expect(html).toContain('Citation Correctness');
    expect(html).toContain('Export .MD');
    expect(html).toContain('Export JSON');
  });

  it('renders ArchitecturePage with the complete 8-stage pipeline and ₹0-cost audit', () => {
    const html = renderToString(<ArchitecturePage />);
    expect(html).toContain('System Architecture &amp; ₹0 Cost Specifications');
    expect(html).toContain('Eight-Stage Deterministic Workflow');
    expect(html).toContain('Question Formulation');
    expect(html).toContain('Deterministic Orchestration');
    expect(html).toContain('Hybrid RAG &amp; Indexing');
    expect(html).toContain('Safe Experiment Sandbox');
    expect(html).toContain('Citation Audit &amp; Guardrails');
    expect(html).toContain('Total Operational Cost: ₹0.00 / $0.00');
  });
});

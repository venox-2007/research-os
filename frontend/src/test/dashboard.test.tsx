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
import { TechnicalDetails } from '../components/TechnicalDetails';
import { EmptyState } from '../components/EmptyState';
import { WorkspacePage } from '../pages/WorkspacePage';
import { MyResearchPage } from '../pages/MyResearchPage';
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

describe('Simplified UI Component Server Rendering', () => {
  it('renders Navbar with brand, status, and demo banner', () => {
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
    expect(html).toContain('Demo Mode');
    expect(html).toContain('Using synthetic demo data — no live research performed.');
  });

  it('renders streamlined Sidebar with primary research navigation', () => {
    const html = renderToString(
      <Sidebar
        activeView="research"
        onSelectView={() => {}}
        evidenceCount={12}
        sourcesCount={5}
        experimentsCount={3}
        savedRunsCount={2}
      />
    );
    expect(html).toContain('Research');
    expect(html).toContain('My Research');
    expect(html).toContain('Sources');
    expect(html).toContain('Evidence');
    expect(html).toContain('Experiments');
    expect(html).toContain('Reports');
    expect(html).toContain('System Details');
    expect(html).not.toContain('LangGraph 8-Stage'); // Technical jargon removed from primary nav
  });

  it('renders TechnicalDetails expandable disclosure component', () => {
    const html = renderToString(
      <TechnicalDetails title="View technical details">
        <div>Node: planner, Execution Time: 12ms</div>
      </TechnicalDetails>
    );
    expect(html).toContain('View technical details');
    expect(html).toContain('Expand');
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

describe('Streamlined Page Views Server Rendering', () => {
  it('renders WorkspacePage landing state with clear hero, input, and suggestions', () => {
    const html = renderToString(
      <WorkspacePage
        activeRun={null}
        synthesisResult={null}
        isLoading={false}
        error={null}
        onSubmitQuestion={() => {}}
        onReset={() => {}}
        onNavigateView={() => {}}
        isDemo={false}
      />
    );
    expect(html).toContain('Research anything.');
    expect(html).toContain('ResearchOS searches academic literature, verifies evidence, runs experiments when useful, and builds a cited research report.');
    expect(html).toContain('What do you want to research?');
    expect(html).toContain('Start Research');
    expect(html).toContain('How does hybrid retrieval improve RAG?');
    expect(html).toContain('Compare CNN and Transformer speech enhancement.');
    expect(html).toContain('What factors affect retrieval quality?');
    expect(html).not.toContain('LangGraph'); // Technical implementation hidden
  });

  it('renders WorkspacePage running state with human-readable progress', () => {
    const inProgressRun = { ...DEMO_RUN, status: 'researching' as const };
    const html = renderToString(
      <WorkspacePage
        activeRun={inProgressRun}
        synthesisResult={null}
        isLoading={true}
        error={null}
        onSubmitQuestion={() => {}}
        onReset={() => {}}
        onNavigateView={() => {}}
        isDemo={false}
      />
    );
    expect(html).toContain('Researching your question...');
    expect(html).toContain('Understanding the question');
    expect(html).toContain('Searching academic literature');
    expect(html).toContain('Analyzing evidence');
    expect(html).toContain('Running experiments');
    expect(html).toContain('Writing the report');
    expect(html).toContain('Checking citations');
    expect(html).toContain('View technical details');
  });

  it('renders WorkspacePage completion state with executive summary and key metrics', () => {
    const html = renderToString(
      <WorkspacePage
        activeRun={DEMO_RUN}
        synthesisResult={DEMO_SYNTHESIS_RESULT}
        isLoading={false}
        error={null}
        onSubmitQuestion={() => {}}
        onReset={() => {}}
        onNavigateView={() => {}}
        isDemo={true}
      />
    );
    expect(html).toContain('Research complete');
    expect(html).toContain('Read Full Report');
    expect(html).toContain('Explore Evidence');
    expect(html).toContain('Citation coverage');
    expect(html).toContain('Unsupported claims');
    expect(html).toContain('Provenance');
    expect(html).toContain('Technical details');
  });

  it('renders MyResearchPage with past runs list', () => {
    const html = renderToString(
      <MyResearchPage
        runs={[DEMO_RUN]}
        onSelectRun={() => {}}
        onNewResearch={() => {}}
      />
    );
    expect(html).toContain('My Research');
    expect(html).toContain('Previous research investigations and findings.');
    expect(html).toContain(DEMO_RUN.question);
    expect(html).toContain('Completed');
    expect(html).toContain('View result');
  });

  it('renders EvidencePage with clean evidence cards and location coordinates', () => {
    const html = renderToString(
      <EvidencePage
        evidenceList={DEMO_EVIDENCE}
        claimsList={DEMO_CLAIMS}
      />
    );
    expect(html).toContain('Evidence supporting your research');
    expect(html).toContain('Claim');
    expect(html).toContain('Location:');
    expect(html).toContain('Supported');
    expect(html).toContain('Technical details');
  });

  it('renders SourcesPage with clean academic literature cards', () => {
    const html = renderToString(
      <SourcesPage sourcesList={DEMO_SOURCES} />
    );
    expect(html).toContain('Academic Literature &amp; Sources');
    expect(html).toContain('Attention Is All You Need');
    expect(html).toContain('Vaswani, A.');
    expect(html).toContain('Open Paper');
    expect(html).toContain('Technical details');
  });

  it('renders ExperimentsPage with clear hypothesis and results table', () => {
    const html = renderToString(
      <ExperimentsPage
        experimentRuns={DEMO_EXPERIMENT_RUNS}
        onAddExperimentRun={() => {}}
      />
    );
    expect(html).toContain('Experiments');
    expect(html).toContain('Experiments run by ResearchOS to test research hypotheses.');
    expect(html).toContain('Hypothesis');
    expect(html).toContain('Method');
    expect(html).toContain('Dataset');
    expect(html).toContain('Results');
    expect(html).toContain('How was this experiment run?');
  });

  it('renders ReportsPage as an academic publication reader with references', () => {
    const html = renderToString(
      <ReportsPage
        synthesisResult={DEMO_SYNTHESIS_RESULT}
        activeRun={DEMO_RUN}
        onUpdateReport={() => {}}
        onNavigateHome={() => {}}
      />
    );
    expect(html).toContain(DEMO_SYNTHESIS_RESULT.title);
    expect(html).toContain('Abstract');
    expect(html).toContain('References');
    expect(html).toContain('Download Markdown');
    expect(html).toContain('Technical report validation details');
  });

  it('renders ArchitecturePage as secondary system details', () => {
    const html = renderToString(<ArchitecturePage />);
    expect(html).toContain('System Architecture &amp; ₹0 Cost Specifications');
    expect(html).toContain('Eight-Stage Deterministic Workflow');
    expect(html).toContain('Total Operational Cost: ₹0.00 / $0.00');
  });
});

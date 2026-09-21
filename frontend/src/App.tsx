import React, { useState } from 'react';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardView } from './components/Sidebar';
import { WorkspacePage } from './pages/WorkspacePage';
import { RunsPage } from './pages/RunsPage';
import { EvidencePage } from './pages/EvidencePage';
import { SourcesPage } from './pages/SourcesPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { ReportsPage } from './pages/ReportsPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { ClaimModal } from './components/ClaimModal';
import { useHealth } from './hooks/useHealth';
import { useTheme } from './hooks/useTheme';
import { useResearchRun } from './hooks/useResearchRun';
import { isDemoMode, setDemoMode } from './services/api';
import {
  DEMO_RUN,
  DEMO_SOURCES,
  DEMO_EVIDENCE,
  DEMO_CLAIMS,
  DEMO_EXPERIMENT_RUNS,
  DEMO_SYNTHESIS_RESULT,
} from './services/mockData';
import { Source, Evidence, ExperimentRun, SynthesisResult, ResearchClaim, ResearchRunResponse } from './types';

export const App: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { health, isOnline } = useHealth();
  const [isDemo, setIsDemo] = useState<boolean>(() => isDemoMode());
  const [activeView, setActiveView] = useState<DashboardView>('workspace');

  // Active Research Run state
  const { currentRun, setCurrentRun, startRun, loading: runLoading, error: runError } = useResearchRun(
    isDemo ? DEMO_RUN : null
  );

  // Entities state
  const [historyRuns, setHistoryRuns] = useState<ResearchRunResponse[]>(() => (isDemo ? [DEMO_RUN] : []));
  const [sourcesList, setSourcesList] = useState<Source[]>(() => (isDemo ? DEMO_SOURCES : []));
  const [evidenceList, setEvidenceList] = useState<Evidence[]>(() => (isDemo ? DEMO_EVIDENCE : []));
  const [experimentRuns, setExperimentRuns] = useState<ExperimentRun[]>(() =>
    isDemo ? DEMO_EXPERIMENT_RUNS : []
  );
  const [synthesisResult, setSynthesisResult] = useState<SynthesisResult | null>(() =>
    isDemo ? DEMO_SYNTHESIS_RESULT : null
  );
  const [selectedClaim, setSelectedClaim] = useState<ResearchClaim | null>(null);

  // Toggle Demo Mode
  const handleToggleDemo = () => {
    const nextMode = !isDemo;
    setDemoMode(nextMode);
    setIsDemo(nextMode);

    if (nextMode) {
      setCurrentRun(DEMO_RUN);
      setHistoryRuns([DEMO_RUN]);
      setSourcesList(DEMO_SOURCES);
      setEvidenceList(DEMO_EVIDENCE);
      setExperimentRuns(DEMO_EXPERIMENT_RUNS);
      setSynthesisResult(DEMO_SYNTHESIS_RESULT);
    } else {
      setCurrentRun(null);
      setHistoryRuns([]);
      setSourcesList([]);
      setEvidenceList([]);
      setExperimentRuns([]);
      setSynthesisResult(null);
    }
  };

  // Submit Question Handler
  const handleSubmitQuestion = async (
    query: string,
    discipline?: string,
    maxIterations: number = 3
  ) => {
    try {
      const run = await startRun(query, discipline, [], maxIterations);
      if (run) {
        setHistoryRuns((prev) => [run, ...prev.filter((r) => r.run_id !== run.run_id)]);
        if (run.sources && run.sources.length > 0) {
          setSourcesList((prev) => [...run.sources, ...prev]);
        }
        if (run.verified_evidence && run.verified_evidence.length > 0) {
          setEvidenceList((prev) => [...run.verified_evidence, ...prev]);
        }
      }
    } catch {
      // Error handled by useResearchRun
    }
  };

  // Reset Run
  const handleResetRun = () => {
    setCurrentRun(null);
  };

  // Select Run from history
  const handleSelectRun = (runId: string) => {
    const found = historyRuns.find((r) => r.run_id === runId);
    if (found) setCurrentRun(found);
  };

  // Add an experiment run
  const handleAddExperimentRun = (newRun: ExperimentRun) => {
    setExperimentRuns((prev) => [newRun, ...prev]);
  };

  // Add a source
  const handleAddSource = (source: Source) => {
    setSourcesList((prev) => [source, ...prev]);
  };

  // Update synthesized report
  const handleUpdateReport = (report: SynthesisResult) => {
    setSynthesisResult(report);
  };

  return (
    <DashboardLayout
      activeView={activeView}
      onSelectView={setActiveView}
      health={health}
      isOnline={isOnline}
      isDemo={isDemo}
      onToggleDemo={handleToggleDemo}
      theme={theme}
      onToggleTheme={toggleTheme}
      evidenceCount={evidenceList.length}
      sourcesCount={sourcesList.length}
      experimentsCount={experimentRuns.length}
    >
      {activeView === 'workspace' && (
        <WorkspacePage
          activeRun={currentRun}
          isLoading={runLoading}
          error={runError}
          onSubmitQuestion={handleSubmitQuestion}
          onReset={handleResetRun}
          onSelectClaim={(claim) => setSelectedClaim(claim)}
          onNavigateView={(view) => setActiveView(view)}
          isDemo={isDemo}
        />
      )}

      {activeView === 'runs' && (
        <RunsPage
          activeRun={currentRun}
          historyRuns={historyRuns}
          onSelectRun={handleSelectRun}
        />
      )}

      {activeView === 'evidence' && (
        <EvidencePage
          evidenceList={evidenceList}
          claimsList={synthesisResult?.claims || (isDemo ? DEMO_CLAIMS : [])}
          onSelectClaim={(claim) => setSelectedClaim(claim)}
          onSelectEvidence={(ev) => {
            const matchedClaim = (synthesisResult?.claims || DEMO_CLAIMS).find((c) =>
              c.supporting_evidence_ids.includes(ev.id)
            );
            if (matchedClaim) {
              setSelectedClaim(matchedClaim);
            }
          }}
        />
      )}

      {activeView === 'sources' && (
        <SourcesPage
          sourcesList={sourcesList}
          onAddSource={handleAddSource}
          isDemo={isDemo}
        />
      )}

      {activeView === 'experiments' && (
        <ExperimentsPage
          experimentRuns={experimentRuns}
          onAddExperimentRun={handleAddExperimentRun}
          isDemo={isDemo}
        />
      )}

      {activeView === 'reports' && (
        <ReportsPage
          synthesisResult={synthesisResult}
          activeRun={currentRun}
          onUpdateReport={handleUpdateReport}
          isDemo={isDemo}
        />
      )}

      {activeView === 'architecture' && <ArchitecturePage />}

      {/* Provenance DAG Modal */}
      {selectedClaim && (
        <ClaimModal
          claim={selectedClaim}
          evidenceList={evidenceList}
          sources={sourcesList}
          onClose={() => setSelectedClaim(null)}
        />
      )}
    </DashboardLayout>
  );
};

export default App;

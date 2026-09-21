import React, { useState } from 'react';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardView } from './components/Sidebar';
import { WorkspacePage } from './pages/WorkspacePage';
import { MyResearchPage } from './pages/MyResearchPage';
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
  const [activeView, setActiveView] = useState<DashboardView>('research');

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

  // Reset / Start new query
  const handleResetRun = () => {
    setCurrentRun(null);
    setActiveView('research');
  };

  // Select Run from history
  const handleSelectRun = (run: ResearchRunResponse) => {
    setCurrentRun(run);
    setActiveView('research');
  };

  // Add an experiment run
  const handleAddExperimentRun = (newRun: ExperimentRun) => {
    setExperimentRuns((prev) => [newRun, ...prev]);
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
      savedRunsCount={historyRuns.length}
    >
      {activeView === 'research' && (
        <WorkspacePage
          activeRun={currentRun}
          synthesisResult={synthesisResult}
          isLoading={runLoading}
          error={runError}
          onSubmitQuestion={handleSubmitQuestion}
          onReset={handleResetRun}
          onNavigateView={(view) => setActiveView(view)}
          isDemo={isDemo}
        />
      )}

      {activeView === 'my-research' && (
        <MyResearchPage
          runs={historyRuns}
          onSelectRun={handleSelectRun}
          onNewResearch={handleResetRun}
        />
      )}

      {activeView === 'evidence' && (
        <EvidencePage
          evidenceList={evidenceList}
          claimsList={synthesisResult?.claims || (isDemo ? DEMO_CLAIMS : [])}
          onSelectClaim={(claim) => setSelectedClaim(claim)}
        />
      )}

      {activeView === 'sources' && (
        <SourcesPage
          sourcesList={sourcesList}
          onViewEvidence={() => setActiveView('evidence')}
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
          evidenceList={evidenceList}
          onNavigateHome={() => setActiveView('research')}
        />
      )}

      {activeView === 'system-details' && <ArchitecturePage />}

      {/* Provenance Lineage Modal */}
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

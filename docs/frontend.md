# ResearchOS Frontend Dashboard (Milestone 7)

The **ResearchOS Frontend Dashboard** is a high-density, demo-ready web application built to visually showcase all capabilities of the autonomous AI research engineer. It connects directly to the FastAPI backend while adhering strictly to the **₹0 cost** constraint — requiring zero paid UI libraries, zero paid charting dependencies, and zero paid cloud hosting.

---

## 1. Technology Stack

- **Framework**: React 18 + TypeScript
- **Bundler & Tooling**: Vite 5
- **Styling**: Tailwind CSS 3 (Dark/Light mode support, high-density academic UI)
- **Testing**: Vitest 1.6
- **Visualizations**: Pure native SVG bar charts (`MetricsChart.tsx`) — 0 bundle bloat, 0 runtime charting overhead.
- **Cost**: **₹0.00 / $0.00**

---

## 2. Core Architectural Views

The dashboard is structured into 7 primary operational consoles accessible via the sidebar:

### 1. Research Workspace (`WorkspacePage.tsx`)
- **Objective Input**: Allows submitting research queries, specifying academic disciplines, and configuring maximum agent iterations (1–5).
- **Curated Benchmarks**: Quick-load buttons for standardized academic queries (e.g. *Dense vs Hybrid RAG Retrieval*, *Citation Grounding*).
- **Autonomous Research Lifecycle (`StageProgress.tsx`)**: Live visual tracker highlighting progression across the 8 deterministic stages:
  1. *Question Formulation*
  2. *Planning*
  3. *Research*
  4. *Evidence Audit*
  5. *Experiments*
  6. *Synthesis*
  7. *Citation Audit*
  8. *Final Report*
- **Active Run Telemetry**: Real-time counter of iterations, tasks completed, evidence chunks retrieved, and agent confidence scores.

### 2. Research Runs & Telemetry (`RunsPage.tsx`)
- **Execution Timeline**: Step-by-step trace stream recording LangGraph node executions (`planner`, `researcher`, `verifier`, `critic`, `experimenter`, `synthesizer`, `citation_validator`).
- **State Decomposition**: Full inspection of sub-task objectives, assigned agents, and task completion statuses.
- **Event Inspection**: Clickable trace cards showing exact execution timestamps, iteration rounds, and payload details.

### 3. Evidence Explorer & Grounding DAG (`EvidencePage.tsx`)
- **Chunk Explorer**: Searchable and filterable grid of all retrieved evidence snippets.
- **Filtering**: By extraction method (`pdf_section_chunk`, `pdf_table_extract`, `arxiv_abstract_ingest`, `hybrid_rag_dense`) and confidence thresholds.
- **Interactive Provenance Inspection (`ClaimModal.tsx`)**: Clicking any claim or evidence opens an interactive modal revealing the multi-hop provenance DAG:
  $$\text{Claim} \longrightarrow \text{Evidence Chunk} \longrightarrow \text{Primary Source} \longrightarrow \text{Page \& Section Coordinates}$$

### 4. Literature & Paper Acquisition (`SourcesPage.tsx`)
- **arXiv Search**: Direct discovery of open-access preprints using the free arXiv API.
- **Paper Cards**: Displays title, author roster, publication date, categories, expandable abstract, and direct PDF download links.
- **Ingestion**: Allows one-click ingestion into the local RAG corpus.

### 5. Experiment Engine (`ExperimentsPage.tsx`)
- **Benchmark Catalog**: Pre-configured sandboxed routines (`ranking_evaluation`, `chunking_benchmark`, `retrieval_comparison`).
- **Safe Execution**: Trigger parameter-controlled benchmark runs isolated within local execution constraints (10s timeout, zero external egress).
- **Empirical Metrics**: Visualizes MRR, NDCG@10, Recall@20, and Latency via pure SVG charts with side-by-side metric cards.
- **Artifact Export**: One-click JSON download of experiment configurations, metrics, and logs.

### 6. Research Synthesis & Quality Audit (`ReportsPage.tsx`)
- **Publication Reader**: Multi-tab viewer offering *Rendered Report*, *Raw Markdown*, and *Citations & Provenance*.
- **Quality Control Audit Panel**: Real-time evaluation of:
  - Provenance Completeness (%)
  - Citation Correctness (%)
  - Unsupported Claim Rate (strictly flagged if > 0)
  - Contradiction Count
- **Export**: Full report export as standard GitHub-flavored Markdown (`.md`) or machine-readable JSON (`.json`).

### 7. System Architecture (`ArchitecturePage.tsx`)
- **End-to-End Diagram**: Comprehensive visual breakdown of the 8-stage deterministic pipeline.
- **Cost Audit Table**: Verification of every technology layer proving operational expenses are ₹0.00.

---

## 3. Offline Demo Mode

To allow complete exploration without running backend server processes or downloading local Ollama weights, the dashboard features a built-in **Deterministic Offline Demo Mode**:
- Toggled via the top navigation bar (`Demo Mode: ON / OFF`).
- Backed by a curated synthetic academic benchmark in `mockData.ts` (*Vaswani et al.*, *Robertson & Zaragoza*, *Karpukhin et al.*).
- Completely isolated: Zero mock data is displayed when Demo Mode is off and connected to a live backend.

---

## 4. Running the Frontend

### Development Server
```bash
cd frontend
npm.cmd run dev
```
The dashboard runs at `http://localhost:5173` and proxies backend requests to `http://127.0.0.1:8000`.

### Running Tests
```bash
cd frontend
npm.cmd test
```
Executes 25 comprehensive Vitest tests verifying mock data integrity, API client simulation, UI component server rendering, and page views.

### Production Build
```bash
cd frontend
npm.cmd run build
```
Compiles TypeScript and bundles production assets into `frontend/dist/` in under 1 second.

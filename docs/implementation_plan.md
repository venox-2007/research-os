# ResearchOS — Roadmap & Implementation Plan

This implementation plan establishes the roadmap for transforming ResearchOS into an autonomous, portfolio-grade AI Research Engineer while operating under a strict **₹0-cost constraint**.

---

## Milestone Breakdown (M1 – M8)

### Milestone 1: Engineering Foundation (CURRENT)
- [x] Establish modular repository layout (`backend/`, `frontend/`, `tests/`, `docs/`, `scripts/`, `data/`).
- [x] FastAPI backend factory with `/health`, versioned routing (`/api/v1`), and standardized error handling.
- [x] Centralized environment configuration via Pydantic Settings (`.env.example`, zero-cost defaults).
- [x] Unified structured logging with configurable log levels.
- [x] Core domain Pydantic models (`ResearchQuestion`, `ResearchPlan`, `ResearchTask`, `Source`, `Evidence`, `Citation`, `Experiment`, `ResearchResult`).
- [x] LLM Provider Abstraction layer (`BaseLLMProvider`) with deterministic offline `MockLLMProvider`.
- [x] Minimal React + Vite + TypeScript frontend with health status badge and question submission interface.
- [x] Complete deterministic pytest suite with zero network/API key dependencies.
- [x] Developer tooling (pyproject.toml, ruff, pytest, Windows compatibility).
- [x] Comprehensive architecture documentation.

---

### Milestone 2: Research Acquisition + Paper Ingestion (COMPLETED)
- [x] `backend/tools/arxiv.py`: Asynchronous arXiv API client parsing Atom XML into normalized `Source` objects.
- [x] `backend/tools/semantic_scholar.py`: Semantic Scholar Academic Graph client with exponential backoff on HTTP 429 rate limits.
- [x] `backend/core/models.py`: Unified `Source` domain model with standardized `pdf_url` property and provider metadata.
- [x] `backend/ingestion/pdf_downloader.py`: Streaming PDF downloader with size limits (50MB threshold), magic bytes verification (`%PDF-`), and deterministic local disk caching.
- [x] `backend/ingestion/pdf_parser.py`: PyMuPDF-based extractor preserving 1-indexed page boundaries, page text, and scanned/blank page markers.
- [x] `backend/ingestion/chunker.py`: Structure-aware academic chunker identifying headings (Abstract, Introduction, Methodology, Experiments, Results, Discussion, Conclusion, References) with page coordinate tracking and fallback chunking.
- [x] `backend/ingestion/pipeline.py`: IngestionPipeline coordinator uniting download, extraction, chunking, and local filesystem caching.
- [x] `backend/api/v1/endpoints/papers.py`: REST endpoints `/api/v1/papers/search`, `/api/v1/papers/ingest`, and `/api/v1/papers/{doc_id}/chunks`.
- [x] 100% offline, deterministic pytest suite (50 passing tests).

---

### Milestone 3: Hybrid RAG + Evidence Store (COMPLETED)
- [x] `backend/rag/embeddings.py`: Local 384-d dense embedding generation via `sentence-transformers` (`all-MiniLM-L6-v2`) with CUDA/CPU auto-detection, batching, and mock mode.
- [x] `backend/rag/vector_store.py`: `FAISSVectorStore` backed by `IndexFlatIP` with disk persistence (`faiss.index` + `faiss_metadata.json`).
- [x] `backend/rag/bm25.py`: `BM25Index` using `BM25Okapi` with specialized tokenization, academic stopword removal, and disk persistence (`bm25_metadata.json`).
- [x] `backend/rag/hybrid.py`: Parameter-free Reciprocal Rank Fusion (RRF) with smoothing constant $k=60$.
- [x] `backend/rag/reranker.py`: Local `CrossEncoder` reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) scoring joint token cross-attention.
- [x] `backend/rag/indexer.py`: `RAGIndexer` scanning `data/chunks/` with incremental caching and rebuild support.
- [x] `backend/rag/pipeline.py`: `RAGPipeline` end-to-end coordinator capturing detailed runtime diagnostics.
- [x] `backend/evidence/store.py`: `SQLiteEvidenceStore` with full lineage, chunk deduplication, upsert, and provenance metadata.
- [x] `backend/api/v1/endpoints/rag.py`: REST endpoints `/api/v1/rag/index`, `/api/v1/rag/search`, `/api/v1/rag/stats`, `/api/v1/evidence`, `/api/v1/evidence/{evidence_id}`.
- [x] `backend/rag/evaluation.py`: Automated IR benchmark suite on 20 gold documents and 16 benchmark queries (Recall@K, Precision@K, MRR, nDCG@K).
- [x] 100% offline, deterministic pytest suite (83 passing tests).

---

### Milestone 4: Agentic Research Orchestration (COMPLETED)
- [x] `backend/agents/events.py`: Structured execution trace telemetry (`TraceEvent`, `TraceCollector`).
- [x] `backend/agents/state.py`: Strongly typed, serializable `ResearchState` (LangGraph TypedDict), `VerificationResult`, `CriticEvaluation`, and `ResearchRunResult`.
- [x] `backend/agents/tools/`: Unified `ToolRegistry` exposing `search_rag`, `search_arxiv`, `search_semantic_scholar`, `web_search`, and `ingest_paper` with ₹0-cost guarantees and deterministic offline mock support.
- [x] `backend/agents/planner.py`: Autonomous `ResearchPlanner` generating prioritized task decompositions with structured JSON parsing and heuristic fallback.
- [x] `backend/agents/researcher.py`: `ResearchWorker` node executing pending research tasks via `ToolRegistry`.
- [x] `backend/agents/verifier.py`: `EvidenceVerifier` auditing retrieved excerpts for relevance, claim support (`supported`, `partially_supported`, `unsupported`), and flagging contradictions.
- [x] `backend/agents/critic.py`: `ResearchCritic` assessing research completeness, spawning refinement tasks, and enforcing hard iteration boundaries.
- [x] `backend/agents/graph.py`: LangGraph `StateGraph(ResearchState)` linking Planner -> Researcher -> Verifier -> Critic -> Finish with conditional refinement routing.
- [x] `backend/api/v1/endpoints/research.py`: REST endpoints `POST /api/v1/research/run` and `GET /api/v1/research/run/{run_id}`.
- [x] `backend/agents/evaluation.py`: Benchmark suite evaluating 6 academic research queries with 100% pass rate.
- [x] 100% offline, deterministic pytest suite (106 passing tests).

---

### Milestone 5: Safe Experiment Engine (COMPLETED)
- [x] `backend/experiments/models.py`: Strongly typed Pydantic models for experiment specifications, configurations, metrics, and runs.
- [x] `backend/experiments/datasets.py`: `DatasetRegistry` with SHA-256 integrity checks, path traversal defenses, and built-in synthetic generators.
- [x] `backend/experiments/metrics.py`: Classification, regression, and ranking evaluation metrics, summary statistics, bootstrap confidence intervals, and paired t-tests.
- [x] `backend/experiments/artifacts.py`: Sandboxed `ArtifactStore` generating `metrics.json`, `predictions.csv`, `summary.json`, and headless `matplotlib` figures (`Agg` backend).
- [x] `backend/experiments/registry.py`: `ExperimentRegistry` with approved routines (`linear_regression_benchmark`, `classification_eval`, `ranking_evaluation`, `ablation_parameter_sweep`, `statistical_significance_test`).
- [x] `backend/experiments/runner.py`: `SafeExperimentRunner` enforcing injection scanning, whitelisted routine execution, timeout supervision, and hardware telemetry.
- [x] `backend/experiments/reproducibility.py`: Deterministic environment profiling and automated reproducibility verification ($\Delta < 10^{-5}$).
- [x] `backend/experiments/planner.py`: Autonomous `ExperimentPlanner` translating research tasks into valid `ExperimentSpec`s.
- [x] `backend/experiments/provenance.py`: Full lineage tracking converting experiment runs to evidence records (`convert_experiment_to_evidence`).
- [x] `backend/agents/tools/experiment_tool.py`: `ExperimentPlanTool` and `ExperimentRunTool` integrated into LangGraph `ToolRegistry`.
- [x] `backend/api/v1/endpoints/experiments.py`: REST endpoints `/api/v1/experiments/plan`, `/api/v1/experiments/run`, `/api/v1/experiments/specs/{spec_id}`, `/api/v1/experiments/runs/{run_id}`, `/api/v1/experiments/runs/{run_id}/artifacts`, `/api/v1/experiments/runs/{run_id}/artifacts/{filename}`, and `/api/v1/experiments/catalog`.
- [x] `backend/experiments/evaluation.py`: Benchmark suite evaluating 9 tasks across planning, execution, reproducibility, and security (100% pass rate).
- [x] 100% offline, deterministic pytest suite (150 passing tests).

---

### Milestone 6: Research Synthesis + Citation Verification + Final Report Engine (COMPLETED)
- [x] `backend/synthesis/models.py`: Strongly typed Pydantic models for report specifications, sections, claims, claim-evidence links, citations, validation audits, artifacts, and synthesis results.
- [x] `backend/synthesis/provenance.py`: Multi-hop `ProvenanceGraph` linking questions, tasks, claims, evidence, sources, and experiment runs with lineage tracing and completeness scoring.
- [x] `backend/synthesis/citations.py`: Anti-hallucination `CitationFormatter` and `CitationManager` supporting IEEE and APA styles with explicit missing-metadata representation (`[Author Unknown]`, `n.d.`).
- [x] `backend/synthesis/verifier.py`: 10-point `CitationVerifier` enforcing evidence grounding, coordinate matching, experiment metric validation, and contradiction detection.
- [x] `backend/synthesis/validator.py`: Comprehensive `ReportValidator` evaluating mathematical quality ratios (`citation_coverage`, `evidence_coverage`, `unsupported_claim_rate`, `provenance_completeness`, `citation_correctness`).
- [x] `backend/synthesis/engine.py`: Evidence-first `SynthesisEngine` building evidence-backed outlines, drafting prose with inline citations (`[N]`), safe revision loops, and artifact archival.
- [x] `backend/synthesis/graph.py`: Stateful LangGraph synthesis workflow (`synthesis_planner` -> `claim_builder` -> `report_writer` -> `citation_verifier` -> `report_validator` -> `finish_report`).
- [x] `backend/api/v1/endpoints/reports.py`: REST endpoints `/api/v1/reports/generate`, `/{report_id}`, `/{report_id}/claims`, `/{report_id}/validation`, `/{report_id}/artifacts`, `/{report_id}/artifacts/{filename}`.
- [x] `backend/synthesis/evaluation.py`: Comprehensive benchmark suite evaluating 6 scenarios with 100% pass rate.
- [x] 100% offline, deterministic pytest suite (182 passing tests).

---

### Milestone 7: Frontend / Research Dashboard
- **Objective**: Deliver a comprehensive user interface for monitoring research progress and inspecting deliverables.
- [x] React 18 + TypeScript + Vite 5 + Tailwind CSS high-density research console (`₹0` cost).
- [x] 7 dedicated views: Workspace (8-stage progress tracker), Research Runs (LangGraph trace timeline), Evidence Explorer (Claim-to-Evidence Grounding DAG modal), Sources / Literature (arXiv discovery & paper cards), Experiment Engine (pure SVG metrics charts & runner), Research Reports (Markdown reader with quality control audit panel), and System Architecture.
- [x] Deterministic Offline Demo Mode with rich synthetic benchmark data (`Vaswani et al.`, `Robertson & Zaragoza`, `Karpukhin et al.`).
- [x] Full test suite with 25 passing Vitest tests (`npm.cmd test`).
- [x] Production build passes cleanly with 0 warnings/errors (`npm.cmd run build`).
- **Verification**: All 25 frontend tests pass, 182 backend tests pass, full end-to-end integration verified.

---

### Milestone 8: Evaluation + Benchmarks + Final Documentation
- **Objective**: Validate ResearchOS against standard benchmarks and publish open-source documentation.
- **Components**:
  - Benchmark evaluation on academic Q&A datasets.
  - Verification accuracy scoring (citation precision/recall).
  - Complete portfolio documentation, video walkthrough, and installation guide for Windows, Linux, and macOS.
- **Verification**: Publish reproducible evaluation results showing zero financial cost across all operations.

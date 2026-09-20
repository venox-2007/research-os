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

### Milestone 3: Hybrid RAG + Evidence Store
- **Objective**: Construct a zero-cost local hybrid retrieval system with verbatim evidence tracking.
- **Components**:
  - `backend/rag/dense.py`: Dense embedding generation with local `sentence-transformers` (`all-MiniLM-L6-v2`) and local `FAISS` index.
  - `backend/rag/sparse.py`: Lexical BM25 indexing for exact keyword and symbol retrieval.
  - `backend/rag/fusion.py`: Reciprocal Rank Fusion (RRF) combining dense and sparse search results.
  - `backend/evidence/store.py`: Local SQLite evidence repository linking chunks directly to `Source` references, sections, and page coordinates.
- **Verification**: Run multi-hop queries against ingested papers; confirm RRF precision and accurate evidence snippet provenance.

---

### Milestone 4: LangGraph Agent System
- **Objective**: Coordinate autonomous multi-agent research planning and execution.
- **Components**:
  - `backend/agents/state.py`: LangGraph typed state representing the evolving research context.
  - `backend/agents/supervisor.py`: Task decomposition and plan generation agent.
  - `backend/agents/researcher.py`: Paper query, acquisition, and retrieval agent.
  - `backend/agents/graph.py`: State graph connecting agents, conditional routing, and termination criteria.
  - Ollama local LLM integration (`backend/llm/ollama.py`) enabling fully offline agent decision-making.
- **Verification**: End-to-end execution of a research question yielding a populated `ResearchPlan` and executed tasks.

---

### Milestone 5: Experiment Engine
- **Objective**: Local computational experiment execution to empirically test hypotheses.
- **Components**:
  - `backend/experiments/designer.py`: Agent producing executable Python experiment scripts with validation checks.
  - `backend/experiments/sandbox.py`: Process isolation, timeout supervision, memory safeguards, and standard I/O capture.
  - `backend/experiments/metrics.py`: Metric parsing and visualization generation (`matplotlib`).
- **Verification**: Run a local benchmarking experiment (e.g. data fitting or model evaluation script), log metrics, and save output charts.

---

### Milestone 6: Critic + Citation Verification + Research Synthesis
- **Objective**: Eliminate hallucinations through rigorous citation verification and compile academic-quality reports.
- **Components**:
  - `backend/evidence/verifier.py`: NLI / entailment checking matching generated claims against raw evidence snippets.
  - `backend/evidence/citation.py`: Automated inline citation generation (`[1]`, `[2]`) linked to verified sources.
  - `backend/agents/critic.py`: Critical review agent identifying unsupported claims and directing research refinement.
  - `backend/agents/synthesizer.py`: Academic research report synthesis in Markdown/LaTeX format.
- **Verification**: Generate a research report where 100% of claims are mapped to verified citations.

---

### Milestone 7: Frontend / Research Dashboard
- **Objective**: Deliver a comprehensive user interface for monitoring research progress and inspecting deliverables.
- **Components**:
  - Real-time agent status and graph execution visualization.
  - Evidence inspection modal showing verbatim text excerpts and original PDF pages.
  - Interactive experiment runner and metrics display.
  - Research report reader with interactive citation hovercards and BibTeX export.
- **Verification**: Run an entire research query from the UI and review the generated report and citations.

---

### Milestone 8: Evaluation + Benchmarks + Final Documentation
- **Objective**: Validate ResearchOS against standard benchmarks and publish open-source documentation.
- **Components**:
  - Benchmark evaluation on academic Q&A datasets.
  - Verification accuracy scoring (citation precision/recall).
  - Complete portfolio documentation, video walkthrough, and installation guide for Windows, Linux, and macOS.
- **Verification**: Publish reproducible evaluation results showing zero financial cost across all operations.

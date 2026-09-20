# ResearchOS — Autonomous AI Research Engineer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Cost](https://img.shields.io/badge/Cost-₹0_Free-brightgreen.svg)](#critical-constraint--0-cost)

**ResearchOS** is an autonomous AI Research Engineer designed to accept complex scientific queries, autonomously explore academic literature and the web, execute hybrid RAG, maintain traceable evidence, design and execute empirical experiments in a local sandbox, critique its findings, verify citations, and synthesize evidence-backed research reports.

---

## Critical Constraint: ₹0 Cost

The entire architecture is designed to run with **zero financial cost**:
- **Zero Paid APIs**: Uses local models (via Ollama) or free-tier APIs (e.g., Google Gemini free tier).
- **Zero Paid Databases**: In-process FAISS vector indexing, SQLite metadata store, local disk storage.
- **Zero Cloud Infrastructure**: Runs entirely on local consumer hardware (Windows 11 / Linux / macOS).

---

## Architecture Overview

```
research-os/
├── backend/
│   ├── agents/          # Multi-agent graph orchestration (Planned M4)
│   ├── rag/             # Dense FAISS + Sparse BM25 Hybrid RAG (Planned M3)
│   ├── tools/           # arXiv, Semantic Scholar, Web retrieval (Planned M2)
│   ├── ingestion/       # PDF parsing & structure-aware chunking (Planned M2)
│   ├── evidence/        # Provenance mapping & citation verification (Planned M3/M6)
│   ├── experiments/     # Sandboxed code execution engine (Planned M5)
│   ├── llm/             # LLM provider abstraction & mock engine
│   ├── api/             # FastAPI REST endpoints (/health, /api/v1/research)
│   └── core/            # Configuration, structured logging, domain models, app factory
├── frontend/            # React 18 + Vite + TypeScript user interface
├── tests/               # Deterministic, offline unit & integration test suite
├── docs/                # Architecture blueprint and roadmap documentation
├── scripts/             # Windows-friendly launch scripts
├── data/                # Local data directory for indices, cache, and sandboxes
├── .env.example         # Environment template
└── pyproject.toml       # Python project metadata and tooling config
```

For complete architectural details, see [docs/architecture.md](docs/architecture.md).

---

## Milestone Roadmap

- [x] **Milestone 1 — Engineering Foundation**: FastAPI backend factory, configuration, domain models, LLM provider abstraction with mock provider, developer tooling, React + Vite + TypeScript frontend, deterministic test suite.
- [x] **Milestone 2 — Research Acquisition + Paper Ingestion**: Free arXiv API client, Semantic Scholar client with rate-limit backoff, streaming PDF downloader with magic-byte verification, PyMuPDF page-level extraction, structure-aware academic chunking, and local cache management.
- [ ] **Milestone 3 — Hybrid RAG + Evidence Store**: Local `sentence-transformers` + FAISS dense search, BM25 sparse search, Reciprocal Rank Fusion, SQLite evidence store.
- [ ] **Milestone 4 — LangGraph Agent System**: Autonomous multi-agent coordination (Supervisor, Researcher, Experimenter, Critic).
- [ ] **Milestone 5 — Experiment Engine**: Automated experiment script generation, sandboxed execution, metrics extraction.
- [ ] **Milestone 6 — Critic + Citation Verification + Research Synthesis**: Claim-to-evidence entailment verification, citation generation, synthesis.
- [ ] **Milestone 7 — Frontend / Research Dashboard**: Real-time agent execution visualization, evidence viewer, interactive report reader.
- [ ] **Milestone 8 — Evaluation + Benchmarks + Final Documentation**: Standardized evaluation benchmarks and publication.

For the full milestone roadmap, see [docs/implementation_plan.md](docs/implementation_plan.md).

---

## Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js LTS (v20+) & npm
- Git

### 1. Clone & Configure
```bash
git clone https://github.com/venox-2007/research-os.git
cd research-os
cp .env.example .env
```

### 2. Backend Setup
Install dependencies and run the development server:
```bash
python -m pip install -e ".[dev]"
# Or run with uvicorn:
python -m uvicorn backend.core.app:create_app --factory --port 8000 --reload
```
API Documentation will be accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will be accessible at [http://localhost:5173](http://localhost:5173).

### 4. Paper Search & Ingestion Testing (Milestone 2)
With the backend running, search and ingest papers using the REST API:
```bash
# Search arXiv papers (free, zero API keys required)
curl "http://127.0.0.1:8000/api/v1/papers/search?query=transformer+scaling&provider=arxiv&limit=3"

# Ingest an academic paper (download, parse, structure-chunk, and cache)
curl -X POST "http://127.0.0.1:8000/api/v1/papers/ingest" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://arxiv.org/pdf/1706.03762.pdf", "title": "Attention Is All You Need"}'

# Retrieve structure-aware chunks for an ingested paper
curl "http://127.0.0.1:8000/api/v1/papers/doc_1706.03762/chunks"
```

### 5. Running Tests
All tests are 100% offline, deterministic, and require no API keys:
```bash
python -m pytest tests/ -v
```

### 5. Linting & Formatting
```bash
python -m ruff check backend tests
python -m ruff format --check backend tests
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

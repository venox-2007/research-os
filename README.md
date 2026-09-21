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
- [x] **Milestone 3 — Hybrid RAG + Evidence Store**: Local `sentence-transformers` (`all-MiniLM-L6-v2`) + FAISS IndexFlatIP dense search, BM25Okapi sparse search, Reciprocal Rank Fusion (RRF, k=60), Cross-Encoder reranker (`ms-marco-MiniLM-L-6-v2`), SQLite evidence store with provenance tracking, and full IR evaluation benchmark suite.
- [x] **Milestone 4 — Agentic Research Orchestration**: Deterministic LangGraph state machine (Planner, Researcher, Verifier, Critic, Finish), unified ToolRegistry (hybrid RAG, arXiv, Semantic Scholar, web search, paper ingestion), automated evidence auditing with contradiction detection, bounded refinement loops, and benchmark evaluation suite.
- [ ] **Milestone 5 — Experiment Engine**: Automated experiment script generation, sandboxed execution, metrics extraction.
- [ ] **Milestone 6 — Critic + Citation Verification + Research Synthesis**: Claim-to-evidence entailment verification, citation generation, synthesis.
- [ ] **Milestone 7 — Frontend / Research Dashboard**: Real-time agent execution visualization, evidence viewer, interactive report reader.
- [ ] **Milestone 8 — Evaluation + Benchmarks + Final Documentation**: Standardized evaluation benchmarks and publication.

For the full milestone roadmap, see [docs/implementation_plan.md](docs/implementation_plan.md).
For detailed retrieval architecture, see [docs/rag.md](docs/rag.md).
For multi-agent orchestration specifications, see [docs/agents.md](docs/agents.md).

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

### 4. Paper Acquisition & Ingestion (Milestone 2)
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

### 5. Hybrid RAG & Evidence Retrieval (Milestone 3)
```bash
# Index all cached chunks into FAISS vector store & BM25 keyword index
curl -X POST "http://127.0.0.1:8000/api/v1/rag/index" \
     -H "Content-Type: application/json" \
     -d '{"rebuild": false}'

# Execute hybrid search with Reciprocal Rank Fusion & Cross-Encoder reranking
curl -X POST "http://127.0.0.1:8000/api/v1/rag/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "multi-head attention mechanism", "top_k": 3}'

# Retrieve recent verified evidence items with provenance coordinates
curl "http://127.0.0.1:8000/api/v1/evidence?limit=10"
```

### 6. Autonomous Research Loop (Milestone 4)
Trigger the full LangGraph orchestration loop (Planner -> Researcher -> Verifier -> Critic):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/research/run" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What are the computational trade-offs of hybrid RAG vs dense-only retrieval?",
       "discipline": "Information Retrieval",
       "constraints": ["focus on latency and reciprocal rank fusion"],
       "max_iterations": 2
     }'
```

### 7. Evaluation Benchmarks
Run the automated evaluation benchmarks:
```bash
# Milestone 3 — Hybrid RAG retrieval benchmark (BM25, Dense, Hybrid, Reranker)
python -m backend.rag.evaluation

# Milestone 4 — Agentic research orchestration benchmark
python -m backend.agents.evaluation
```

### 8. Running Tests
All tests are 100% offline, deterministic, and require no API keys:
```bash
python -m pytest tests/ -v
```

### 9. Linting & Formatting
```bash
python -m ruff check backend tests
python -m ruff format --check backend tests
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

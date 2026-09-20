# ResearchOS — Architecture Blueprint

> Autonomous AI Research Engineer operating under a strict **₹0-cost constraint**.
> Designed for local-first, privacy-preserving, transparent, and reproducible scientific exploration.

---

## 1. Architectural Philosophy & Zero-Cost Principles

ResearchOS is engineered to execute end-to-end academic research workflows autonomously without reliance on paid APIs, paid vector databases, or proprietary cloud infrastructure:

1. **Zero Financial Overhead (₹0 Cost)**:
   - Primary LLM inference targets local runtimes via **Ollama** (`llama3.2`, `qwen2.5`, `deepseek-r1`) or optional free-tier endpoints (e.g. Google Gemini free-tier).
   - Embedding models run locally via `sentence-transformers` (e.g. `all-MiniLM-L6-v2`, `bge-small-en-v1.5`).
   - Vector storage uses in-process **FAISS** index backed by local disk storage (`./data`).
   - Academic paper sourcing uses open APIs: **arXiv API**, **Semantic Scholar API** (free tier), and direct open-access PDF acquisition.
2. **Deterministic Evidence Traceability**:
   - Every synthesized claim must cite a verified snippet with verbatim quotation, page/section coordinates, and confidence score.
   - A dedicated **Critic Agent** cross-checks citations against retrieved evidence to eliminate hallucinations before final report compilation.
3. **Reproducible Experimentation**:
   - Scientific claims requiring verification are validated through sandboxed local code execution that captures telemetry, metrics, and generated artifacts.

---

## 2. System Architecture Diagram

```
+-----------------------------------------------------------------------------+
|                                 User Client                                 |
|                       React 18 + Vite + TypeScript                          |
+---------------------------------------+-------------------------------------+
                                        | HTTP / REST (CORS enabled)
                                        v
+-----------------------------------------------------------------------------+
|                              FastAPI Gateway                                |
|           Versioned Endpoints: /health, /api/v1/research/*                  |
|           Pydantic Validation, Structured Error Handling, Lifespan Hooks   |
+---------------------------------------+-------------------------------------+
                                        |
       +--------------------------------+-------------------------------+
       |                                |                               |
       v                                v                               v
+--------------+               +------------------+           +-----------------+
|  Agents Core |               |    Hybrid RAG    |           | Experiment Exec |
| (LangGraph)  |               | (FAISS + BM25)   |           |    (Sandbox)    |
+-------+------+               +--------+---------+           +--------+--------+
        |                               |                              |
        v                               v                              v
+--------------+               +------------------+           +-----------------+
| LLM Provider |               | Paper Ingestion  |           | Local Storage   |
| Abstraction  |               | (PyMuPDF/Docling)|           | SQLite / Files  |
+-------+------+               +------------------+           +-----------------+
        |
  +-----+-----+
  |           |
  v           v
[Ollama]   [Free-Tier Gemini]
(Local)    (Fallback)
```

---

## 3. Module Responsibilities & Boundary Separation

```
research-os/
├── backend/
│   ├── agents/          # Agent definitions, state machines, and LangGraph workflows
│   ├── rag/             # Dense & sparse indexing, retrieval, and fusion ranking
│   ├── tools/           # External search tools (arXiv, Semantic Scholar, Web)
│   ├── ingestion/       # PDF parsing, document normalization, and semantic chunking
│   ├── evidence/        # Provenance tracking, claim-to-source mapping, citation verification
│   ├── experiments/     # Local code execution sandbox, metrics extraction, plotting
│   ├── llm/             # LLM provider interface, factory, and mock/local adapters
│   ├── api/             # FastAPI routers, request/response models, controllers
│   └── core/            # Configuration, logging, domain models, and app factory
├── frontend/            # React + Vite + TypeScript user dashboard
├── tests/               # Offline, deterministic unit and integration test suite
├── docs/                # Architecture specifications and milestone roadmaps
├── scripts/             # Operational launch scripts for Windows and POSIX
└── data/                # Local data directory for indices, cache, and sandbox runs
```

### Module Responsibilities:

| Module | Primary Responsibility |
| :--- | :--- |
| `backend.core` | Centralized Pydantic settings, standardized logging, domain models (`ResearchQuestion`, `Source`, `Evidence`, `Citation`, `Experiment`, `ResearchResult`), and FastAPI factory. |
| `backend.api` | Versioned RESTful API endpoints (`/api/v1/...`), status probes (`/health`), and CORS/middleware management. |
| `backend.llm` | Provider-agnostic interface (`BaseLLMProvider`) insulating ResearchOS from specific LLM implementations. Contains `MockLLMProvider` for offline testing and future adapters for Ollama and Gemini. |
| `backend.ingestion` | Ingests PDF research papers using open-source parsers (`PyMuPDF` / `Docling`), strips headers/footers, extracts section hierarchies, and performs structure-aware chunking. |
| `backend.rag` | Implements hybrid retrieval fusing local FAISS vector search (`sentence-transformers`) with sparse BM25 lexical search using Reciprocal Rank Fusion (RRF). |
| `backend.evidence` | Tracks the lineage of each research finding back to exact source coordinates, ensuring every statement in a research report is backed by verifiable text. |
| `backend.experiments` | Generates and runs localized Python verification scripts in an isolated process sandbox, capturing stdout, stderr, execution status, and numerical metrics. |
| `backend.agents` | Multi-agent coordination built on LangGraph (Supervisor, Literature Researcher, Experimenter, and Critic). |
| `backend.tools` | Deterministic tool execution for fetching papers from arXiv, Semantic Scholar, and local filesystem caches without fees. |

---

## 4. Planned Multi-Agent Workflow (LangGraph)

In Milestone 4, the autonomous workflow is orchestrated via a state graph:

```
                  +---------------------------+
                  |  User Research Question   |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |     Supervisor Agent      |
                  |  (Decomposes into Plan)   |
                  +-------------+-------------+
                                |
        +-----------------------+-----------------------+
        |                                               |
        v                                               v
+-------------------------------+             +-------------------------------+
|   Literature Research Agent   |             |       Experiment Agent        |
|  - Sourcing (arXiv, Scholar)  |             |  - Designs protocol / code    |
|  - Ingestion & Hybrid RAG     |             |  - Executes in local sandbox  |
|  - Evidence Extraction        |             |  - Extracts metrics & plots   |
+---------------+---------------+             +---------------+---------------+
        |                                               |
        +-----------------------+-----------------------+
                                |
                                v
                  +---------------------------+
                  |       Critic Agent        |
                  |  - Verifies claim support |
                  |  - Validates citations    |
                  |  - Flags hallucinations   |
                  +-------------+-------------+
                                |
                   [Pass Verification Check?]
                     /                    \
             (Yes)  /                      \ (No: Refine plan)
                   v                        v
     +--------------------------+    +--------------------------+
     |     Synthesis Agent      |    |    Supervisor Feedback   |
     | - Compiles final report  |    +--------------------------+
     | - Traceable citations    |
     +--------------------------+
```

---

## 5. LLM Provider Abstraction Layer

ResearchOS prevents vendor lock-in by decoupling business logic from inference endpoints through `BaseLLMProvider`:

- **`MockLLMProvider`**: Zero-cost, 100% offline, deterministic engine used for unit testing, CI pipelines, and initial scaffolding.
- **`OllamaProvider` (Planned M2/M4)**: Connects to local Ollama daemon (`http://localhost:11434`), supporting local models such as `llama3.2`, `qwen2.5`, or `deepseek-r1`.
- **`GeminiProvider` (Planned M2/M4)**: Optional connector utilizing Google AI Studio's free tier for environments with constrained local compute.

All providers return standardized `LLMResponse` objects containing normalized text, model tags, token usage metrics, and stop reasons.

---

## 6. Planned Hybrid RAG Architecture

Modern academic literature queries require both semantic similarity and exact keyword/symbol matching (e.g. formula names, hyperparameter symbols, author surnames).

1. **Dense Vector Search**:
   - Model: `sentence-transformers/all-MiniLM-L6-v2` (compact, runs on CPU/GPU locally).
   - Index: In-memory **FAISS** (IndexFlatIP or IndexHNSWFlat) serialized to `./data/indices`.
2. **Sparse Lexical Search**:
   - Model: **Rank-BM25** with custom academic stopword filtering and tokenization.
3. **Reciprocal Rank Fusion (RRF)**:
   - Rank score calculation:
     \[
     RRF(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{k + r_m(d)}
     \]
     where \(k = 60\) and \(r_m(d)\) is the rank of document \(d\) in retrieval method \(m\).
4. **Context Deduplication & Traceability**:
   - Chunks maintain foreign key references back to the parent `Source` with section titles and page indices.

---

## 7. Evidence & Citation Verification Subsystem

To guarantee research integrity:
1. **Evidence Model**: Stores verbatim snippet, source ID, page coordinate, section header, and extraction confidence score.
2. **Citation Model**: Stores APA/IEEE formatted citation string, inline reference marker (`[1]`), and verification boolean.
3. **Critic Verification Protocol**:
   - Every claim asserted in the final report is matched against the corresponding `Evidence.content`.
   - Natural Language Inference (NLI) or structured local LLM prompting assesses whether the evidence **entails**, **contradicts**, or is **neutral** to the claim.
   - Claims failing entailment verification are flagged or revised.

---

## 8. Sandboxed Experiment Execution Engine

For empirical computational research (e.g. algorithm benchmarking, data analysis):
1. **Isolated Subprocess Execution**: Scripts run in an isolated Python subprocess with constrained environment variables, working directory sandboxes (`./data/experiments/<exp_id>`), and timeout limits.
2. **Telemetry Capture**: Real-time streaming of stdout/stderr and exit code monitoring.
3. **Metric Extraction**: Automated JSON/regex extraction of numerical metrics into the `Experiment.metrics` key-value store.
4. **Artifact Archival**: Generated figures (PNG, SVG) and output datasets (CSV, JSON) are linked to the parent `ResearchQuestion`.

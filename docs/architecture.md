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

## 4. Multi-Agent Workflow (Milestone 4 — Implemented)

The autonomous research workflow is orchestrated via a deterministic, stateful LangGraph graph (`backend/agents/graph.py`):

```
                  +---------------------------+
                  |  User Research Question   |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |     Research Planner      |
                  |  (Decomposes into Plan)   |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |      Research Worker      |◄────────────────┐
                  |  (RAG, arXiv, S2, Web)    |                 │
                  +-------------+-------------+                 │
                                |                               │
                                v                               │
                  +---------------------------+                 │
                  |     Evidence Verifier     |                 │
                  |  - Audits claim support   |                 │
                  |  - Checks coordinates     |                 │
                  |  - Flags contradictions   |                 │
                  +-------------+-------------+                 │
                                |                               │ Refine Loop
                                v                               │ (is_sufficient = False
                  +---------------------------+                 │  & iter < max)
                  |      Research Critic      |                 │
                  |  - Evaluates sufficiency  |                 │
                  |  - Proposes new tasks     |                 │
                  +-------------+-------------+                 │
                                |                               │
                     [ Is Sufficient or Max? ]                  │
                                |                               │
                       No ──────┴───────────────────────────────┘
                       │
                      Yes
                       │
                       v
         +--------------------------+
         |       Finish Node        |
         |  - Consolidates context  |
         |  - Emits ResearchResult  |
         +--------------------------+
```

### Agent Node Roles:
- **`ResearchPlanner`**: Decomposes the research question into atomic, non-redundant tasks (`literature_search`, `rag_query`, `critique`, `paper_ingestion`).
- **`ResearchWorker`**: Dispatches tasks through `ToolRegistry` to query hybrid RAG, arXiv, Semantic Scholar, and web search.
- **`EvidenceVerifier`**: Audits retrieved snippets for relevance, claim support (`supported`, `partially_supported`, `unsupported`), and detects conflicting empirical findings.
- **`ResearchCritic`**: Evaluates completeness, determines whether the question is answered, proposes refinement tasks, and strictly enforces hard iteration limits (`max_iterations`).
- **`finish`**: Consolidates state into `final_context`, compiles execution traces, and transitions to `completed`.

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

---

## 9. Research Acquisition & Paper Ingestion Pipeline (Milestone 2)

Implemented in Milestone 2, this subsystem provides an automated, zero-cost bridge between academic repositories and structured text ready for RAG indexing.

```
[arXiv API / Semantic Scholar API]
                │
                ▼
       [Source Normalization]
  (title, authors, year, pdf_url, IDs)
                │
                ▼
       [PDF Downloader]
  (streaming, size guard, %PDF- magic bytes)
                │
                ▼
     [data/papers/*.pdf]
                │
                ▼
       [PyMuPDF PDF Parser]
  (page-level text, scanned/blank detection)
                │
                ▼
    [data/extracted/*.json]
                │
                ▼
   [Structure-Aware Chunker]
  (academic sections, page coordinate tracking)
                │
                ▼
     [data/chunks/*.json]
                │
                ▼
     (Ready for M3 Hybrid RAG)
```

### Core Components & Flow:

1. **Academic Discovery Clients**:
   - **`ArxivClient` (`backend/tools/arxiv.py`)**: Queries arXiv's public export API (`https://export.arxiv.org/api/query`), parsing Atom XML into strongly typed domain `Source` objects without web scraping or API keys.
   - **`SemanticScholarClient` (`backend/tools/semantic_scholar.py`)**: Searches the free Academic Graph API, retrieving citation counts, DOIs, venues, and open-access PDF links, equipped with exponential backoff for HTTP 429 rate limits.

2. **Unified Source Normalization**:
   - The `Source` model (`backend/core/models.py`) acts as the single canonical representation for papers from arXiv, Semantic Scholar, web links, or local PDFs. Provider-specific identifiers (`arxiv_id`, `doi`, `venue`, `citation_count`) are preserved in metadata while standardizing `pdf_url` access.

3. **Streaming PDF Downloader (`backend/ingestion/pdf_downloader.py`)**:
   - Streams PDF binaries in 64KB chunks to prevent high memory usage.
   - Enforces strict file size thresholds (`max_pdf_size_bytes`, default 50MB).
   - Validates magic bytes (`%PDF-`) before persisting to prevent HTML error pages from being treated as PDFs.
   - Employs deterministic file naming (`paper_<hash>.pdf` or `<arxiv_id>.pdf`) to deduplicate downloads.

4. **Page-Bounded PDF Extraction (`backend/ingestion/pdf_parser.py`)**:
   - Utilizes PyMuPDF (`pymupdf`) to extract text while maintaining strict 1-indexed page boundaries.
   - Categorizes pages: normal text, blank pages, and scanned/image-only pages.
   - Generates structured `ParsedDocument` containing ordered `ParsedPage` objects rather than a monolithic text dump.

5. **Structure-Aware Academic Chunking (`backend/ingestion/chunker.py`)**:
   - Identifies academic sections (Abstract, Introduction, Related Work, Methodology, Experiments, Results, Discussion, Conclusion, References) via header heuristics.
   - Preserves short sections (such as Abstract) as self-contained semantic units.
   - Subdivides longer sections using target character windows (~2,000 chars / ~500 tokens) with configurable sentence overlap.
   - Retains provenance coordinates on every chunk (`start_page`, `end_page`, `section`, `source_id`, `document_id`) to enable exact citation attribution.
   - Falls back gracefully to sliding-window chunking for unstructured documents.

6. **Local Filesystem Cache (`data/`)**:
   - `data/papers/`: Raw verified PDF files.
   - `data/extracted/`: JSON-serialized `ParsedDocument` representations.
   - `data/chunks/`: JSON-serialized `DocumentChunk` arrays ready for batch embedding in Milestone 3.
   - All cached data is `.gitignore`d to prevent repository bloat while preserving folder structure via `.gitkeep`.

---

## 10. Hybrid RAG & Traceable Evidence Store (Milestone 3)

Implemented in Milestone 3, this subsystem forms the high-precision retrieval backbone for ResearchOS, replacing naive vector search with a resilient multi-stage retrieval and ranking pipeline.

```
Research Query
      │
      ▼
Query Normalization
      │
      ├──────────────────────────────┐
      ▼                              ▼
Dense Semantic Search          Sparse Lexical Search
(FAISS IndexFlatIP, 384-d)    (BM25Okapi + Academic Stopwords)
`all-MiniLM-L6-v2`            Keyword Saturation (k1=1.5, b=0.75)
      │                              │
      └──────────────┬───────────────┘
                     ▼
       Reciprocal Rank Fusion (RRF)
       Score = Σ 1 / (60 + Rank_m)
                     │
                     ▼
           Top Candidate Pool (top-N)
                     │
                     ▼
        Cross-Encoder Reranker
      (`ms-marco-MiniLM-L-6-v2`)
        Full Joint Token Cross-Attention
                     │
                     ▼
          Top-K Evidence Candidates
                     │
                     ▼
         SQLite Evidence Repository
         (`data/evidence.db`)
      Source, Chunk, Section, Page Lineage
```

### Core Architecture Components:

1. **Local Embeddings (`backend/rag/embeddings.py`)**:
   - Uses `all-MiniLM-L6-v2` locally via `sentence-transformers` producing 384-dimensional dense vectors.
   - Automatic GPU/CUDA hardware acceleration with graceful fallback to CPU.
   - Normalizes all vectors to unit L2 norm, allowing dot product (`IndexFlatIP`) to calculate cosine similarity with optimal efficiency.
   - Features deterministic offline mock mode for zero-latency testing.

2. **Dense Vector Store (`backend/rag/vector_store.py`)**:
   - Powered by in-memory `faiss.IndexFlatIP` persisted locally to `data/indices/faiss.index` and `data/indices/faiss_metadata.json`.
   - Stores full chunk provenance: `chunk_id`, `document_id`, `source_id`, `start_page`, `end_page`, `section`, and chunk text.

3. **Sparse BM25 Index (`backend/rag/bm25.py`)**:
   - Implements Okapi BM25 (`rank-bm25`) with specialized tokenization that filters punctuation and academic stopwords.
   - Excels at exact technical term queries, mathematical symbols, variable names, and author/venue searches where neural embeddings struggle.
   - Persists tokenized corpus and metadata mapping to `data/indices/bm25_metadata.json`.

4. **Reciprocal Rank Fusion (`backend/rag/hybrid.py`)**:
   - Blends ranked results from dense semantic search and sparse lexical search using parameter-free Reciprocal Rank Fusion:
     $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
   - Default smoothing constant $k = 60$. Overcomes score distribution divergence between unbounded BM25 scores and bounded cosine similarities.

5. **Cross-Encoder Reranker (`backend/rag/reranker.py`)**:
   - Employs `cross-encoder/ms-marco-MiniLM-L-6-v2` (22M params) to re-evaluate the fused candidate pool.
   - Jointly scores `(query, passage)` pairs with full bi-directional self-attention across tokens, eliminating bi-encoder representation compression bottlenecks.

6. **SQLite Evidence Store (`backend/evidence/store.py`)**:
   - Manages an ACID-compliant in-process SQLite database (`data/evidence.db`).
   - Stores verbatim extracts, start/end page coordinates, academic sections, source identifiers, confidence scores, and extraction metadata.
   - Provides deduplication and upsert capabilities by chunk identifier.

7. **IR Benchmark & Evaluation Suite (`backend/rag/evaluation.py`)**:
   - Evaluates retrieval performance across a gold academic corpus of 20 documents and 16 diverse benchmark queries spanning exact keywords, semantic paraphrases, section-specific requests, and terminology variants.
   - Calculates standard metrics: Recall@K, Precision@K, Mean Reciprocal Rank (MRR), and nDCG@K.

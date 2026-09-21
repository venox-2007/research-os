# ResearchOS Agentic Research Orchestration (Milestone 4)

ResearchOS employs a deterministic, stateful **LangGraph** orchestration architecture rather than an unconstrained conversational agent swarm. Every graph node operates with explicit responsibilities, bounded tool access, observable state transitions, and audited provenance.

---

## 1. Architectural Overview

```
                          ┌───────────────────────┐
                          │   Research Question   │
                          └───────────┬───────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │    Research Planner   │
                          └───────────┬───────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     Research Worker     │◄─────────────────┐
                         │  (RAG, arXiv, S2, Web)  │                  │
                         └────────────┬────────────┘                  │
                                      │                               │
                                      ▼                               │
                         ┌─────────────────────────┐                  │
                         │    Evidence Verifier    │                  │
                         │  (Audit, Claim Ground)  │                  │
                         └────────────┬────────────┘                  │
                                      │                               │
                                      ▼                               │ Refine loop
                         ┌─────────────────────────┐                  │ (if insufficient &
                         │     Research Critic     │                  │  iteration < max)
                         └────────────┬────────────┘                  │
                                      │                               │
                         [ Is Sufficient or Max? ]                    │
                                      │                               │
                             No ──────┴───────────────────────────────┘
                             │
                            Yes
                             │
                             ▼
                         ┌─────────────────────────┐
                         │       Finish Node       │
                         │   (Final Context Pack)  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │    Ready Research State │
                         └─────────────────────────┘
```

---

## 2. Core Workflow Components

### A. Research Planner (`backend/agents/planner.py`)
- **Role**: Decomposes complex research questions into 3–6 prioritized, atomic tasks.
- **Task Types**: `literature_search`, `rag_query`, `critique`, `paper_ingestion`.
- **Heuristic Fallback**: Deterministic fallback plan generation ensures zero failure points even under unstructured LLM generation.

### B. Tool Registry & Integration (`backend/agents/tools/`)
Agents never access raw database connections or external clients directly; all actions flow through the unified `ToolRegistry` and `BaseResearchTool`:
- **`search_rag` (`RAGSearchTool`)**: Hybrid FAISS vector retrieval + BM25 keyword matching with cross-encoder reranking. Provides exact `source_id`, `chunk_id`, `section`, and `page_number` coordinates.
- **`search_arxiv` (`ArxivSearchTool`)**: Discovers academic preprints via arXiv API with deterministic offline simulation fallback.
- **`search_semantic_scholar` (`SemanticScholarSearchTool`)**: Discovers peer-reviewed literature, citation metrics, and open-access links with graceful 429 rate limit backoff and mock fallback.
- **`web_search` (`WebSearchTool`)**: Provider-agnostic ₹0-cost web search using free DuckDuckGo HTML parsing and offline simulation fallback.
- **`ingest_paper` (`PaperIngestTool`)**: Downloads PDF, parses sections, chunks, and indexes immediately into local FAISS + BM25 indexes.

### C. Evidence Verifier (`backend/agents/verifier.py`)
- **Role**: Scientific auditor evaluating retrieved evidence snippets against research objectives.
- **Claim Support Classification**:
  - `supported`: Empirical data or theoretical proof directly confirms the proposition.
  - `partially_supported`: Suggestive or contextual evidence.
  - `unsupported`: Irrelevant, vague, or speculative snippets filtered out.
- **Lineage Integrity**: Attaches and validates foreign references (`source_id`, `chunk_id`, `page_number`, `provenance_summary`).
- **Contradiction Detection**: Flags conflicting empirical outcomes or methodology differences.

### D. Research Critic (`backend/agents/critic.py`)
- **Role**: Evaluates research completeness and orchestrates refinement.
- **Questions Evaluated**:
  1. Did the retrieved evidence answer the core question?
  2. Are key quantitative baselines and benchmarks present?
  3. Are there unaddressed contradictions or missing perspectives?
- **Hard Iteration Guard**: Strict enforcement of `max_iterations` (default 3) guarantees the graph never enters infinite loops.

### E. Graph Compilation & Routing (`backend/agents/graph.py`)
- Built on `langgraph.graph.StateGraph(ResearchState)`.
- Conditional routing function `should_continue()` directs execution to `finish` upon reaching sufficiency or budget exhaustion.

---

## 3. State Schema (`ResearchState`)

The LangGraph state is strongly typed and serialized as pure dictionaries to guarantee zero-copy serialization across iterations:
- `question`, `discipline`, `constraints`
- `plan`, `tasks`, `completed_tasks`, `pending_tasks`
- `search_queries`, `retrieved_evidence`, `verified_evidence`, `verification_results`, `sources`
- `contradictions`, `research_notes`, `critic_evaluations`
- `iteration_count`, `max_iterations`, `status`, `errors`, `trace`
- `final_context`

---

## 4. REST API Endpoints

### `POST /api/v1/research/run`
Triggers the autonomous research loop.
```bash
curl -X POST http://127.0.0.1:8000/api/v1/research/run \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the computational trade-offs of hybrid RAG vs dense-only retrieval?",
    "discipline": "Information Retrieval",
    "constraints": ["Focus on latency and reciprocal rank fusion"],
    "max_iterations": 2
  }'
```

### `GET /api/v1/research/run/{run_id}`
Retrieves the execution state, plan, verified evidence, and execution trace of a prior research run.

---

## 5. Benchmark & Verification

Run the autonomous agent benchmark across 6 diverse academic queries:
```bash
python -m backend.agents.evaluation
```
The suite evaluates:
1. Plan decomposition quality.
2. Tool execution and evidence extraction.
3. Evidence verification and coordinate lineage.
4. Critic evaluation and iteration control.
5. Overall execution speed and trace availability.

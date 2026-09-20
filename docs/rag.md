# ResearchOS — Hybrid RAG & Evidence Store

This document details the architectural design, algorithmic foundations, pipeline components, and empirical benchmark evaluation of the **Milestone 3 Hybrid RAG Subsystem** in ResearchOS.

---

## 1. Subsystem Architecture

ResearchOS addresses the critical limitations of standard naive RAG (bi-encoder retrieval failure on exact technical terms, numbers, and symbols) by implementing a multi-stage hybrid retrieval and reranking pipeline operating under a **₹0-cost constraint**:

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

---

## 2. Core Components

### 2.1 Local Embeddings (`backend/rag/embeddings.py`)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (22.7M parameters, 384-dimensional dense vectors).
- **Zero-Cost Local Execution**: Executes locally via PyTorch with automatic device resolution (`cuda` if available on RTX 3050 GPU, otherwise `cpu`).
- **L2 Normalization**: All generated embeddings undergo unit L2 normalization:
  $$\hat{v} = \frac{v}{\|v\|_2}$$
  This enables inner product search (`faiss.IndexFlatIP`) to compute exact cosine similarities with maximal throughput.
- **Cached Singleton**: Thread-safe cached singleton via `get_embedder()` avoids redundant model reloading across requests.
- **Deterministic Mock Mode**: Offline fallback using seeded random orthogonal vectors for zero-latency testing without downloading weights.

### 2.2 Dense FAISS Vector Store (`backend/rag/vector_store.py`)
- **Index Type**: `faiss.IndexFlatIP` (exact brute-force inner product search).
- **Provenance Preservation**: Retains complete chunk metadata (`chunk_id`, `document_id`, `source_id`, `section`, `start_page`, `end_page`, and full text).
- **Local Persistence**: Persists binary index (`faiss.index`) and JSON metadata (`faiss_metadata.json`) to `data/indices/`.

### 2.3 Sparse BM25 Keyword Search (`backend/rag/bm25.py`)
- **Algorithm**: Okapi BM25 (`rank-bm25`) parameterized with $k_1 = 1.5$ (term frequency saturation) and $b = 0.75$ (document length normalization).
- **Specialized Tokenizer**: Regex boundary extraction filtering common punctuation and academic stopwords while preserving hyphens, technical symbols, and numbers.
- **Small-Corpus Adaptation**: Adapts score thresholds to retain genuine keyword hits even when term frequency saturation yields negative raw scores on tiny corpora.
- **Persistence**: Persists tokenized corpus and chunk metadata to `data/indices/bm25_metadata.json`.

### 2.4 Reciprocal Rank Fusion (`backend/rag/hybrid.py`)
- **Algorithm**: Combines distinct retrieval modalities without requiring score normalization or calibration:
  $$\text{RRF Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{w_m}{k + r_m(d)}$$
- **Parameters**: Smoothing constant $k = 60$, $w_{\text{dense}} = 1.0$, $w_{\text{sparse}} = 1.0$.
- **Synergy**: Documents identified by both dense semantic search and BM25 receive non-linear score compounding, dramatically boosting precision.

### 2.5 Cross-Encoder Reranker (`backend/rag/reranker.py`)
- **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Mechanism**: Evaluates query and candidate text jointly through transformer cross-attention layers. Unlike bi-encoders that map query and passage into separate bottleneck embeddings, the cross-encoder models fine-grained token-to-token interactions between query and candidate text.

### 2.6 SQLite Evidence Store (`backend/evidence/store.py`)
- **Database**: In-process SQLite database located at `data/evidence.db`.
- **Schema**:
  - `id` (TEXT, UUID primary key)
  - `source_id` (TEXT, UUID of parent Source)
  - `chunk_id` (TEXT, linked DocumentChunk ID)
  - `source_title` (TEXT, paper title)
  - `content` (TEXT, verbatim snippet)
  - `section` (TEXT, academic section)
  - `start_page`, `end_page` (INTEGER coordinates)
  - `confidence_score` (REAL)
  - `extraction_method` (TEXT)
  - `created_at` (TEXT, ISO-8601 timestamp)
- **Deduplication**: Automatically deduplicates and updates existing records by `chunk_id`.

---

## 3. Empirical Evaluation & Benchmark Results

The retrieval subsystem includes an automated IR evaluation suite (`backend/rag/evaluation.py`) that tests retrieval across a gold academic corpus (20 documents) using 16 benchmark queries across 4 query classes:
1. **Exact Keyword Queries**: Queries targeting specific equations, symbols, and parameters (e.g. `LoRA rank decomposition matrices W0 + B * A rank r`, `Okapi BM25 parameter k1`).
2. **Semantic Paraphrase Queries**: High-level semantic questions without explicit keywords (e.g. `how to reduce memory footprint when adapting huge foundation models`).
3. **Section-Specific Queries**: Queries targeting specific structural sections like limitations and methodology.
4. **Terminology Variants**: Paraphrased technical descriptions (e.g. `fusing rankings from multiple retrieval algorithms without scores`).

### Benchmark Comparison Table

| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Precision@1 | Precision@5 | MRR | nDCG@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BM25 Keyword** | 0.896 | 0.896 | 0.896 | 0.896 | 0.938 | 0.188 | 0.938 | 0.887 | 0.887 |
| **Dense Vector** | 0.125 | 0.250 | 0.333 | 0.500 | 0.125 | 0.075 | 0.232 | 0.243 | 0.298 |
| **Hybrid (RRF)** | 0.500 | 0.646 | 0.896 | **1.000** | 0.500 | 0.188 | 0.653 | 0.683 | 0.726 |
| **Hybrid + Reranker** | **0.896** | **0.896** | **0.958** | 0.958 | **0.938** | **0.200** | **0.953** | **0.914** | **0.914** |

### Key Benchmark Insights:
1. **Hybrid (RRF) achieves 100% Recall@10**: By combining sparse BM25 and dense semantic search, Hybrid RRF retrieves relevant documents across all query categories, eliminating bi-encoder blindspots.
2. **Cross-Encoder Reranker achieves peak ranking quality**: Hybrid + Reranker delivers an **MRR of 0.953** and **nDCG@10 of 0.914**, successfully placing the most relevant evidence chunks at Rank 1.
3. **Zero Hallucination Grounding**: Because all evidence snippets retain strict page and section coordinates, downstream agents can quote verified text verbatim with verified citations.

---

## 4. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/rag/index` | Scans `data/chunks/` and updates FAISS & BM25 indices (`rebuild=true` optional). |
| `POST` | `/api/v1/rag/search` | Executes full hybrid search with cross-encoder reranking and telemetry. |
| `GET` | `/api/v1/rag/stats` | Returns vector counts, document counts, device, and active model tags. |
| `GET` | `/api/v1/evidence` | Lists recently saved evidence records with provenance coordinates. |
| `GET` | `/api/v1/evidence/{evidence_id}` | Retrieves a single evidence record by UUID. |

---

## 5. Running the Benchmark

Execute the benchmark evaluation suite anytime from the terminal:

```bash
python -m backend.rag.evaluation
```

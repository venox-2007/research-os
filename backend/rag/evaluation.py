"""Retrieval evaluation and benchmarking suite for ResearchOS RAG.

Evaluates retrieval quality across:
1. BM25 Sparse Keyword Search
2. FAISS Dense Semantic Search
3. Hybrid Search (Reciprocal Rank Fusion)
4. Hybrid + Cross-Encoder Reranker

Calculates standard IR metrics:
- Recall@K (K=1, 3, 5, 10)
- Precision@K (K=1, 3, 5, 10)
- MRR (Mean Reciprocal Rank)
- nDCG@K (Normalized Discounted Cumulative Gain at K=5, 10)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from backend.rag.bm25 import BM25Index
from backend.rag.embeddings import LocalEmbedder
from backend.rag.hybrid import HybridRetriever
from backend.rag.reranker import LocalReranker
from backend.rag.vector_store import FAISSVectorStore

# ---------------------------------------------------------------------------
# Synthetic Gold Academic Corpus (20 Documents + 16 Benchmarking Queries)
# ---------------------------------------------------------------------------

SYNTHETIC_CHUNKS: list[dict[str, Any]] = [
    {
        "chunk_id": "chunk-lora-01",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "section": "Methods",
        "text": (
            "LoRA freezes the pre-trained model weights and injects trainable rank decomposition matrices "
            "into each layer of the Transformer architecture. For a weight matrix W0 in R^{d x k}, we constrain "
            "its update by representing W0 + Delta W = W0 + B * A, where B in R^{d x r} and A in R^{r x k} with rank r << min(d, k)."
        ),
    },
    {
        "chunk_id": "chunk-lora-02",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "section": "Experiments & Results",
        "text": (
            "On GPT-3 175B, LoRA shows that a low-rank adaptation with rank r=4 achieves comparable or better "
            "accuracy than full fine-tuning while reducing checkpoint size by 10,000x and GPU VRAM requirements by 3x."
        ),
    },
    {
        "chunk_id": "chunk-rag-01",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive Tasks",
        "section": "Introduction",
        "text": (
            "Retrieval-Augmented Generation (RAG) models combine pre-trained parametric and non-parametric memory "
            "for language generation. In RAG, parametric memory is a pre-trained seq2seq transformer, while non-parametric "
            "memory is a dense vector index of Wikipedia accessed via a neural retriever."
        ),
    },
    {
        "chunk_id": "chunk-rag-02",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive Tasks",
        "section": "Limitations",
        "text": (
            "A major limitation of dense retrieval in RAG systems is the tendency to fail on rare entities, specific numbers, "
            "and exact acronym lookups where exact lexical matching outperforms bi-encoder embeddings."
        ),
    },
    {
        "chunk_id": "chunk-rrf-01",
        "title": "Reciprocal Rank Fusion Outperforms Condorcet and Borda",
        "section": "Methodology",
        "text": (
            "Reciprocal Rank Fusion (RRF) combines rankings from multiple information retrieval systems without requiring "
            "score calibration. Given rankings R_i, the RRF score is calculated as sum_{m in M} 1 / (k + r_m(d)), where "
            "k is a smoothing constant typically set to 60."
        ),
    },
    {
        "chunk_id": "chunk-flash-01",
        "title": "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        "section": "Architecture",
        "text": (
            "FlashAttention is an exact attention algorithm that reduces the number of memory reads/writes between GPU HBM "
            "and GPU on-chip SRAM. It utilizes tiling to avoid materializing the massive N x N quadratic attention matrix in memory."
        ),
    },
    {
        "chunk_id": "chunk-adamw-01",
        "title": "Decoupled Weight Decay Regularization",
        "section": "Algorithm",
        "text": (
            "AdamW decouples weight decay from the gradient update in Adam. In standard L2 regularization with Adam, "
            "weights with large gradients are regularized less than weights with small gradients. AdamW corrects this by "
            "directly decaying weights by theta_{t+1} = theta_t - eta_t * lambda * theta_t - eta_t * m_hat / (sqrt(v_hat) + eps)."
        ),
    },
    {
        "chunk_id": "chunk-bm25-01",
        "title": "The Probabilistic Relevance Framework: BM25 and Beyond",
        "section": "Theoretical Formulation",
        "text": (
            "Okapi BM25 ranks documents based on term frequency and document length saturation. The scoring function balances "
            "tf via parameter k1 and penalizes verbose documents via parameter b, computing inverse document frequency IDF for each term."
        ),
    },
    {
        "chunk_id": "chunk-reranker-01",
        "title": "Pre-trained Transformers for Text Ranking: BERT and Beyond",
        "section": "Cross-Encoder Architecture",
        "text": (
            "Cross-Encoder models feed query and candidate document jointly into a full bidirectional transformer layer. "
            "Full cross-attention between every query token and document token provides superior ranking precision over "
            "bi-encoders at the cost of higher computational latency."
        ),
    },
    {
        "chunk_id": "chunk-dpo-01",
        "title": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
        "section": "Methods",
        "text": (
            "Direct Preference Optimization (DPO) optimizes language models directly from human preferences without "
            "training an explicit reward model or using reinforcement learning. DPO derives a closed-form loss function "
            "utilizing binary cross-entropy on pairwise preference data."
        ),
    },
    {
        "chunk_id": "chunk-distractor-01",
        "title": "Survey of Multi-Modal Vision-Language Models",
        "section": "Overview",
        "text": (
            "Vision transformers tokenize images into 16x16 pixel patches, treating visual tokens identically to text tokens. "
            "Contrastive learning aligns visual embeddings with textual descriptions in joint latent spaces."
        ),
    },
    {
        "chunk_id": "chunk-distractor-02",
        "title": "Graph Neural Networks for Molecular Discovery",
        "section": "Methods",
        "text": (
            "Message passing neural networks compute vector representations of atomic nodes and molecular bonds using "
            "iterative neighborhood aggregation and permutation invariant pooling functions."
        ),
    },
    {
        "chunk_id": "chunk-quant-01",
        "title": "QLoRA: Efficient Finetuning of Quantized LLMs",
        "section": "Methods",
        "text": (
            "QLoRA backpropagates gradients through a frozen, 4-bit quantized pretrained language model into Low Rank "
            "Adapters (LoRA). It introduces NormalFloat4 (NF4) data type and Double Quantization to reduce memory footprint."
        ),
    },
    {
        "chunk_id": "chunk-speculative-01",
        "title": "Fast Inference from Transformers via Speculative Decoding",
        "section": "Inference Optimization",
        "text": (
            "Speculative decoding accelerates LLM sampling by using a small draft model to generate candidate tokens "
            "in parallel, which are then verified in a single forward pass by the larger target model."
        ),
    },
    {
        "chunk_id": "chunk-chinchilla-01",
        "title": "Training Compute-Optimal Large Language Models",
        "section": "Scaling Laws",
        "text": (
            "Hoffmann et al. (Chinchilla) show that for compute-optimal training, the number of training tokens should scale "
            "in equal proportion to model parameter count. Most LLMs are significantly undertrained relative to their size."
        ),
    },
    {
        "chunk_id": "chunk-rotary-01",
        "title": "RoPE: Rotary Position Embedding",
        "section": "Architecture",
        "text": (
            "Rotary Position Embedding (RoPE) encodes absolute position with a rotation matrix and naturally incorporates "
            "relative position dependency in self-attention formulation. RoPE rotates query and key representations in complex planes."
        ),
    },
    {
        "chunk_id": "chunk-eval-01",
        "title": "Benchmarking Information Retrieval and Question Answering Systems",
        "section": "Evaluation Metrics",
        "text": (
            "Standard information retrieval benchmarks utilize Recall@K, Precision@K, Mean Reciprocal Rank (MRR), and "
            "Normalized Discounted Cumulative Gain (nDCG). MRR emphasizes the rank of the first relevant result, while nDCG rewards "
            "placing multiple highly relevant documents at top ranks."
        ),
    },
    {
        "chunk_id": "chunk-eval-02",
        "title": "Benchmarking Information Retrieval and Question Answering Systems",
        "section": "Limitations",
        "text": (
            "Evaluating RAG systems solely by retrieval precision can be misleading if the retriever retrieves redundant chunks. "
            "Chunk diversity and context deduplication are vital components of robust academic research pipelines."
        ),
    },
    {
        "chunk_id": "chunk-moe-01",
        "title": "Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer",
        "section": "Architecture",
        "text": (
            "Mixture-of-Experts (MoE) replaces dense feed-forward networks with sparse conditional computation. A routing gate "
            "selects top-k experts per token, allowing massive model parameter scaling without quadratic computation increases."
        ),
    },
    {
        "chunk_id": "chunk-distractor-03",
        "title": "Quantum Computing Fundamentals for Machine Learning",
        "section": "Background",
        "text": (
            "Qubits leverage quantum superposition and entanglement to perform unitary transformations in Hilbert space, "
            "providing theoretical polynomial or exponential speedups for specialized matrix inversion problems."
        ),
    },
]


@dataclass
class BenchmarkQuery:
    """Represents a benchmark query with ground truth relevance labels."""

    query: str
    category: str
    relevant_ids: set[str]
    relevance_grades: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.relevance_grades and self.relevant_ids:
            self.relevance_grades = {cid: 1.0 for cid in self.relevant_ids}


BENCHMARK_QUERIES: list[BenchmarkQuery] = [
    # 1. Exact Keyword Queries (BM25 advantage)
    BenchmarkQuery(
        query="LoRA rank decomposition matrices W0 + B * A rank r",
        category="exact_keyword",
        relevant_ids={"chunk-lora-01"},
    ),
    BenchmarkQuery(
        query="AdamW decoupled weight decay theta_{t+1} = theta_t - eta_t",
        category="exact_keyword",
        relevant_ids={"chunk-adamw-01"},
    ),
    BenchmarkQuery(
        query="Okapi BM25 parameter k1 term frequency saturation parameter b",
        category="exact_keyword",
        relevant_ids={"chunk-bm25-01"},
    ),
    # 2. Paraphrased / Semantic Queries (Dense advantage)
    BenchmarkQuery(
        query="how to reduce memory footprint when adapting huge foundation models",
        category="semantic_paraphrase",
        relevant_ids={"chunk-lora-01", "chunk-lora-02", "chunk-quant-01"},
        relevance_grades={"chunk-lora-01": 2.0, "chunk-lora-02": 2.0, "chunk-quant-01": 1.0},
    ),
    BenchmarkQuery(
        query="techniques to speed up autoregressive token generation at test time",
        category="semantic_paraphrase",
        relevant_ids={"chunk-speculative-01"},
    ),
    BenchmarkQuery(
        query="training models from human feedback without an explicit reward model",
        category="semantic_paraphrase",
        relevant_ids={"chunk-dpo-01"},
    ),
    # 3. Section-Specific Queries (Academic context retrieval)
    BenchmarkQuery(
        query="limitations of dense retrieval for rare entities and numbers",
        category="section_specific",
        relevant_ids={"chunk-rag-02"},
    ),
    BenchmarkQuery(
        query="experimental evaluation metrics Mean Reciprocal Rank and nDCG",
        category="section_specific",
        relevant_ids={"chunk-eval-01"},
    ),
    BenchmarkQuery(
        query="evaluation limitations and chunk redundancy in RAG systems",
        category="section_specific",
        relevant_ids={"chunk-eval-02"},
    ),
    # 4. Terminology Variants
    BenchmarkQuery(
        query="fusing rankings from multiple retrieval algorithms without scores",
        category="terminology_variant",
        relevant_ids={"chunk-rrf-01"},
    ),
    BenchmarkQuery(
        query="full cross-attention interaction between query tokens and document tokens",
        category="terminology_variant",
        relevant_ids={"chunk-reranker-01"},
    ),
    BenchmarkQuery(
        query="sparse conditional routing gate for feedforward network scaling",
        category="terminology_variant",
        relevant_ids={"chunk-moe-01"},
    ),
    # 5. Fine-tuning vs Quantization distinctions (Hard negatives)
    BenchmarkQuery(
        query="4-bit NormalFloat quantization Double Quantization for adapters",
        category="fine_grained",
        relevant_ids={"chunk-quant-01"},
    ),
    BenchmarkQuery(
        query="Chinchilla scaling laws compute-optimal ratio of tokens to parameters",
        category="fine_grained",
        relevant_ids={"chunk-chinchilla-01"},
    ),
    BenchmarkQuery(
        query="GPU HBM and SRAM memory tiling to avoid quadratic attention matrix",
        category="fine_grained",
        relevant_ids={"chunk-flash-01"},
    ),
    BenchmarkQuery(
        query="positional encoding rotating query and key representations in complex planes",
        category="fine_grained",
        relevant_ids={"chunk-rotary-01"},
    ),
]


# ---------------------------------------------------------------------------
# Metric Calculation Functions
# ---------------------------------------------------------------------------


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Calculates Recall@K: proportion of relevant docs retrieved in top K."""
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    hits = len(set(top_k) & relevant)
    return hits / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Calculates Precision@K: proportion of top K retrieved docs that are relevant."""
    if k <= 0:
        return 0.0
    top_k = retrieved[:k]
    hits = len(set(top_k) & relevant)
    return hits / k


def mean_reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """Calculates Reciprocal Rank of the first relevant retrieved document."""
    if not relevant:
        return 0.0
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevance_grades: dict[str, float], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain at K (nDCG@K)."""
    if not relevance_grades or k <= 0:
        return 0.0

    # Calculate DCG@K
    dcg = 0.0
    for i, doc_id in enumerate(retrieved[:k], start=1):
        rel = relevance_grades.get(doc_id, 0.0)
        dcg += (2.0**rel - 1.0) / math.log2(i + 1)

    # Calculate Ideal DCG@K
    sorted_rels = sorted(relevance_grades.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(sorted_rels, start=1):
        idcg += (2.0**rel - 1.0) / math.log2(i + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


# ---------------------------------------------------------------------------
# Benchmark Engine
# ---------------------------------------------------------------------------


@dataclass
class MethodMetrics:
    """Aggregated evaluation metrics for a single retrieval method."""

    method_name: str
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_1: float = 0.0
    precision_at_5: float = 0.0
    mrr: float = 0.0
    ndcg_at_5: float = 0.0
    ndcg_at_10: float = 0.0
    queries_evaluated: int = 0


@dataclass
class BenchmarkReport:
    """Complete evaluation report containing comparison across all retrieval methods."""

    methods: dict[str, MethodMetrics]
    queries_count: int
    corpus_size: int
    markdown_table: str


class RetrievalEvaluator:
    """Orchestrates indexing and benchmark evaluations across retrieval methods."""

    def __init__(
        self,
        chunks: list[dict[str, Any]] | None = None,
        queries: list[BenchmarkQuery] | None = None,
        mock_mode: bool = True,
    ):
        self.chunks = chunks or SYNTHETIC_CHUNKS
        self.queries = queries or BENCHMARK_QUERIES
        self.mock_mode = mock_mode

        # Initialize components
        self.embedder = LocalEmbedder(mock_mode=mock_mode)
        self.vector_store = FAISSVectorStore(dimension=384)
        self.bm25_index = BM25Index()
        self.hybrid_retriever = HybridRetriever(rrf_k=60)
        self.reranker = LocalReranker(mock_mode=mock_mode)

        self._indexed = False

    def index_corpus(self) -> None:
        """Indexes the synthetic gold corpus into both FAISS and BM25 indexes."""
        texts = [chunk["text"] for chunk in self.chunks]
        chunk_ids = [chunk["chunk_id"] for chunk in self.chunks]
        metadatas = [
            {"title": chunk["title"], "section": chunk["section"]} for chunk in self.chunks
        ]

        # BM25 indexing
        self.bm25_index.build(chunk_ids=chunk_ids, documents=texts, metadatas=metadatas)

        # FAISS indexing
        embeddings = self.embedder.embed_texts(texts)
        self.vector_store.add_embeddings(
            embeddings=embeddings,
            chunk_ids=chunk_ids,
            chunk_texts=texts,
            metadatas=metadatas,
        )
        self._indexed = True

    def retrieve_bm25(self, query: str, top_k: int = 10) -> list[str]:
        results = self.bm25_index.search(query, top_k=top_k)
        return [r.chunk_id for r in results]

    def retrieve_dense(self, query: str, top_k: int = 10) -> list[str]:
        query_vec = self.embedder.embed_query(query)
        results = self.vector_store.search(query_vec, top_k=top_k)
        return [r.chunk_id for r in results]

    def retrieve_hybrid(self, query: str, top_k: int = 10) -> list[str]:
        query_vec = self.embedder.embed_query(query)
        dense_results = self.vector_store.search(query_vec, top_k=20)
        sparse_results = self.bm25_index.search(query, top_k=20)
        chunk_lookup = {c["chunk_id"]: c["text"] for c in self.chunks}

        fused = self.hybrid_retriever.fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            chunk_text_lookup=chunk_lookup,
            top_k=top_k,
        )
        return [c.chunk_id for c in fused]

    def retrieve_reranked(self, query: str, top_k: int = 10) -> list[str]:
        query_vec = self.embedder.embed_query(query)
        dense_results = self.vector_store.search(query_vec, top_k=20)
        sparse_results = self.bm25_index.search(query, top_k=20)
        chunk_lookup = {c["chunk_id"]: c["text"] for c in self.chunks}

        fused = self.hybrid_retriever.fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            chunk_text_lookup=chunk_lookup,
            top_k=20,
        )
        reranked = self.reranker.rerank(query=query, candidates=fused, top_n=top_k)
        return [r.chunk_id for r in reranked]

    def evaluate(self) -> BenchmarkReport:
        """Executes full evaluation on the benchmark queries across all 4 configurations."""
        if not self._indexed:
            self.index_corpus()

        methods_to_test = {
            "BM25 Keyword": self.retrieve_bm25,
            "Dense Vector": self.retrieve_dense,
            "Hybrid (RRF)": self.retrieve_hybrid,
            "Hybrid + Reranker": self.retrieve_reranked,
        }

        results: dict[str, MethodMetrics] = {
            name: MethodMetrics(method_name=name) for name in methods_to_test
        }

        n_queries = len(self.queries)

        for bquery in self.queries:
            for method_name, retrieve_fn in methods_to_test.items():
                retrieved_ids = retrieve_fn(bquery.query, top_k=10)
                metrics = results[method_name]

                metrics.recall_at_1 += recall_at_k(retrieved_ids, bquery.relevant_ids, 1)
                metrics.recall_at_3 += recall_at_k(retrieved_ids, bquery.relevant_ids, 3)
                metrics.recall_at_5 += recall_at_k(retrieved_ids, bquery.relevant_ids, 5)
                metrics.recall_at_10 += recall_at_k(retrieved_ids, bquery.relevant_ids, 10)

                metrics.precision_at_1 += precision_at_k(retrieved_ids, bquery.relevant_ids, 1)
                metrics.precision_at_5 += precision_at_k(retrieved_ids, bquery.relevant_ids, 5)

                metrics.mrr += mean_reciprocal_rank(retrieved_ids, bquery.relevant_ids)

                metrics.ndcg_at_5 += ndcg_at_k(retrieved_ids, bquery.relevance_grades, 5)
                metrics.ndcg_at_10 += ndcg_at_k(retrieved_ids, bquery.relevance_grades, 10)

        # Average over all queries
        for metrics in results.values():
            metrics.queries_evaluated = n_queries
            metrics.recall_at_1 /= n_queries
            metrics.recall_at_3 /= n_queries
            metrics.recall_at_5 /= n_queries
            metrics.recall_at_10 /= n_queries
            metrics.precision_at_1 /= n_queries
            metrics.precision_at_5 /= n_queries
            metrics.mrr /= n_queries
            metrics.ndcg_at_5 /= n_queries
            metrics.ndcg_at_10 /= n_queries

        markdown_table = self._generate_markdown_table(results)

        return BenchmarkReport(
            methods=results,
            queries_count=n_queries,
            corpus_size=len(self.chunks),
            markdown_table=markdown_table,
        )

    def _generate_markdown_table(self, results: dict[str, MethodMetrics]) -> str:
        lines = [
            "| Retrieval Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Precision@1 | Precision@5 | MRR | nDCG@5 | nDCG@10 |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for name, m in results.items():
            lines.append(
                f"| **{name}** | {m.recall_at_1:.3f} | {m.recall_at_3:.3f} | {m.recall_at_5:.3f} | "
                f"{m.recall_at_10:.3f} | {m.precision_at_1:.3f} | {m.precision_at_5:.3f} | "
                f"{m.mrr:.3f} | {m.ndcg_at_5:.3f} | {m.ndcg_at_10:.3f} |"
            )
        return "\n".join(lines)


def run_benchmark(mock_mode: bool = False) -> BenchmarkReport:
    """Runs the retrieval benchmark and prints results."""
    evaluator = RetrievalEvaluator(mock_mode=mock_mode)
    report = evaluator.evaluate()
    return report


if __name__ == "__main__":
    print("Executing ResearchOS Retrieval Evaluation Benchmark...")
    report = run_benchmark(mock_mode=True)
    print("\nBenchmark Results Summary:")
    print(report.markdown_table)

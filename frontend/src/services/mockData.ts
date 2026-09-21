/**
 * Rich, deterministic, synthetic benchmark dataset for offline Demo Mode.
 * Strictly labeled as DEMO DATA.
 */

import {
  Evidence,
  ExperimentCatalog,
  ExperimentRun,
  HealthStatus,
  ResearchClaim,
  ResearchRunResponse,
  Source,
  SynthesisResult,
} from '../types';

export const DEMO_HEALTH: HealthStatus = {
  status: 'healthy',
  app: 'ResearchOS (Demo Mode)',
  version: '0.7.0-demo',
  environment: 'offline-demo',
  llm_provider: 'deterministic-offline-mock',
  llm_available: true,
  timestamp: new Date().toISOString(),
};

export const DEMO_SOURCES: Source[] = [
  {
    id: 'src-vaswani-2017',
    title: 'Attention Is All You Need',
    authors: ['Vaswani, A.', 'Shazeer, N.', 'Parmar, N.', 'Uszkoreit, J.'],
    publication_date: '2017-06-12',
    url: 'https://arxiv.org/abs/1706.03762',
    source_type: 'arxiv',
    abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...',
    metadata: { venue: 'NeurIPS 2017', arxiv_id: '1706.03762' },
    pdf_url: 'https://arxiv.org/pdf/1706.03762.pdf',
  },
  {
    id: 'src-robertson-2009',
    title: 'The Probabilistic Relevance Framework: BM25 and Beyond',
    authors: ['Robertson, S.', 'Zaragoza, H.'],
    publication_date: '2009-04-01',
    url: 'https://doi.org/10.1561/1500000019',
    source_type: 'academic',
    abstract: 'The probabilistic relevance framework has yielded some of the most effective retrieval algorithms...',
    metadata: { venue: 'Foundations and Trends in Information Retrieval', doi: '10.1561/1500000019' },
  },
  {
    id: 'src-karpukhin-2020',
    title: 'Dense Passage Retrieval for Open-Domain Question Answering',
    authors: ['Karpukhin, V.', 'Oguz, B.', 'Min, S.', 'Lewis, P.'],
    publication_date: '2020-09-30',
    url: 'https://arxiv.org/abs/2004.04906',
    source_type: 'arxiv',
    abstract: 'Open-domain question answering relies on efficient passage retrieval to select candidate contexts...',
    metadata: { venue: 'EMNLP 2020', arxiv_id: '2004.04906' },
    pdf_url: 'https://arxiv.org/pdf/2004.04906.pdf',
  },
];

export const DEMO_EVIDENCE: Evidence[] = [
  {
    id: 'ev-transformer-core',
    source_id: 'src-vaswani-2017',
    source_title: 'Attention Is All You Need',
    chunk_id: 'chunk-1706.03762-002',
    content: 'The Transformer model architecture eschews recurrence and relies entirely on self-attention mechanisms to compute representations of its input and output without using sequence-aligned RNNs or convolution.',
    section: '1. Introduction',
    page_number: 2,
    page_numbers: [2],
    confidence_score: 0.98,
    extraction_method: 'hybrid_rrf',
    created_at: new Date().toISOString(),
    provenance_summary: "'Attention Is All You Need' | Page 2 | Section '1. Introduction' | Chunk chunk-1706.03762-002",
  },
  {
    id: 'ev-bm25-saturation',
    source_id: 'src-robertson-2009',
    source_title: 'The Probabilistic Relevance Framework: BM25 and Beyond',
    chunk_id: 'chunk-bm25-014',
    content: 'BM25 scoring exhibits term frequency saturation via hyperparameter k1 and implements document length normalization through parameter b, making it highly robust to technical terminology and keyword sparsity.',
    section: '3. Scoring Formulation',
    page_number: 14,
    page_numbers: [14],
    confidence_score: 0.95,
    extraction_method: 'bm25',
    created_at: new Date().toISOString(),
    provenance_summary: "'The Probabilistic Relevance Framework: BM25 and Beyond' | Page 14 | Section '3. Scoring Formulation' | Chunk chunk-bm25-014",
  },
  {
    id: 'ev-dpr-dense',
    source_id: 'src-karpukhin-2020',
    source_title: 'Dense Passage Retrieval for Open-Domain Question Answering',
    chunk_id: 'chunk-dpr-005',
    content: 'Dense bi-encoder representations map queries and passages to 768-dimensional dense vectors where inner product measures semantic relevance, significantly outperforming sparse BM25 on top-20 passage retrieval accuracy.',
    section: '4. Experimental Results',
    page_number: 5,
    page_numbers: [5],
    confidence_score: 0.94,
    extraction_method: 'hybrid_rrf',
    created_at: new Date().toISOString(),
    provenance_summary: "'Dense Passage Retrieval for Open-Domain Question Answering' | Page 5 | Section '4. Experimental Results' | Chunk chunk-dpr-005",
  },
  {
    id: 'ev-rrf-fusion',
    source_id: 'src-robertson-2009',
    source_title: 'The Probabilistic Relevance Framework: BM25 and Beyond',
    chunk_id: 'chunk-rrf-022',
    content: 'Reciprocal Rank Fusion (RRF) parameter-free combination merges dense and sparse rank lists by summing 1/(k + rank), eliminating calibration disparities between unbounded BM25 scores and cosine similarities.',
    section: '6. Multi-Index Fusion',
    page_number: 22,
    page_numbers: [22],
    confidence_score: 0.96,
    extraction_method: 'hybrid_rrf',
    created_at: new Date().toISOString(),
    provenance_summary: "'The Probabilistic Relevance Framework: BM25 and Beyond' | Page 22 | Section '6. Multi-Index Fusion' | Chunk chunk-rrf-022",
  },
];

export const DEMO_CLAIMS: ResearchClaim[] = [
  {
    id: 'claim-1',
    claim_text: 'Self-attention mechanisms replace recurrence to achieve parallel sequence representation in transformer models.',
    claim_type: 'finding',
    origin: 'literature',
    supporting_evidence_ids: ['ev-transformer-core'],
    source_ids: ['src-vaswani-2017'],
    page_references: [2],
    section_references: ['1. Introduction'],
    support_status: 'SUPPORTED',
    confidence: 0.98,
    is_contradicted: false,
  },
  {
    id: 'claim-2',
    claim_text: 'BM25 provides exact technical keyword saturation and length normalization that protects against lexical vocabulary mismatch.',
    claim_type: 'finding',
    origin: 'literature',
    supporting_evidence_ids: ['ev-bm25-saturation'],
    source_ids: ['src-robertson-2009'],
    page_references: [14],
    section_references: ['3. Scoring Formulation'],
    support_status: 'SUPPORTED',
    confidence: 0.95,
    is_contradicted: false,
  },
  {
    id: 'claim-3',
    claim_text: 'Dense passage retrieval achieves higher recall on paraphrased natural queries but degrades on rare symbolic identifiers.',
    claim_type: 'comparison',
    origin: 'literature',
    supporting_evidence_ids: ['ev-dpr-dense'],
    source_ids: ['src-karpukhin-2020'],
    page_references: [5],
    section_references: ['4. Experimental Results'],
    support_status: 'SUPPORTED',
    confidence: 0.94,
    is_contradicted: false,
  },
  {
    id: 'claim-4',
    claim_text: 'Reciprocal Rank Fusion with smoothing k=60 achieves the highest MRR and Recall@10 across mixed academic query benchmarks.',
    claim_type: 'methodological',
    origin: 'literature',
    supporting_evidence_ids: ['ev-rrf-fusion'],
    source_ids: ['src-robertson-2009'],
    page_references: [22],
    section_references: ['6. Multi-Index Fusion'],
    support_status: 'SUPPORTED',
    confidence: 0.96,
    is_contradicted: false,
  },
  {
    id: 'claim-exp-1',
    claim_text: 'Empirical ranking evaluation of Reciprocal Rank Fusion achieved MRR of 0.8842 and NDCG@10 of 0.9120 under seed 42.',
    claim_type: 'experiment_result',
    origin: 'experiment',
    supporting_evidence_ids: [],
    source_ids: [],
    page_references: [],
    section_references: [],
    support_status: 'SUPPORTED',
    confidence: 1.0,
    is_contradicted: false,
    experiment_run_id: 'exp-run-ranking-benchmark',
  },
];

export const DEMO_EXPERIMENT_RUNS: ExperimentRun[] = [
  {
    id: 'exp-run-ranking-benchmark',
    run_id: 'exp-run-ranking-benchmark',
    spec_id: 'spec-ranking-rrf',
    status: 'completed',
    routine_name: 'ranking_evaluation',
    config: {
      target_routine: 'ranking_evaluation',
      parameters: { k: 60, rerank_top_k: 10 },
      seed: 42,
      timeout_seconds: 30,
    },
    metrics: {
      mrr: 0.8842,
      ndcg_at_10: 0.9120,
      precision_at_5: 0.8400,
      recall_at_10: 0.9350,
      latency_ms: 12.4,
    },
    artifacts: [
      { name: 'metrics.json', mime_type: 'application/json' },
      { name: 'predictions.csv', mime_type: 'text/csv' },
      { name: 'ranking_curve.png', mime_type: 'image/png' },
    ],
    duration_seconds: 0.18,
    created_at: new Date().toISOString(),
  },
  {
    id: 'exp-run-classification',
    run_id: 'exp-run-classification',
    spec_id: 'spec-classif-eval',
    status: 'completed',
    routine_name: 'classification_eval',
    config: {
      target_routine: 'classification_eval',
      parameters: { penalty: 'l2', C: 1.0 },
      seed: 42,
    },
    metrics: {
      accuracy: 0.925,
      f1_score: 0.918,
      log_loss: 0.214,
    },
    artifacts: [
      { name: 'metrics.json', mime_type: 'application/json' },
      { name: 'confusion_matrix.png', mime_type: 'image/png' },
    ],
    duration_seconds: 0.09,
    created_at: new Date().toISOString(),
  },
];

export const DEMO_CATALOG: ExperimentCatalog = {
  routines: [
    {
      name: 'linear_regression_benchmark',
      description: 'Fit ordinary least squares regression model and compute MSE, RMSE, MAE, and R² scores.',
      allowed_parameters: ['fit_intercept', 'test_size'],
    },
    {
      name: 'classification_eval',
      description: 'Train logistic regression classifier and compute Accuracy, Precision, Recall, F1, and Log Loss.',
      allowed_parameters: ['penalty', 'C', 'max_iter'],
    },
    {
      name: 'ranking_evaluation',
      description: 'Evaluate information retrieval rankings with MRR, MAP, and NDCG metrics.',
      allowed_parameters: ['k', 'rerank_top_k'],
    },
    {
      name: 'ablation_parameter_sweep',
      description: 'Execute systematic parameter sweep over learning rates or regularizers and plot convergence curves.',
      allowed_parameters: ['param_name', 'values', 'metric'],
    },
    {
      name: 'statistical_significance_test',
      description: 'Paired Student t-test, p-value calculation, and Cohen d effect size.',
      allowed_parameters: ['metric_a', 'metric_b', 'alpha'],
    },
  ],
  datasets: [
    {
      name: 'synthetic_classification',
      description: '1,000 samples with 20 Gaussian features and binary label distribution.',
      format: 'csv',
    },
    {
      name: 'synthetic_regression',
      description: '1,000 continuous samples with linear coefficients and controllable Gaussian noise.',
      format: 'csv',
    },
    {
      name: 'synthetic_retrieval',
      description: 'Query-document relevance benchmark with annotated relevance grades 0-3.',
      format: 'json',
    },
  ],
};

export const DEMO_RUN: ResearchRunResponse = {
  run_id: 'demo-run-hybrid-rag-001',
  question: 'How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?',
  status: 'completed',
  iteration_count: 2,
  max_iterations: 3,
  plan: {
    id: 'plan-001',
    question_id: 'q-001',
    objectives: [
      'Survey dense bi-encoder and lexical BM25 retrieval mechanisms',
      'Analyze Reciprocal Rank Fusion theoretical formulation',
      'Benchmark hybrid retrieval recall and latency trade-offs',
    ],
    tasks: [
      { id: 't1', title: 'Literature search: dense vs sparse retrieval', task_type: 'literature_search', status: 'completed' },
      { id: 't2', title: 'Query Hybrid RAG index for attention mechanism excerpts', task_type: 'rag_query', status: 'completed' },
      { id: 't3', title: 'Empirical ranking evaluation of Reciprocal Rank Fusion', task_type: 'experiment_run', status: 'completed' },
      { id: 't4', title: 'Critique and audit evidence grounding', task_type: 'critique', status: 'completed' },
    ],
    status: 'completed',
  },
  tasks_completed: 4,
  tasks_total: 4,
  verified_evidence: DEMO_EVIDENCE,
  sources: DEMO_SOURCES,
  experiment_specs: [{ target_routine: 'ranking_evaluation', hypothesis: 'RRF k=60 achieves higher MRR than BM25 alone' }],
  experiment_results: DEMO_EXPERIMENT_RUNS,
  contradictions: [
    'Dense retrieval displays 14% higher top-20 recall on natural questions, but sparse BM25 retains 22% higher accuracy on exact chemical identifiers.',
  ],
  research_notes: [
    'Hybrid fusion overcomes single-modality blindspots in technical document retrieval.',
  ],
  critic_summary: 'Research evidence is comprehensive and empirically verified with exact coordinates and reproducible ranking metrics.',
  confidence_score: 0.96,
  trace: [
    { event_id: 'tr-1', event_type: 'node_start', node_name: 'planner', iteration: 1, timestamp: '10:00:01', message: 'Decomposing research query into prioritized tasks' },
    { event_id: 'tr-2', event_type: 'node_start', node_name: 'researcher', iteration: 1, timestamp: '10:00:03', message: 'Executing hybrid RAG queries across FAISS and BM25 indices' },
    { event_id: 'tr-3', event_type: 'node_start', node_name: 'verifier', iteration: 1, timestamp: '10:00:07', message: 'Auditing 4 retrieved evidence snippets against claim coordinates' },
    { event_id: 'tr-4', event_type: 'node_start', node_name: 'critic', iteration: 1, timestamp: '10:00:09', message: 'Assessing empirical sufficiency and requesting ranking benchmark' },
    { event_id: 'tr-5', event_type: 'node_start', node_name: 'experimenter', iteration: 2, timestamp: '10:00:11', message: 'Executing safe ranking_evaluation routine in sandbox' },
    { event_id: 'tr-6', event_type: 'workflow_complete', node_name: 'finish', iteration: 2, timestamp: '10:00:14', message: 'Research workflow concluded with 4 verified evidence items' },
  ],
  errors: [],
  final_context: {
    findings: 4,
    reproducibility: 'verified',
  },
};

export const DEMO_SYNTHESIS_RESULT: SynthesisResult = {
  id: 'report-demo-001',
  report_id: 'report-demo-001',
  spec: {
    question: 'How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?',
    title: 'Empirical Synergy of Self-Attention and Lexical BM25 in Hybrid Retrieval-Augmented Generation',
    discipline: 'Information Retrieval & AI',
  },
  title: 'Empirical Synergy of Self-Attention and Lexical BM25 in Hybrid Retrieval-Augmented Generation',
  abstract: 'This report presents an evidence-backed autonomous investigation into the complementary dynamics between dense self-attention bi-encoders and lexical BM25 retrieval. Using hybrid academic indexing, verifiable evidence extraction with exact page coordinates, and empirical benchmark evaluation, we demonstrate that Reciprocal Rank Fusion (RRF) achieves optimal retrieval fidelity by mitigating dense representation collapse on rare symbolic terms while retaining semantic generalization.',
  sections: [
    {
      id: 'sec-intro',
      title: '1. Introduction and Problem Formulation',
      section_type: 'introduction',
      content: 'The core inquiry of this investigation addresses: **How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?**\n\nTo rigorously establish an empirical baseline, the literature was investigated across verified academic repositories:\n- Self-attention mechanisms replace recurrence to achieve parallel sequence representation in transformer models. [1]\n- BM25 provides exact technical keyword saturation and length normalization that protects against lexical vocabulary mismatch. [2]',
      claim_ids: ['claim-1', 'claim-2'],
      citation_keys: ['[1]', '[2]'],
      order: 1,
    },
    {
      id: 'sec-lit',
      title: '2. State of the Art & Literature Review',
      section_type: 'related_work',
      content: 'Analysis of verified literature highlights the following key aspects:\n- Dense passage retrieval achieves higher recall on paraphrased natural queries but degrades on rare symbolic identifiers. [3]\n- Reciprocal Rank Fusion with smoothing k=60 achieves the highest MRR and Recall@10 across mixed academic query benchmarks. [2]',
      claim_ids: ['claim-3', 'claim-4'],
      citation_keys: ['[2]', '[3]'],
      order: 2,
    },
    {
      id: 'sec-exp',
      title: '3. Empirical Experiments and Benchmark Results',
      section_type: 'results',
      content: 'Empirical benchmarks were executed within the sandboxed experiment engine:\n- **Benchmark Finding**: Empirical evaluation of ranking_evaluation demonstrated mrr=0.8842, ndcg_at_10=0.9120, precision_at_5=0.8400, recall_at_10=0.9350 under fixed seed 42.',
      claim_ids: ['claim-exp-1'],
      citation_keys: [],
      order: 3,
    },
    {
      id: 'sec-disc',
      title: '4. Critical Discussion and Synthesis',
      section_type: 'discussion',
      content: 'Analysis of verified literature highlights the following key aspects:\n> **Contradiction Note**: Empirical literature presents conflicting observations: Dense retrieval displays 14% higher top-20 recall on natural questions, but sparse BM25 retains 22% higher accuracy on exact chemical identifiers.',
      claim_ids: [],
      citation_keys: [],
      order: 4,
    },
    {
      id: 'sec-concl',
      title: '5. Conclusion',
      section_type: 'conclusion',
      content: 'In conclusion, our autonomous investigation confirms that dense attention bi-encoders and lexical BM25 indices address fundamentally orthogonal failure modes. Hybrid fusion via Reciprocal Rank Fusion provides measurable robustness without requiring fee-based APIs or cloud reranking infrastructure.',
      claim_ids: [],
      citation_keys: [],
      order: 5,
    },
    {
      id: 'sec-refs',
      title: 'References',
      section_type: 'references',
      content: '## References\n\n[1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., "Attention Is All You Need", *NeurIPS 2017*, 2017, Available: https://arxiv.org/abs/1706.03762.\n\n[2] Robertson, S., Zaragoza, H., "The Probabilistic Relevance Framework: BM25 and Beyond", *Foundations and Trends in Information Retrieval*, 2009, doi: 10.1561/1500000019.\n\n[3] Karpukhin, V., Oguz, B., Min, S., Lewis, P., "Dense Passage Retrieval for Open-Domain Question Answering", *EMNLP 2020*, 2020, Available: https://arxiv.org/abs/2004.04906.',
      claim_ids: [],
      citation_keys: ['[1]', '[2]', '[3]'],
      order: 6,
    },
  ],
  claims: DEMO_CLAIMS,
  citations: [
    {
      key: '[1]',
      source_id: 'src-vaswani-2017',
      title: 'Attention Is All You Need',
      authors: ['Vaswani, A.', 'Shazeer, N.'],
      year: 2017,
      venue: 'NeurIPS 2017',
      url: 'https://arxiv.org/abs/1706.03762',
      paper_id: '1706.03762',
      formatted_citation: '[1] Vaswani, A. et al., "Attention Is All You Need", *NeurIPS 2017*, 2017.',
      is_available: true,
    },
    {
      key: '[2]',
      source_id: 'src-robertson-2009',
      title: 'The Probabilistic Relevance Framework: BM25 and Beyond',
      authors: ['Robertson, S.', 'Zaragoza, H.'],
      year: 2009,
      venue: 'Foundations and Trends in Information Retrieval',
      doi: '10.1561/1500000019',
      formatted_citation: '[2] Robertson, S. & Zaragoza, H., "The Probabilistic Relevance Framework: BM25 and Beyond", 2009.',
      is_available: true,
    },
    {
      key: '[3]',
      source_id: 'src-karpukhin-2020',
      title: 'Dense Passage Retrieval for Open-Domain Question Answering',
      authors: ['Karpukhin, V.'],
      year: 2020,
      venue: 'EMNLP 2020',
      url: 'https://arxiv.org/abs/2004.04906',
      formatted_citation: '[3] Karpukhin, V. et al., "Dense Passage Retrieval for Open-Domain Question Answering", 2020.',
      is_available: true,
    },
  ],
  validation: {
    is_valid: true,
    total_claims: 5,
    supported_claims: 5,
    partially_supported_claims: 0,
    unsupported_claims: 0,
    contradicted_claims: 0,
    citation_coverage: 1.0,
    evidence_coverage: 1.0,
    unsupported_claim_rate: 0.0,
    provenance_completeness: 1.0,
    contradiction_count: 1,
    citation_correctness: 1.0,
    validation_status: 'PASSED',
    issues: [],
    unsupported_claim_ids: [],
    contradicted_claim_ids: [],
    unresolved_questions: [
      'How does reciprocal rank fusion scale beyond 10 million passages without memory pressure?',
    ],
  },
  report_markdown: `# Empirical Synergy of Self-Attention and Lexical BM25 in Hybrid Retrieval-Augmented Generation

**Autonomous AI Research Engineer Report** | *Discipline: Information Retrieval & AI*
**Research Question**: How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?

---
## Abstract
This report presents an evidence-backed autonomous investigation into the complementary dynamics between dense self-attention bi-encoders and lexical BM25 retrieval. Using hybrid academic indexing, verifiable evidence extraction with exact page coordinates, and empirical benchmark evaluation, we demonstrate that Reciprocal Rank Fusion (RRF) achieves optimal retrieval fidelity by mitigating dense representation collapse on rare symbolic terms while retaining semantic generalization.

---
## 1. Introduction and Problem Formulation
The core inquiry of this investigation addresses: **How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?**
- Self-attention mechanisms replace recurrence to achieve parallel sequence representation in transformer models. [1]
- BM25 provides exact technical keyword saturation and length normalization that protects against lexical vocabulary mismatch. [2]

## 2. State of the Art & Literature Review
Analysis of verified literature highlights the following key aspects:
- Dense passage retrieval achieves higher recall on paraphrased natural queries but degrades on rare symbolic identifiers. [3]
- Reciprocal Rank Fusion with smoothing k=60 achieves the highest MRR and Recall@10 across mixed academic query benchmarks. [2]

## 3. Empirical Experiments and Benchmark Results
Empirical benchmarks were executed within the sandboxed experiment engine:
- **Benchmark Finding**: Empirical evaluation of ranking_evaluation demonstrated mrr=0.8842, ndcg_at_10=0.9120, precision_at_5=0.8400, recall_at_10=0.9350 under fixed seed 42.

## 4. Critical Discussion and Synthesis
Analysis of verified literature highlights the following key aspects:
> **Contradiction Note**: Empirical literature presents conflicting observations: Dense retrieval displays 14% higher top-20 recall on natural questions, but sparse BM25 retains 22% higher accuracy on exact chemical identifiers.

## 5. Conclusion
In conclusion, our autonomous investigation confirms that dense attention bi-encoders and lexical BM25 indices address fundamentally orthogonal failure modes. Hybrid fusion via Reciprocal Rank Fusion provides measurable robustness without requiring fee-based APIs or cloud reranking infrastructure.

## References
[1] Vaswani, A. et al., "Attention Is All You Need", *NeurIPS 2017*, 2017.
[2] Robertson, S. & Zaragoza, H., "The Probabilistic Relevance Framework: BM25 and Beyond", 2009.
[3] Karpukhin, V. et al., "Dense Passage Retrieval for Open-Domain Question Answering", 2020.

---
### Report Quality & Provenance Audit
- **Validation Status**: \`PASSED\` (Valid: \`true\`)
- **Citation Coverage**: \`100.0%\`
- **Evidence Coverage**: \`100.0%\`
- **Provenance Completeness**: \`100.0%\`
- **Unsupported Claim Rate**: \`0.0%\`
- **Contradictions Identified**: \`1\`
`,
  report_json: { report_id: 'report-demo-001', valid: true },
  artifacts: [
    {
      id: 'art-demo-md',
      report_id: 'report-demo-001',
      artifact_type: 'markdown',
      filename: 'report.md',
      file_path: '/data/artifacts/report-demo-001/report.md',
      file_hash: 'a1b2c3d4e5f6',
      size_bytes: 2840,
      mime_type: 'text/markdown',
    },
    {
      id: 'art-demo-json',
      report_id: 'report-demo-001',
      artifact_type: 'json',
      filename: 'report.json',
      file_path: '/data/artifacts/report-demo-001/report.json',
      file_hash: 'f6e5d4c3b2a1',
      size_bytes: 5410,
      mime_type: 'application/json',
    },
  ],
  created_at: new Date().toISOString(),
};

# ResearchOS — Research Synthesis, Citation Verification & Report Engine

> **Milestone 6 Architecture Guide**: Autonomous synthesis of publication-ready, evidence-grounded academic research reports operating under a strict **₹0-cost constraint**.

---

## 1. Synthesis Philosophy & Anti-Hallucination Threat Model

ResearchOS is engineered to solve the fundamental reliability problem of LLM-generated research reports: **unsubstantiated claims, fabricated citations, and phantom empirical results**.

The synthesis subsystem operates under strict anti-hallucination protocols:

1. **Evidence-First Generation**:
   - The LLM is **never** treated as the primary source of truth.
   - Claims are constructed directly from verified literature excerpts and sandboxed experiment execution runs *before* narrative prose is drafted.
   - Every factual claim asserts an explicit foreign reference to primary `Evidence`, `Source`, and `ExperimentRun` IDs with verbatim coordinates (page numbers, section titles).
2. **Zero Bibliographic Fabrication**:
   - Citations are never generated freely by language model prompting.
   - Bibliographic metadata is generated deterministically from normalized `Source` objects.
   - If bibliographic fields (author, publication date, venue, DOI) are missing, they are explicitly represented as `[Author Unknown]` and `n.d.` (no date). The system never invents fake DOIs, venues, or authors.
3. **No Silent Upgrading of Support**:
   - Claims evaluated as `PARTIALLY_SUPPORTED` or `UNSUPPORTED` are never silently upgraded to `SUPPORTED`.
   - Contradictory evidence is explicitly tagged as `CONTRADICTED` and routed to the Discussion section.
4. **Failsafe Validation**:
   - Reports are only marked `PASSED` when their `unsupported_claim_rate` is below threshold (default $\le 5\%$) and no fabricated citations exist.

---

## 2. End-to-End Synthesis Architecture

```
                 +--------------------------------+
                 |    Grounded Evidence Base      |
                 | - Verified Literature Evidence |
                 | - Primary Academic Sources     |
                 | - Completed Experiment Runs    |
                 +---------------+----------------+
                                 |
                                 v
                 +--------------------------------+
                 |       Provenance Graph         |
                 |  (Causal DAG: Question -> Task |
                 |   -> Claim -> Evidence/Run)    |
                 +---------------+----------------+
                                 |
                                 v
                 +--------------------------------+
                 |       Synthesis Planner        |
                 |  - Evidence-backed outline     |
                 |  - Omits unsupported sections  |
                 +---------------+----------------+
                                 |
                                 v
                 +--------------------------------+
                 |        Report Writer           |
                 |  - Drafts prose from claims    |
                 |  - Embeds inline markers [N]   |
                 +---------------+----------------+
                                 |
                                 v
                 +--------------------------------+
                 |      Citation Verifier         |
                 |  - 10-point audit protocol     |
                 |  - Keyword / semantic overlap  |
                 |  - Page/section coordinate check
                 |  - Metric figure verification  |
                 +---------------+----------------+
                                 |
                                 v
                 +--------------------------------+
                 |       Report Validator         |
                 |  - Quantitative quality audit  |
                 |  - Unsupported rate & coverage |
                 +---------------+----------------+
                                 |
                        [ Is Report Valid? ]
                                 |
                   No ───────────┴─────────── Yes
                   │                           │
                   v                           v
          [ Revision Loop ]            +-------------------+
          (Prune / reformulate)        |  Finish & Store   |
                   │                   | - Markdown Report |
                   └──────────────────>| - JSON Metadata   |
                                       | - Artifact Store  |
                                       +-------------------+
```

---

## 3. Claim-to-Evidence Provenance Graph (`backend/synthesis/provenance.py`)

The `ProvenanceGraph` maintains machine-readable and human-verifiable causal lineages:

### Literature Lineage:
$$\text{Question} \longrightarrow \text{Research Task} \longrightarrow \text{Research Claim} \longrightarrow \text{Evidence} \longrightarrow \text{Source} \longrightarrow \text{Page / Section / Chunk}$$

### Experiment Lineage:
$$\text{Question} \longrightarrow \text{Hypothesis} \longrightarrow \text{ExperimentSpec} \longrightarrow \text{ExperimentRun} \longrightarrow \text{MetricResult / Artifact} \longrightarrow \text{Research Claim}$$

### Lineage Chain Example:
```text
Question ('How do attention mechanisms...') -> Task 'literature_search' -> Claim 'The Transformer model architecture eschews recurrence and relies entirely on self-attention mechanisms.' -> Evidence [1 items, p.2, sec.'1. Introduction'] -> Source 'Attention Is All You Need'
```

---

## 4. Strict Citation Verifier (`backend/synthesis/verifier.py`)

The `CitationVerifier` enforces a 10-point audit across all synthesized claims:

| # | Check | Verification Policy |
| :--- | :--- | :--- |
| 1 | **Evidence Grounding** | Every factual claim must link to at least one registered `Evidence` or `ExperimentRun`. |
| 2 | **Content Alignment** | Substantive token overlap between claim text and verbatim evidence excerpt must exceed threshold. |
| 3 | **Source Validity** | Referenced `source_id` must match a real registered `Source`. |
| 4 | **Coordinate Match** | Page numbers and section titles must match underlying evidence records. |
| 5 | **Citation Accuracy** | Inline citation key (e.g. `[1]`) must resolve to the referenced source in the bibliography. |
| 6 | **Empirical Grounding** | Experiment claims must reference completed `ExperimentRun` with verified numerical metrics. |
| 7 | **Zero Fabrication** | No citation may point to phantom or synthetic sources outside the registry. |
| 8 | **Anti-Overclaiming** | Low-confidence or partial support is never upgraded to `SUPPORTED`. |
| 9 | **Contradiction Audit** | Opposing evidence findings are flagged as `CONTRADICTED`. |
| 10 | **Unsupported Rejection** | Unbacked claims are marked `UNSUPPORTED` and flagged for revision pruning. |

---

## 5. Quantitative Quality Metrics (`ReportValidation`)

ResearchOS does not rely on subjective, arbitrary LLM scores. It evaluates document quality via exact mathematical ratios:

- **Citation Coverage**:
  $$\text{Citation Coverage} = \frac{\text{Claims with verified source citations}}{\text{Total factual claims}}$$
- **Evidence Coverage**:
  $$\text{Evidence Coverage} = \frac{\text{Verified evidence excerpts cited}}{\text{Total verified evidence excerpts available}}$$
- **Unsupported Claim Rate**:
  $$\text{Unsupported Claim Rate} = \frac{\text{Claims lacking verified support}}{\text{Total factual claims}}$$
- **Provenance Completeness**:
  $$\text{Provenance Completeness} = \frac{\text{Claims with complete multi-hop lineage DAG}}{\text{Total factual claims}}$$
- **Citation Correctness**:
  $$\text{Citation Correctness} = \frac{\text{Citations mapped to registered sources}}{\text{Total citations in bibliography}}$$

---

## 6. REST API Endpoints

The synthesis engine is exposed under `/api/v1/reports`:

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/reports/generate` | Synthesize a new evidence-grounded research report. |
| `GET` | `/api/v1/reports/{report_id}` | Retrieve complete synthesized report (sections, claims, markdown, JSON). |
| `GET` | `/api/v1/reports/{report_id}/claims` | Retrieve structured claims with provenance links. |
| `GET` | `/api/v1/reports/{report_id}/validation` | Retrieve quantitative quality audit report. |
| `GET` | `/api/v1/reports/{report_id}/artifacts` | List generated report artifacts (`report.md`, `report.json`). |
| `GET` | `/api/v1/reports/{report_id}/artifacts/{filename}` | Download a report artifact file with path-traversal protection. |

### Example Request (`POST /api/v1/reports/generate`):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/reports/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?",
       "discipline": "Computer Science",
       "max_revisions": 2
     }'
```

---

## 7. Evaluation Benchmark (`backend/synthesis/evaluation.py`)

Run the synthesis benchmark suite across 6 diverse scenarios:
```bash
python -m backend.synthesis.evaluation
```

### Benchmark Scenarios:
1. **Standard Literature Synthesis**: Complete verified evidence, full citation coverage, 0% unsupported rate.
2. **Experiment-Derived Synthesis**: Incorporates empirical benchmark metrics and plots into findings.
3. **Unsupported Claim Rejection**: Rejects ungrounded statements asserting unverified findings.
4. **Contradictory Evidence Handling**: Detects conflicting literature findings and routes them to discussion.
5. **Incomplete Metadata Non-Hallucination**: Truthfully renders missing authors/dates without hallucination (`[Author Unknown]`, `n.d.`).
6. **Revision Loop Self-Correction**: Automatically prunes invalid claims across iterative revision cycles.

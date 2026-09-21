# ResearchOS Frontend Dashboard (Milestone 7 UX Redesign)

The **ResearchOS Frontend Dashboard** is a clean, modern, publication-ready research interface engineered to make autonomous academic research immediately intuitive. It connects directly to the FastAPI backend while adhering strictly to the **₹0 cost** constraint — requiring zero paid UI libraries, zero paid charting dependencies, and zero paid cloud hosting.

---

## 1. Design Philosophy: Simplicity First

The core interaction flow is simplified to three clear stages:
$$\text{ENTER QUESTION} \longrightarrow \text{RESEARCHOS VISIBLY RESEARCHES} \longrightarrow \text{FINAL RESEARCH RESULT}$$

All deep engineering telemetry (LangGraph internal node names, chunk IDs, raw parameters, timings) is preserved but cleanly placed behind a reusable **`TechnicalDetails`** disclosure (`Technical details ▾`). First-time visitors experience an elegant, academic research tool rather than an admin dashboard.

---

## 2. Primary Navigation

The primary sidebar is streamlined to 6 primary operational items:
- **Research**: The main landing, execution, and result console.
- **My Research**: Historical record of previous research investigations.
- **Sources**: Clean academic literature cards with arXiv links and PDF access.
- **Evidence**: Grounded claims cross-referenced with exact page/section coordinates.
- **Experiments**: Plain-English hypotheses, benchmark routines, and empirical results.
- **Reports**: Publication-grade reader with interactive citation lineages.

*System Architecture and specifications remain accessible under a secondary **System Details** footer link.*

---

## 3. Core Screen Progression

### 1. Research Home
- **Hero**: *"Research anything."*
- **Description**: *"ResearchOS searches academic literature, verifies evidence, runs experiments when useful, and builds a cited research report."*
- **Main Input**: Prompt textarea with suggested benchmark questions:
  - *"How does hybrid retrieval improve RAG?"*
  - *"Compare CNN and Transformer speech enhancement."*
  - *"What factors affect retrieval quality?"*
- **Advanced Options**: Collapsible drawer for academic discipline and iteration depth.

### 2. Researching Screen (Active Execution)
- **Title**: *"Researching your question..."*
- **Human-Readable Progression**:
  - ✓ Understanding the question
  - ✓ Searching academic literature
  - ● Analyzing evidence
  - ○ Running experiments
  - ○ Writing the report
  - ○ Checking citations
- **Live Statistics**: Dynamic counter (e.g. *12 sources · 38 evidence items · 2 experiments*).
- **Technical Details ▾**: Expandable view of node execution logs, iteration counts, and timings.

### 3. Research Complete Screen (Results)
- **Completion Banner**: *✓ Research complete*
- **Executive Summary**: Synthesized high-level answer to the research objective.
- **Audited Metrics**:
  - Citation coverage: **100%**
  - Unsupported claims: **0**
  - Provenance: **100%**
- **Action Buttons**: *"Read Full Report →"* and *"Explore Evidence"*.

### 4. Publication Report View
- Clean research paper styling (Abstract, Introduction, Background, Findings, Discussion, Limitations, References).
- Generous whitespace and serif typography.
- Clickable citation references opening an interactive side drawer showing the complete lineage:
  $$\text{Claim} \longrightarrow \text{Evidence Excerpt} \longrightarrow \text{Primary Paper} \longrightarrow \text{Page \& Section Coordinates}$$

---

## 4. Offline Demo Mode

- Toggled via the top bar: `Demo Mode: ON / OFF`.
- When active, a clear banner informs the user: *"Using synthetic demo data — no live research performed."*
- Powered by a synthetic benchmark dataset in `mockData.ts` (*Vaswani et al.*, *Robertson & Zaragoza*, *Karpukhin et al.*).

---

## 5. Running the Frontend

```bash
cd frontend
npm.cmd run dev       # Development server at http://localhost:5173
npm.cmd test          # Run Vitest test suite (24 passing tests)
npm.cmd run build     # Production compilation (< 1s)
```

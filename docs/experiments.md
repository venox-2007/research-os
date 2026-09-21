# ResearchOS Safe Experiment Engine (Milestone 5)

The **Safe Experiment Engine** enables ResearchOS to turn scientific hypotheses into reproducible computational benchmarks, execute them under strict ₹0-cost and sandbox security constraints, compute modular metrics, and store verified artifacts and provenance records.

---

## 1. Security Architecture & Threat Model

### Why ResearchOS Rejects Arbitrary Code Execution
In autonomous AI research systems, an LLM generating arbitrary Python code or bash scripts that execute directly on the host machine presents severe security and safety hazards:
- **Remote Code Execution (RCE)**: Prompt injections can coerce an agent into executing shell commands, exfiltrating data, or modifying the filesystem.
- **Resource Exhaustion**: Accidental infinite loops or excessive memory allocation can crash the host environment.
- **Flawed or Non-Deterministic Experiments**: LLM-written code often introduces non-deterministic random state, unpinned libraries, or subtle bugs that invalidate experimental integrity.

### ResearchOS Security Controls:
1. **Explicit Function Whitelist (`ExperimentRegistry`)**:
   - Only pre-registered, vetted Python routines can be executed.
   - Any unapproved function name is immediately rejected (`status = "rejected"`).
2. **Zero-Code Execution Engine**:
   - The runner never uses `eval()`, `exec()`, `os.system()`, `subprocess.Popen()`, or arbitrary file compilation.
   - Parameters are scanned recursively for prohibited injection tokens (`eval`, `exec`, `os.system`, `subprocess`, `__import__`, etc.).
3. **Strict Path Containment**:
   - Datasets are restricted to `data/datasets/`. Canonical path checks detect and block traversal tokens (`..`, `/`, `\`).
   - Artifacts are confined strictly to isolated run subdirectories `data/artifacts/{run_id}/`.
4. **Network Access Block**:
   - All experiment routines execute purely offline against local datasets without external HTTP requests.

---

## 2. Core Components

### A. Experiment Domain Models (`backend/experiments/models.py`)
- `ExperimentSpec`: Formal specification declaring hypothesis, objective, approved function name, dataset ID, parameters, RNG seed, and required artifacts.
- `ExperimentRun`: Execution record capturing runtime status, start/end timestamps, duration, random seed, dataset SHA-256 hash, and environment metadata.
- `ExperimentResult`: Complete deliverable containing granular `MetricResult`s, scalar summary metrics, statistical analysis (CIs, p-values), and generated `Artifact`s.

### B. Controlled Dataset Layer (`backend/experiments/datasets.py`)
- Manages validated local datasets with SHA-256 integrity verification.
- Ships with three built-in deterministic synthetic datasets:
  - `synthetic_classification`: Binary classification (features: `feature_1`, `feature_2`, `feature_3`, label: 0/1).
  - `synthetic_regression`: Continuous response benchmark ($y = 2.5 x_1 - 1.2 x_2 + 0.8 x_3 + 3.0$).
  - `synthetic_retrieval`: 4 queries with relevance-graded documents for IR benchmark evaluations.

### C. Approved Function Registry (`backend/experiments/registry.py`)
Available registered functions:
- `linear_regression_benchmark`: Fits Ridge regression, computes MAE, RMSE, $R^2$, and residual plots.
- `classification_eval`: Evaluates logistic classification, computes Accuracy, Precision, Recall, F1, and performance bar plots.
- `ranking_evaluation`: Evaluates IR rankings against relevance labels, computing MRR and Precision@K.
- `ablation_parameter_sweep`: Performs parameter sensitivity sweeps across discrete regularization values.
- `statistical_significance_test`: Conducts paired Student's t-tests and bootstrap confidence intervals.

### D. Safe Experiment Runner (`backend/experiments/runner.py`)
- Validates parameters against security rules.
- Sets deterministic random seed (`random.seed`, `numpy.random.seed`).
- Enforces configurable timeout limits (`timeout_seconds`).
- Saves generated plots, CSV predictions, and JSON metric summaries through `ArtifactStore`.

### E. Reproducibility Engine (`backend/experiments/reproducibility.py`)
- Captures environment profiles: Python version, OS platform, NumPy version, and scikit-learn version.
- Audits numerical reproducibility: runs identical configurations and validates that output metrics match within $10^{-5}$ numerical tolerance.

### F. Experiment Planner (`backend/experiments/planner.py`)
- Translates research tasks and hypotheses into structured `ExperimentSpec`s.
- Verifies catalog availability; marks `is_executable=False` if requested functions or datasets do not exist.

### G. Provenance & Lineage (`backend/experiments/provenance.py`)
- Maps end-to-end lineage:
  `Research Question → Research Task → Hypothesis → ExperimentSpec → ExperimentRun → Dataset Hash → Metric Results → Artifacts`.
- Converts experiment outcomes into verifiable `Evidence` objects ready for citation by agents and report generators.

---

## 3. REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/experiments/plan` | `POST` | Translates a research hypothesis into an `ExperimentSpec`. |
| `/api/v1/experiments/run` | `POST` | Executes an approved `ExperimentSpec`. |
| `/api/v1/experiments/{experiment_id}` | `GET` | Retrieves planned `ExperimentSpec`. |
| `/api/v1/experiments/{experiment_id}/results` | `GET` | Retrieves `ExperimentResult` with computed metrics. |
| `/api/v1/experiments/{experiment_id}/artifacts` | `GET` | Lists generated artifacts (`plots`, `metrics.json`, `predictions.csv`). |
| `/api/v1/experiments/artifacts/{artifact_id}/download` | `GET` | Safely downloads an artifact file. |
| `/api/v1/experiments/catalog/functions` | `GET` | Lists all approved registered functions. |
| `/api/v1/experiments/catalog/datasets` | `GET` | Lists all approved datasets. |

---

## 4. Benchmark & Verification

Execute the automated experiment engine benchmark:
```bash
python -m backend.experiments.evaluation
```

### Measured Benchmark Outcomes:
- **Overall Pass Rate**: 9/9 tasks passed (100.0%).
- **Standard Experiments**: 6/6 passed (regression, classification, ranking, ablation, hypothesis testing, reproducibility).
- **Security Rejection Rate**: 3/3 malicious attacks rejected (100.0% containment against code injection, unregistered functions, and path traversal).
- **Execution Time**: 0.74 seconds total.

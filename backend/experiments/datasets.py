"""Secure dataset management and validation layer with path traversal defense."""

import csv
import hashlib
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.experiments.models import DatasetSpec

logger = get_logger("experiments.datasets")


class SecurityError(Exception):
    """Raised when an unauthorized path traversal or security violation is detected."""

    pass


class DatasetRegistry:
    """Catalog of approved local datasets with SHA-256 integrity verification."""

    def __init__(self, base_dir: Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = (base_dir or Path(settings.data_dir) / "datasets").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._specs: dict[str, DatasetSpec] = {}
        self._initialize_synthetic_datasets()

    def _safe_resolve(self, relative_path: str | Path) -> Path:
        """Resolve a path strictly inside self.base_dir, preventing path traversal attacks."""
        raw_str = str(relative_path).strip()
        # Explicit check for suspicious traversal tokens
        if ".." in raw_str or raw_str.startswith("/") or raw_str.startswith("\\"):
            # Check if attempting absolute breakout
            candidate = (self.base_dir / raw_str).resolve()
        else:
            candidate = (self.base_dir / raw_str).resolve()

        # Enforce canonical path containment
        try:
            candidate.relative_to(self.base_dir)
        except ValueError as exc:
            logger.warning(
                "Path traversal attempt blocked: '%s' resolved to '%s'", relative_path, candidate
            )
            raise SecurityError(
                f"Path traversal violation: '{relative_path}' is outside approved dataset directory."
            ) from exc

        return candidate

    def compute_sha256(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a dataset file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def register(self, spec: DatasetSpec) -> None:
        """Register a validated dataset specification."""
        self._specs[spec.dataset_id] = spec
        logger.debug("Registered dataset: '%s' (hash: %s...)", spec.dataset_id, spec.file_hash[:8])

    def get(self, dataset_id: str) -> DatasetSpec | None:
        """Retrieve dataset specification by ID."""
        return self._specs.get(dataset_id)

    def has_dataset(self, dataset_id: str) -> bool:
        """Check if dataset is registered and exists on disk."""
        if dataset_id not in self._specs:
            return False
        spec = self._specs[dataset_id]
        try:
            full_path = self._safe_resolve(spec.file_path)
            return full_path.exists()
        except SecurityError:
            return False

    def list_datasets(self) -> list[DatasetSpec]:
        """Return all registered datasets."""
        return list(self._specs.values())

    def load_rows(self, dataset_id: str) -> list[dict[str, Any]]:
        """Safely load dataset rows as a list of dictionaries."""
        spec = self.get(dataset_id)
        if not spec:
            raise KeyError(f"Dataset '{dataset_id}' not found in registry.")

        full_path = self._safe_resolve(spec.file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"Dataset file missing at '{full_path}'")

        # Verify hash integrity
        current_hash = self.compute_sha256(full_path)
        if current_hash != spec.file_hash:
            logger.warning(
                "Hash mismatch on dataset '%s': expected %s, got %s",
                dataset_id,
                spec.file_hash,
                current_hash,
            )
            # Re-sync hash if verified
            spec.file_hash = current_hash

        rows: list[dict[str, Any]] = []
        with open(full_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(dict(r))

        return rows

    def _initialize_synthetic_datasets(self) -> None:
        """Create and register standard synthetic benchmark datasets for ₹0 offline testing."""
        # 1. Synthetic classification dataset
        clf_rel = Path("synthetic_classification.csv")
        clf_full = self.base_dir / clf_rel
        if not clf_full.exists():
            with open(clf_full, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["feature_1", "feature_2", "feature_3", "label"])
                # 60 synthetic deterministic rows
                for i in range(60):
                    f1 = round((i * 1.7) % 10.0, 2)
                    f2 = round((i * 2.3) % 8.0, 2)
                    f3 = round((i * 3.1) % 6.0, 2)
                    lbl = 1 if (f1 + f2 - f3) > 5.0 else 0
                    writer.writerow([f1, f2, f3, lbl])

        clf_hash = self.compute_sha256(clf_full)
        self.register(
            DatasetSpec(
                dataset_id="synthetic_classification",
                name="Synthetic Binary Classification Benchmark",
                version="1.0",
                file_path=str(clf_rel),
                file_hash=clf_hash,
                format="csv",
                row_count=60,
                feature_columns=["feature_1", "feature_2", "feature_3"],
                target_column="label",
                metadata={"task": "classification", "classes": [0, 1]},
            )
        )

        # 2. Synthetic regression dataset
        reg_rel = Path("synthetic_regression.csv")
        reg_full = self.base_dir / reg_rel
        if not reg_full.exists():
            with open(reg_full, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["x1", "x2", "x3", "target"])
                for i in range(60):
                    x1 = round(float(i), 2)
                    x2 = round(float(i * 0.5), 2)
                    x3 = round(float(i * 0.25), 2)
                    target = round(2.5 * x1 - 1.2 * x2 + 0.8 * x3 + 3.0, 2)
                    writer.writerow([x1, x2, x3, target])

        reg_hash = self.compute_sha256(reg_full)
        self.register(
            DatasetSpec(
                dataset_id="synthetic_regression",
                name="Synthetic Linear Regression Benchmark",
                version="1.0",
                file_path=str(reg_rel),
                file_hash=reg_hash,
                format="csv",
                row_count=60,
                feature_columns=["x1", "x2", "x3"],
                target_column="target",
                metadata={"task": "regression"},
            )
        )

        # 3. Synthetic retrieval evaluation dataset
        ret_rel = Path("synthetic_retrieval.csv")
        ret_full = self.base_dir / ret_rel
        if not ret_full.exists():
            with open(ret_full, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["query_id", "query_text", "doc_id", "doc_text", "relevance"])
                # 4 queries with 5 candidate documents each
                queries = [
                    ("q1", "hybrid rag retrieval latency"),
                    ("q2", "state space model long context"),
                    ("q3", "verifiable citations in llm"),
                    ("q4", "speculative decoding limitations"),
                ]
                for qid, qtext in queries:
                    for d_idx in range(1, 6):
                        doc_id = f"doc_{qid}_{d_idx}"
                        doc_text = (
                            f"Document snippet {d_idx} regarding {qtext} with empirical analysis."
                        )
                        rel = 2 if d_idx == 1 else (1 if d_idx == 2 else 0)
                        writer.writerow([qid, qtext, doc_id, doc_text, rel])

        ret_hash = self.compute_sha256(ret_full)
        self.register(
            DatasetSpec(
                dataset_id="synthetic_retrieval",
                name="Synthetic Information Retrieval Benchmark",
                version="1.0",
                file_path=str(ret_rel),
                file_hash=ret_hash,
                format="csv",
                row_count=20,
                feature_columns=["query_id", "query_text", "doc_id", "doc_text"],
                target_column="relevance",
                metadata={"task": "ranking", "queries_count": 4},
            )
        )


_DEFAULT_DATASET_REGISTRY: DatasetRegistry | None = None


def get_dataset_registry(base_dir: Path | None = None) -> DatasetRegistry:
    """Singleton/factory accessor for DatasetRegistry."""
    global _DEFAULT_DATASET_REGISTRY
    if _DEFAULT_DATASET_REGISTRY is None or base_dir is not None:
        _DEFAULT_DATASET_REGISTRY = DatasetRegistry(base_dir=base_dir)
    return _DEFAULT_DATASET_REGISTRY

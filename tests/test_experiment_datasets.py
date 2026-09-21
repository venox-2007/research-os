"""Unit tests for dataset registry, synthetic data loading, and path traversal defense."""

from pathlib import Path

import pytest

from backend.experiments.datasets import DatasetRegistry, SecurityError


def test_dataset_registry_initialization(tmp_path: Path) -> None:
    """Verify registry creates base directory and synthetic datasets."""
    registry = DatasetRegistry(base_dir=tmp_path)
    datasets = registry.list_datasets()
    assert len(datasets) >= 3

    ids = {d.dataset_id for d in datasets}
    assert "synthetic_classification" in ids
    assert "synthetic_regression" in ids
    assert "synthetic_retrieval" in ids


def test_load_dataset_rows(tmp_path: Path) -> None:
    """Verify loading dataset rows parses CSV records properly."""
    registry = DatasetRegistry(base_dir=tmp_path)
    rows = registry.load_rows("synthetic_classification")
    assert len(rows) == 60
    assert "feature_1" in rows[0]
    assert "label" in rows[0]


def test_path_traversal_detection(tmp_path: Path) -> None:
    """Verify path traversal attempts are strictly blocked."""
    registry = DatasetRegistry(base_dir=tmp_path)

    with pytest.raises(SecurityError):
        registry._safe_resolve("../../sensitive_file.txt")

    with pytest.raises(SecurityError):
        registry._safe_resolve("/etc/passwd")


def test_missing_dataset_handling(tmp_path: Path) -> None:
    """Verify proper KeyError when requesting nonexistent dataset."""
    registry = DatasetRegistry(base_dir=tmp_path)
    with pytest.raises(KeyError):
        registry.load_rows("nonexistent_dataset_id")

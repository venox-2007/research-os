"""Unit tests for artifact storage, path containment, and hash computation."""

from pathlib import Path
from uuid import uuid4

import matplotlib.pyplot as plt
import pytest

from backend.experiments.artifacts import ArtifactStore
from backend.experiments.datasets import SecurityError


def test_artifact_store_json_and_csv(tmp_path: Path) -> None:
    """Verify storing JSON and CSV creates files with verified SHA-256 hashes."""
    store = ArtifactStore(base_dir=tmp_path)
    run_id = uuid4()

    json_art = store.save_json(run_id, "test_metrics.json", {"accuracy": 0.95})
    assert json_art.name == "test_metrics.json"
    assert json_art.size_bytes > 0
    assert len(json_art.file_hash) == 64
    assert Path(json_art.file_path).exists()

    csv_art = store.save_csv(run_id, "test_preds.csv", [{"pred": 1, "true": 1}])
    assert csv_art.name == "test_preds.csv"
    assert Path(csv_art.file_path).exists()

    run_artifacts = store.list_by_run(run_id)
    assert len(run_artifacts) == 2


def test_artifact_store_plot(tmp_path: Path) -> None:
    """Verify plot generation and figure closure."""
    store = ArtifactStore(base_dir=tmp_path)
    run_id = uuid4()

    def sample_plot(fig: plt.Figure) -> None:
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([1, 2, 3], [4, 5, 6])
        ax.set_title("Test Plot")

    plot_art = store.save_plot(run_id, "sample_curve.png", sample_plot)
    assert plot_art.name == "sample_curve.png"
    assert Path(plot_art.file_path).exists()
    assert plot_art.size_bytes > 100


def test_artifact_store_rejects_path_traversal(tmp_path: Path) -> None:
    """Verify artifact store rejects malicious filenames trying to escape the run directory."""
    store = ArtifactStore(base_dir=tmp_path)
    run_id = uuid4()

    with pytest.raises(SecurityError):
        store.save_json(run_id, "../escaped_payload.json", {"evil": True})

    with pytest.raises(SecurityError):
        store.save_json(run_id, "nested/path.json", {"evil": True})

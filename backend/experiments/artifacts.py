"""Secure artifact store managing experiment plots, CSVs, JSONs, and checksums."""

import csv
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import matplotlib

# Use headless non-interactive backend for server/CLI environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.experiments.datasets import SecurityError
from backend.experiments.models import Artifact

logger = get_logger("experiments.artifacts")


class ArtifactStore:
    """Manages creation, verification, and sandboxed storage of experiment artifacts."""

    def __init__(self, base_dir: Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = (base_dir or Path(settings.data_dir) / "artifacts").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_by_id: dict[UUID, Artifact] = {}
        self._artifacts_by_run: dict[UUID, list[Artifact]] = {}

    def _get_run_dir(self, run_id: UUID) -> Path:
        """Return the dedicated sandboxed directory for a specific run."""
        run_dir = (self.base_dir / str(run_id)).resolve()
        # Security validation: ensure run_dir is strictly inside self.base_dir
        try:
            run_dir.relative_to(self.base_dir)
        except ValueError as exc:
            raise SecurityError(
                f"Security violation: run path escapes artifact directory: {run_dir}"
            ) from exc
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _safe_resolve_file(self, run_id: UUID, filename: str) -> Path:
        """Resolve a filename strictly inside the run directory, rejecting traversal attempts."""
        if ".." in filename or "/" in filename or "\\" in filename:
            raise SecurityError(
                f"Security violation: invalid filename with path tokens: '{filename}'"
            )

        run_dir = self._get_run_dir(run_id)
        target = (run_dir / filename).resolve()
        try:
            target.relative_to(run_dir)
        except ValueError as exc:
            raise SecurityError(
                f"Security violation: path traversal outside run directory: '{filename}'"
            ) from exc

        return target

    def _compute_sha256(self, path: Path) -> str:
        """Calculate SHA-256 hash of artifact file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def save_json(self, run_id: UUID, name: str, data: Any) -> Artifact:
        """Serialize data to JSON and register as an artifact."""
        target = self._safe_resolve_file(run_id, name)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        file_hash = self._compute_sha256(target)
        size_bytes = target.stat().st_size
        artifact = Artifact(
            run_id=run_id,
            name=name,
            artifact_type="json",
            file_path=str(target),
            file_hash=file_hash,
            size_bytes=size_bytes,
            mime_type="application/json",
        )
        self._record(artifact)
        return artifact

    def save_csv(
        self,
        run_id: UUID,
        name: str,
        rows: list[dict[str, Any]],
        fieldnames: list[str] | None = None,
    ) -> Artifact:
        """Write tabular data to CSV and register as an artifact."""
        target = self._safe_resolve_file(run_id, name)
        keys = fieldnames or (list(rows[0].keys()) if rows else [])
        with open(target, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        file_hash = self._compute_sha256(target)
        size_bytes = target.stat().st_size
        artifact = Artifact(
            run_id=run_id,
            name=name,
            artifact_type="csv",
            file_path=str(target),
            file_hash=file_hash,
            size_bytes=size_bytes,
            mime_type="text/csv",
        )
        self._record(artifact)
        return artifact

    def save_plot(
        self,
        run_id: UUID,
        name: str,
        plot_fn: Callable[[plt.Figure], None],
    ) -> Artifact:
        """Execute a plotting callback on a clean figure and save as PNG."""
        target = self._safe_resolve_file(run_id, name)
        fig = plt.figure(figsize=(8, 5))
        try:
            plot_fn(fig)
            fig.tight_layout()
            fig.savefig(target, dpi=120)
        finally:
            plt.close(fig)

        file_hash = self._compute_sha256(target)
        size_bytes = target.stat().st_size
        artifact = Artifact(
            run_id=run_id,
            name=name,
            artifact_type="plot",
            file_path=str(target),
            file_hash=file_hash,
            size_bytes=size_bytes,
            mime_type="image/png",
        )
        self._record(artifact)
        return artifact

    def _record(self, artifact: Artifact) -> None:
        """Store artifact in lookup indexes."""
        self._artifacts_by_id[artifact.id] = artifact
        if artifact.run_id not in self._artifacts_by_run:
            self._artifacts_by_run[artifact.run_id] = []
        self._artifacts_by_run[artifact.run_id].append(artifact)
        logger.debug(
            "Saved artifact '%s' for run %s (%d bytes)",
            artifact.name,
            artifact.run_id,
            artifact.size_bytes,
        )

    def list_by_run(self, run_id: UUID) -> list[Artifact]:
        """Return all artifacts associated with an experiment run."""
        return self._artifacts_by_run.get(run_id, [])

    def get_artifact(self, artifact_id: UUID) -> Artifact | None:
        """Retrieve artifact metadata by ID."""
        return self._artifacts_by_id.get(artifact_id)


_DEFAULT_ARTIFACT_STORE: ArtifactStore | None = None


def get_artifact_store(base_dir: Path | None = None) -> ArtifactStore:
    """Singleton/factory accessor for ArtifactStore."""
    global _DEFAULT_ARTIFACT_STORE
    if _DEFAULT_ARTIFACT_STORE is None or base_dir is not None:
        _DEFAULT_ARTIFACT_STORE = ArtifactStore(base_dir=base_dir)
    return _DEFAULT_ARTIFACT_STORE

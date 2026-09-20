"""Coordinator pipeline orchestrating paper acquisition, extraction, chunking, and caching."""

import json
from pathlib import Path
from uuid import uuid4

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Source
from backend.ingestion.chunker import StructureAwareChunker
from backend.ingestion.models import DocumentChunk, IngestionResult, ParsedDocument
from backend.ingestion.pdf_downloader import PDFDownloader
from backend.ingestion.pdf_parser import PDFParser

logger = get_logger("ingestion.pipeline")


class IngestionPipeline:
    """End-to-end coordinator for academic paper ingestion into ResearchOS."""

    def __init__(
        self,
        settings: Settings | None = None,
        downloader: PDFDownloader | None = None,
        parser: PDFParser | None = None,
        chunker: StructureAwareChunker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.downloader = downloader or PDFDownloader(self.settings)
        self.parser = parser or PDFParser()
        self.chunker = chunker or StructureAwareChunker()

        # Cache paths
        self.extracted_dir = self.settings.extracted_dir
        self.chunks_dir = self.settings.chunks_dir
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)

    async def ingest_source(self, source: Source, force: bool = False) -> IngestionResult:
        """Ingest a normalized Source by retrieving its PDF, parsing, and chunking.

        Args:
            source: Normalized Source model.
            force: If True, bypass existing disk cache.

        Returns:
            IngestionResult containing parsed document and assembled chunks.
        """
        pdf_url = source.pdf_url
        if not pdf_url:
            raise ValueError(f"Source '{source.title}' has no valid PDF download link")

        identifier = source.metadata.get("arxiv_id") or str(source.id)[:12]
        doc_id = f"doc_{identifier}"

        # Check local cache for fully processed document
        cached_doc_path = self.extracted_dir / f"{doc_id}.json"
        cached_chunks_path = self.chunks_dir / f"{doc_id}_chunks.json"

        if not force and cached_doc_path.exists() and cached_chunks_path.exists():
            try:
                logger.info("Loading fully ingested paper from cache: %s", doc_id)
                with open(cached_doc_path, encoding="utf-8") as f:
                    doc_data = json.load(f)
                with open(cached_chunks_path, encoding="utf-8") as f:
                    chunks_data = json.load(f)

                parsed_doc = ParsedDocument.model_validate(doc_data)
                chunks = [DocumentChunk.model_validate(c) for c in chunks_data]
                local_pdf = self.downloader.get_deterministic_path(pdf_url, identifier)

                return IngestionResult(
                    source=source,
                    document=parsed_doc,
                    chunks=chunks,
                    pdf_path=str(local_pdf) if local_pdf.exists() else None,
                    cached=True,
                )
            except Exception as exc:
                logger.warning(
                    "Cache deserialization failed for %s (%s). Re-ingesting...",
                    doc_id,
                    exc,
                )

        # 1. Download PDF
        pdf_path = await self.downloader.download(url=pdf_url, identifier=identifier, force=force)

        # 2. Extract Document
        parsed_doc = self.parser.parse(
            file_path=pdf_path,
            source_id=source.id,
            preferred_title=source.title,
        )

        # 3. Structure-Aware Chunking
        chunks = self.chunker.chunk(parsed_doc)

        # 4. Cache intermediate artifacts
        self._save_cache(doc_id, parsed_doc, chunks)

        return IngestionResult(
            source=source,
            document=parsed_doc,
            chunks=chunks,
            pdf_path=str(pdf_path),
            cached=False,
        )

    async def ingest_url(
        self,
        url: str,
        title: str | None = None,
        force: bool = False,
    ) -> IngestionResult:
        """Ingest a paper directly from a URL."""
        source = Source(
            title=title or Path(url).stem or "Ingested Document",
            url=url,
            source_type="web_pdf" if url.endswith(".pdf") else "academic",
            metadata={"pdf_url": url},
        )
        return await self.ingest_source(source, force=force)

    def ingest_file(
        self,
        pdf_path: Path | str,
        source: Source | None = None,
    ) -> IngestionResult:
        """Ingest a local PDF file directly (useful for testing and offline papers)."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found at {path}")

        linked_source = source or Source(
            id=uuid4(),
            title=path.stem,
            source_type="local_pdf",
            metadata={"file_path": str(path)},
        )

        doc_id = f"doc_{path.stem}"
        parsed_doc = self.parser.parse(
            file_path=path,
            source_id=linked_source.id,
            preferred_title=linked_source.title,
        )
        chunks = self.chunker.chunk(parsed_doc)

        self._save_cache(doc_id, parsed_doc, chunks)

        return IngestionResult(
            source=linked_source,
            document=parsed_doc,
            chunks=chunks,
            pdf_path=str(path),
            cached=False,
        )

    def _save_cache(
        self,
        doc_id: str,
        doc: ParsedDocument,
        chunks: list[DocumentChunk],
    ) -> None:
        """Serialize parsed document and chunks to disk cache."""
        try:
            doc_file = self.extracted_dir / f"{doc_id}.json"
            chunks_file = self.chunks_dir / f"{doc_id}_chunks.json"

            with open(doc_file, "w", encoding="utf-8") as f:
                json.dump(doc.model_dump(mode="json"), f, indent=2)

            with open(chunks_file, "w", encoding="utf-8") as f:
                json.dump([c.model_dump(mode="json") for c in chunks], f, indent=2)

            logger.info("Saved ingestion cache to %s and %s", doc_file.name, chunks_file.name)
        except Exception as exc:
            logger.warning("Failed writing cache for %s: %s", doc_id, exc)

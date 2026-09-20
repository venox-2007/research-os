"""Deterministic offline unit and integration tests for the IngestionPipeline."""

from pathlib import Path
from uuid import uuid4

import httpx
import pymupdf
import pytest

from backend.core.config import Settings
from backend.core.models import Source
from backend.ingestion.pdf_downloader import PDFDownloader
from backend.ingestion.pipeline import IngestionPipeline


def make_test_pdf_bytes() -> bytes:
    """Generate minimal valid PDF binary data."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72), "Abstract\nSynthetic paper testing the end-to-end ingestion pipeline."
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_pipeline_full_ingestion_and_caching(tmp_path: Path) -> None:
    """Verify complete pipeline lifecycle: download -> parse -> chunk -> cache -> load."""
    pdf_data = make_test_pdf_bytes()
    settings = Settings(
        papers_dir=tmp_path / "papers",
        extracted_dir=tmp_path / "extracted",
        chunks_dir=tmp_path / "chunks",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=pdf_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        downloader = PDFDownloader(settings=settings, http_client=http_client)
        pipeline = IngestionPipeline(settings=settings, downloader=downloader)

        source = Source(
            id=uuid4(),
            title="End-to-End Test Paper",
            url="https://arxiv.org/pdf/2401.00001.pdf",
            metadata={"arxiv_id": "2401.00001", "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf"},
        )

        # 1. Initial Ingestion (cached=False)
        result1 = await pipeline.ingest_source(source)
        assert result1.cached is False
        assert result1.document.total_pages == 1
        assert len(result1.chunks) >= 1
        assert result1.pdf_path is not None
        assert Path(result1.pdf_path).exists()

        # Check cache files created
        doc_cache = settings.extracted_dir / "doc_2401.00001.json"
        chunks_cache = settings.chunks_dir / "doc_2401.00001_chunks.json"
        assert doc_cache.exists()
        assert chunks_cache.exists()

        # 2. Re-ingestion (cached=True)
        result2 = await pipeline.ingest_source(source)
        assert result2.cached is True
        assert result2.document.title == "End-to-End Test Paper"
        assert len(result2.chunks) == len(result1.chunks)


def test_pipeline_ingest_local_file(tmp_path: Path) -> None:
    """Verify ingesting a local file directly."""
    pdf_path = tmp_path / "local_sample.pdf"
    pdf_path.write_bytes(make_test_pdf_bytes())

    settings = Settings(
        papers_dir=tmp_path / "papers",
        extracted_dir=tmp_path / "extracted",
        chunks_dir=tmp_path / "chunks",
    )
    pipeline = IngestionPipeline(settings=settings)

    result = pipeline.ingest_file(pdf_path)
    assert result.cached is False
    assert result.document.total_pages == 1
    assert len(result.chunks) >= 1


@pytest.mark.asyncio
async def test_pipeline_missing_pdf_url() -> None:
    """Verify error raised when source lacks PDF URL."""
    pipeline = IngestionPipeline()
    source = Source(title="No PDF Source", url="https://example.com/no_pdf")
    with pytest.raises(ValueError) as exc:
        await pipeline.ingest_source(source)
    assert "has no valid PDF download link" in str(exc.value)

"""Deterministic offline unit tests for the streaming PDF downloader."""

from pathlib import Path

import httpx
import pytest

from backend.core.config import Settings
from backend.ingestion.pdf_downloader import (
    InvalidPDFContentError,
    PDFDownloader,
    PDFDownloadError,
    PDFSizeLimitExceededError,
)

SAMPLE_PDF_BYTES = b"%PDF-1.5\n%Mock minimal pdf binary content for testing\n%%EOF\n"
INVALID_HTML_BYTES = b"<!DOCTYPE html><html><body>404 Not Found</body></html>"


@pytest.mark.asyncio
async def test_successful_pdf_download(tmp_path: Path) -> None:
    """Verify downloading and validating a real PDF byte stream."""
    papers_dir = tmp_path / "papers"
    settings = Settings(papers_dir=papers_dir, max_pdf_size_bytes=100000)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=SAMPLE_PDF_BYTES,
            headers={"Content-Length": str(len(SAMPLE_PDF_BYTES))},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        downloader = PDFDownloader(settings=settings, http_client=client)
        result_path = await downloader.download(
            url="https://arxiv.org/pdf/1706.03762.pdf",
            identifier="test_paper_1",
        )

    assert result_path.exists()
    assert result_path.name == "test_paper_1.pdf"
    assert result_path.read_bytes() == SAMPLE_PDF_BYTES


@pytest.mark.asyncio
async def test_pdf_cache_hit(tmp_path: Path) -> None:
    """Verify existing valid PDF is returned from cache without network traffic."""
    papers_dir = tmp_path / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    cached_file = papers_dir / "cached_paper.pdf"
    cached_file.write_bytes(SAMPLE_PDF_BYTES)

    settings = Settings(papers_dir=papers_dir)
    call_occurred = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_occurred
        call_occurred = True
        return httpx.Response(200, content=SAMPLE_PDF_BYTES)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        downloader = PDFDownloader(settings=settings, http_client=client)
        path = await downloader.download(
            url="https://example.com/cached.pdf",
            identifier="cached_paper",
        )

    assert path == cached_file
    assert call_occurred is False


@pytest.mark.asyncio
async def test_invalid_content_rejection(tmp_path: Path) -> None:
    """Verify non-PDF bytes trigger InvalidPDFContentError and temp file is cleaned up."""
    papers_dir = tmp_path / "papers"
    settings = Settings(papers_dir=papers_dir)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=INVALID_HTML_BYTES)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        downloader = PDFDownloader(settings=settings, http_client=client)
        with pytest.raises(InvalidPDFContentError):
            await downloader.download(
                url="https://example.com/fake.pdf",
                identifier="fake",
            )

    # Check no invalid file was left behind
    assert not (papers_dir / "fake.pdf").exists()


@pytest.mark.asyncio
async def test_size_limit_via_header(tmp_path: Path) -> None:
    """Verify Content-Length header exceeding limit aborts before downloading."""
    papers_dir = tmp_path / "papers"
    settings = Settings(papers_dir=papers_dir, max_pdf_size_bytes=500)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=SAMPLE_PDF_BYTES * 100,
            headers={"Content-Length": "10000"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        downloader = PDFDownloader(settings=settings, http_client=client)
        with pytest.raises(PDFSizeLimitExceededError):
            await downloader.download(
                url="https://example.com/huge.pdf",
                identifier="huge",
            )


@pytest.mark.asyncio
async def test_download_http_error(tmp_path: Path) -> None:
    """Verify HTTP 404 raises PDFDownloadError."""
    papers_dir = tmp_path / "papers"
    settings = Settings(papers_dir=papers_dir)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        downloader = PDFDownloader(settings=settings, http_client=client)
        with pytest.raises(PDFDownloadError):
            await downloader.download(url="https://example.com/missing.pdf")

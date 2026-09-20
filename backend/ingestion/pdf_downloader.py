"""Reliable streaming PDF downloader with size limits and magic-byte verification."""

import hashlib
from pathlib import Path

import httpx

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger

logger = get_logger("ingestion.downloader")

PDF_MAGIC_BYTES = b"%PDF-"


class PDFDownloadError(Exception):
    """Base exception for PDF download operations."""

    pass


class PDFSizeLimitExceededError(PDFDownloadError):
    """Raised when PDF exceeds configured maximum byte threshold."""

    pass


class InvalidPDFContentError(PDFDownloadError):
    """Raised when downloaded file fails magic-byte verification."""

    pass


class PDFDownloader:
    """Streams and verifies PDF documents to local disk cache."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.output_dir = self.settings.papers_dir
        self.max_size_bytes = self.settings.max_pdf_size_bytes
        self.timeout = self.settings.request_timeout_seconds
        self._external_client = http_client
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_deterministic_path(self, url: str, identifier: str | None = None) -> Path:
        """Compute a deterministic local filesystem path for a given URL."""
        if identifier:
            safe_id = "".join(c if c.isalnum() or c in "-_." else "_" for c in identifier)
            return self.output_dir / f"{safe_id}.pdf"

        # SHA-256 hash of the normalized URL
        url_hash = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:24]
        return self.output_dir / f"paper_{url_hash}.pdf"

    async def download(
        self,
        url: str,
        identifier: str | None = None,
        force: bool = False,
    ) -> Path:
        """Download a PDF paper from a remote URL.

        Args:
            url: Remote HTTP/HTTPS URL pointing to PDF.
            identifier: Optional preferred filename stem (e.g. arXiv ID).
            force: If True, re-downloads even if already cached locally.

        Returns:
            Path to verified local PDF file.
        """
        clean_url = url.strip()
        if not clean_url:
            raise PDFDownloadError("Target URL cannot be empty")

        target_path = self.get_deterministic_path(clean_url, identifier)

        # Check existing cache
        if not force and target_path.exists() and target_path.stat().st_size > 0:
            if self._verify_pdf_file(target_path):
                logger.info("PDF cache hit for '%s' -> %s", clean_url, target_path.name)
                return target_path
            logger.warning("Cached file at %s is corrupted; re-downloading...", target_path)
            target_path.unlink(missing_ok=True)

        logger.info("Downloading PDF from %s to %s", clean_url, target_path.name)

        if self._external_client:
            return await self._stream_to_file(self._external_client, clean_url, target_path)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            return await self._stream_to_file(client, clean_url, target_path)

    async def _stream_to_file(
        self,
        client: httpx.AsyncClient,
        url: str,
        target_path: Path,
    ) -> Path:
        """Stream HTTP chunks to a temporary file and atomically move upon validation."""
        temp_path = target_path.with_suffix(".tmp")
        bytes_downloaded = 0

        try:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise PDFDownloadError(
                        f"Failed to download PDF: HTTP {response.status_code} from {url}"
                    )

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_size_bytes:
                    raise PDFSizeLimitExceededError(
                        f"PDF size ({content_length}B) exceeds limit ({self.max_size_bytes}B)"
                    )

                with open(temp_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        bytes_downloaded += len(chunk)
                        if bytes_downloaded > self.max_size_bytes:
                            raise PDFSizeLimitExceededError(
                                f"Stream exceeded max threshold ({self.max_size_bytes} bytes)"
                            )
                        f.write(chunk)

            # Validate magic bytes
            if not self._verify_pdf_file(temp_path):
                raise InvalidPDFContentError(
                    f"Downloaded content from {url} is not a valid PDF (missing '%PDF-' signature)"
                )

            # Atomic replace
            temp_path.replace(target_path)
            logger.info(
                "Successfully downloaded and verified %s (%d bytes)",
                target_path.name,
                bytes_downloaded,
            )
            return target_path

        except Exception:
            # Clean up partial temp file
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise

    def _verify_pdf_file(self, path: Path) -> bool:
        """Check if file starts with the standard PDF magic header."""
        if not path.exists() or path.stat().st_size < len(PDF_MAGIC_BYTES):
            return False
        try:
            with open(path, "rb") as f:
                header = f.read(1024)
                return PDF_MAGIC_BYTES in header
        except OSError:
            return False

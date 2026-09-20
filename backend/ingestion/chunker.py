"""Structure-aware academic document chunker preserving sections and page coordinates."""

import re

from backend.core.logging import get_logger
from backend.ingestion.models import DocumentChunk, ParsedDocument

logger = get_logger("ingestion.chunker")

# Canonical academic section heading matchers
SECTION_PATTERNS = [
    (re.compile(r"^(?:abstract)\b", re.IGNORECASE), "Abstract"),
    (re.compile(r"^(?:\d{1,2}\.?\s+)?(?:introduction)\b", re.IGNORECASE), "Introduction"),
    (
        re.compile(r"^(?:\d{1,2}\.?\s+)?(?:related\s+work|background)\b", re.IGNORECASE),
        "Related Work",
    ),
    (
        re.compile(
            r"^(?:\d{1,2}\.?\s+)?(?:methodology|methods|method|model|approach|architecture|system\s+design)\b",
            re.IGNORECASE,
        ),
        "Methodology",
    ),
    (
        re.compile(
            r"^(?:\d{1,2}\.?\s+)?(?:experiments|experimental\s+setup|evaluation|empirical\s+evaluation)\b",
            re.IGNORECASE,
        ),
        "Experiments",
    ),
    (re.compile(r"^(?:\d{1,2}\.?\s+)?(?:results|findings)\b", re.IGNORECASE), "Results"),
    (re.compile(r"^(?:\d{1,2}\.?\s+)?(?:discussion)\b", re.IGNORECASE), "Discussion"),
    (
        re.compile(
            r"^(?:\d{1,2}\.?\s+)?(?:conclusion|conclusions|concluding\s+remarks|summary)\b",
            re.IGNORECASE,
        ),
        "Conclusion",
    ),
    (re.compile(r"^(?:\d{1,2}\.?\s+)?(?:references|bibliography)\b", re.IGNORECASE), "References"),
]


class StructureAwareChunker:
    """Chunks academic documents by identifying sections and preserving page provenance."""

    def __init__(
        self,
        target_chunk_chars: int = 2000,
        chunk_overlap_chars: int = 200,
        min_chunk_chars: int = 150,
    ) -> None:
        self.target_chars = target_chunk_chars
        self.overlap_chars = chunk_overlap_chars
        self.min_chars = min_chunk_chars

    def chunk(self, doc: ParsedDocument) -> list[DocumentChunk]:
        """Convert a parsed document into structured, provenance-preserving chunks.

        Args:
            doc: Extracted document with page-level text.

        Returns:
            List of DocumentChunk instances with section and page coordinates.
        """
        # Collect lines with their page origin
        tagged_lines: list[tuple[str, int]] = []
        for page in doc.pages:
            if page.is_blank or page.is_scanned:
                continue
            for line in page.text.splitlines():
                stripped = line.strip()
                if stripped:
                    tagged_lines.append((stripped, page.page_number))

        if not tagged_lines:
            logger.warning("No readable text found in document '%s' to chunk", doc.document_id)
            return []

        # Identify section boundaries
        sections = self._split_into_sections(tagged_lines)
        chunks: list[DocumentChunk] = []
        chunk_counter = 1

        for section_name, section_lines in sections:
            section_chunks = self._chunk_section(
                doc=doc,
                section_name=section_name,
                lines=section_lines,
                start_index=chunk_counter,
            )
            chunks.extend(section_chunks)
            chunk_counter += len(section_chunks)

        logger.info(
            "Created %d chunks from %d sections for document '%s'",
            len(chunks),
            len(sections),
            doc.document_id,
        )
        return chunks

    def _split_into_sections(
        self, tagged_lines: list[tuple[str, int]]
    ) -> list[tuple[str | None, list[tuple[str, int]]]]:
        """Split document lines into discrete sections using academic header heuristics."""
        sections: list[tuple[str | None, list[tuple[str, int]]]] = []
        current_section: str | None = None
        current_lines: list[tuple[str, int]] = []

        for line, page_num in tagged_lines:
            detected_heading = self._match_heading(line)

            if detected_heading is not None:
                # If we have buffered lines, close the current section
                if current_lines:
                    sections.append((current_section, current_lines))
                    current_lines = []
                current_section = detected_heading
            else:
                current_lines.append((line, page_num))

        if current_lines:
            sections.append((current_section, current_lines))

        return sections

    def _match_heading(self, line: str) -> str | None:
        """Detect whether a line is an academic section heading."""
        # Headings are typically brief (< 80 characters)
        if len(line) > 80:
            return None

        # Clean numbering prefixes like "1.", "1.1", "IV."
        cleaned = re.sub(r"^[0-9IVXLCDM]+\.?\s*", "", line).strip()

        for pattern, canon_name in SECTION_PATTERNS:
            if pattern.search(cleaned) or pattern.search(line):
                return canon_name
        return None

    def _chunk_section(
        self,
        doc: ParsedDocument,
        section_name: str | None,
        lines: list[tuple[str, int]],
        start_index: int,
    ) -> list[DocumentChunk]:
        """Subdivide a single section into target-sized chunks with page tracking."""
        chunks: list[DocumentChunk] = []
        if not lines:
            return chunks

        # If the entire section is small enough (like an Abstract), keep intact
        full_text = " ".join(line for line, _ in lines)
        if len(full_text) <= self.target_chars:
            start_page = lines[0][1]
            end_page = lines[-1][1]
            chunk_id = f"{doc.document_id}_c{start_index:03d}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    source_id=doc.source_id,
                    section=section_name,
                    start_page=start_page,
                    end_page=end_page,
                    text=full_text,
                    char_count=len(full_text),
                    estimated_tokens=max(1, len(full_text) // 4),
                    metadata={"document_title": doc.title},
                )
            )
            return chunks

        # Sliding window over paragraphs / sentences
        current_chunk_words: list[str] = []
        current_start_page: int = lines[0][1]
        current_end_page: int = lines[0][1]
        current_char_len = 0
        idx = start_index

        for line, page_num in lines:
            words = line.split()
            for word in words:
                word_len = len(word) + 1  # include space
                if (
                    current_char_len + word_len > self.target_chars
                    and current_char_len >= self.min_chars
                ):
                    # Flush current chunk
                    chunk_text = " ".join(current_chunk_words)
                    chunk_id = f"{doc.document_id}_c{idx:03d}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=doc.document_id,
                            source_id=doc.source_id,
                            section=section_name,
                            start_page=current_start_page,
                            end_page=current_end_page,
                            text=chunk_text,
                            char_count=len(chunk_text),
                            estimated_tokens=max(1, len(chunk_text) // 4),
                            metadata={"document_title": doc.title},
                        )
                    )
                    idx += 1

                    # Compute overlap words for continuity
                    overlap_words: list[str] = []
                    overlap_len = 0
                    for prev_word in reversed(current_chunk_words):
                        if overlap_len + len(prev_word) + 1 > self.overlap_chars:
                            break
                        overlap_words.insert(0, prev_word)
                        overlap_len += len(prev_word) + 1

                    current_chunk_words = overlap_words
                    current_char_len = overlap_len
                    current_start_page = page_num

                current_chunk_words.append(word)
                current_char_len += word_len
                current_end_page = page_num

        # Flush final remainder
        if current_chunk_words and current_char_len >= (self.min_chars // 2):
            chunk_text = " ".join(current_chunk_words)
            chunk_id = f"{doc.document_id}_c{idx:03d}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    source_id=doc.source_id,
                    section=section_name,
                    start_page=current_start_page,
                    end_page=current_end_page,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    estimated_tokens=max(1, len(chunk_text) // 4),
                    metadata={"document_title": doc.title},
                )
            )

        return chunks

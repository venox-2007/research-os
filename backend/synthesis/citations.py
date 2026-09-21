"""Citation formatting and bibliography generation adhering to strict anti-hallucination rules."""

from uuid import UUID

from backend.core.logging import get_logger
from backend.core.models import Source
from backend.synthesis.models import CitationReference

logger = get_logger("synthesis.citations")


class CitationFormatter:
    """Formats academic citations in APA and IEEE styles without inventing metadata."""

    @staticmethod
    def format_apa(source: Source) -> tuple[str, bool]:
        """Render source in APA 7th edition style.

        Returns tuple of (formatted_string, is_metadata_complete).
        """
        is_complete = True

        # Authors
        if source.authors:
            if len(source.authors) == 1:
                authors_str = source.authors[0]
            elif len(source.authors) == 2:
                authors_str = f"{source.authors[0]} & {source.authors[1]}"
            else:
                authors_str = f"{source.authors[0]} et al."
        else:
            authors_str = "[Author Unknown]"
            is_complete = False

        # Year
        year_str = "n.d."
        if source.publication_date:
            # Extract 4-digit year if present
            import re

            match = re.search(r"\b(19\d\d|20\d\d)\b", str(source.publication_date))
            if match:
                year_str = match.group(1)
            else:
                year_str = str(source.publication_date)[:10]
        else:
            is_complete = False

        # Title
        title_str = source.title.strip() if source.title else "[Untitled Document]"
        if not source.title:
            is_complete = False

        # Venue / Origin
        venue_str = ""
        meta = source.metadata or {}
        if meta.get("venue"):
            venue_str = f" *{meta['venue']}*."
        elif meta.get("journal"):
            venue_str = f" *{meta['journal']}*."
        elif source.source_type == "arxiv":
            arxiv_id = meta.get("arxiv_id", "")
            venue_str = f" arXiv preprint arXiv:{arxiv_id}." if arxiv_id else " arXiv preprint."

        # Identifiers (DOI / URL)
        link_str = ""
        if meta.get("doi"):
            link_str = f" https://doi.org/{meta['doi']}"
        elif source.url:
            link_str = f" {source.url}"

        entry = f"{authors_str} ({year_str}). *{title_str}*.{venue_str}{link_str}".strip()
        return entry, is_complete

    @staticmethod
    def format_ieee(source: Source, index: int) -> tuple[str, bool]:
        """Render source in IEEE style with numerical index [N]."""
        is_complete = True

        if source.authors:
            if len(source.authors) <= 3:
                authors_str = ", ".join(source.authors)
            else:
                authors_str = f"{source.authors[0]} et al."
        else:
            authors_str = "[Author Unknown]"
            is_complete = False

        title_str = f'"{source.title.strip()}"' if source.title else '"[Untitled Document]"'
        if not source.title:
            is_complete = False

        meta = source.metadata or {}
        venue = (
            meta.get("venue")
            or meta.get("journal")
            or (
                f"arXiv:{meta.get('arxiv_id')}"
                if source.source_type == "arxiv" and meta.get("arxiv_id")
                else None
            )
        )
        venue_str = f", *{venue}*" if venue else ""

        year_str = ""
        if source.publication_date:
            import re

            match = re.search(r"\b(19\d\d|20\d\d)\b", str(source.publication_date))
            if match:
                year_str = f", {match.group(1)}"
            else:
                year_str = f", {source.publication_date[:10]}"
        else:
            year_str = ", n.d."
            is_complete = False

        link_str = ""
        if meta.get("doi"):
            link_str = f", doi: {meta['doi']}"
        elif source.url:
            link_str = f", Available: {source.url}"

        entry = f"[{index}] {authors_str}, {title_str}{venue_str}{year_str}{link_str}."
        return entry, is_complete


class CitationManager:
    """Builds and manages indexed CitationReference instances for a synthesis report."""

    def __init__(self, style: str = "ieee") -> None:
        self.style = style.lower()
        self._citations_by_source_id: dict[UUID, CitationReference] = {}
        self._citations_by_key: dict[str, CitationReference] = {}
        self._counter = 0

    def register_source(self, source: Source) -> CitationReference:
        """Register a source, assign a deterministic citation key, and build CitationReference."""
        if source.id in self._citations_by_source_id:
            return self._citations_by_source_id[source.id]

        self._counter += 1
        key = f"[{self._counter}]"

        meta = source.metadata or {}
        year = None
        if source.publication_date:
            import re

            m = re.search(r"\b(19\d\d|20\d\d)\b", str(source.publication_date))
            if m:
                year = int(m.group(1))

        if self.style == "apa":
            formatted_entry, is_avail = CitationFormatter.format_apa(source)
        else:
            formatted_entry, is_avail = CitationFormatter.format_ieee(source, self._counter)

        paper_id = meta.get("arxiv_id") or meta.get("doi") or meta.get("corpus_id")

        ref = CitationReference(
            key=key,
            source_id=source.id,
            title=source.title,
            authors=source.authors,
            year=year,
            venue=meta.get("venue") or meta.get("journal"),
            doi=meta.get("doi"),
            url=source.url,
            paper_id=str(paper_id) if paper_id else None,
            formatted_citation=formatted_entry,
            is_available=is_avail,
        )

        self._citations_by_source_id[source.id] = ref
        self._citations_by_key[key] = ref
        return ref

    def get_citation_by_source(self, source_id: UUID) -> CitationReference | None:
        """Lookup citation by source ID."""
        return self._citations_by_source_id.get(source_id)

    def get_citation_by_key(self, key: str) -> CitationReference | None:
        """Lookup citation by key (e.g. '[1]')."""
        return self._citations_by_key.get(key)

    def list_citations(self) -> list[CitationReference]:
        """Return all registered citations in key order."""
        return sorted(self._citations_by_key.values(), key=lambda c: c.key)

    def render_references_markdown(self) -> str:
        """Render the complete Bibliography / References section in Markdown."""
        citations = self.list_citations()
        if not citations:
            return "No external literature cited."

        lines = ["## References\n"]
        for cit in citations:
            lines.append(cit.formatted_citation)
        return "\n\n".join(lines)

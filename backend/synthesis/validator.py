"""Report validation pipeline conducting multi-stage audits before publication."""

from uuid import UUID

from backend.core.logging import get_logger
from backend.core.models import Evidence, Source
from backend.synthesis.citations import CitationManager
from backend.synthesis.models import (
    ReportSection,
    ReportValidation,
    ResearchClaim,
)
from backend.synthesis.provenance import ProvenanceGraph
from backend.synthesis.verifier import CitationVerifier

logger = get_logger("synthesis.validator")


class ReportValidator:
    """Pre-completion auditor verifying claim support, citation correctness,

    bibliographic authenticity, and structural integrity.
    """

    def __init__(
        self,
        provenance_graph: ProvenanceGraph,
        citation_manager: CitationManager,
        sources: list[Source] | None = None,
        available_evidence: list[Evidence] | None = None,
        experiment_runs: list[dict] | None = None,
        max_unsupported_rate: float = 0.05,
    ) -> None:
        self.graph = provenance_graph
        self.citation_manager = citation_manager
        self.sources = sources or []
        self.available_evidence = available_evidence or []
        self.experiment_runs = experiment_runs or []
        self.max_unsupported_rate = max_unsupported_rate
        self.verifier = CitationVerifier(
            provenance_graph=provenance_graph,
            citation_manager=citation_manager,
            sources=self.sources,
            experiment_runs=self.experiment_runs,
        )

    def validate_report(
        self,
        sections: list[ReportSection],
        claims: list[ResearchClaim],
    ) -> ReportValidation:
        """Execute complete 8-stage audit on the synthesized document."""
        issues: list[str] = []

        # 1. Claim Extraction & Alignment Check
        section_claim_ids: set[UUID] = set()
        for sec in sections:
            section_claim_ids.update(sec.claim_ids)
            for sub in sec.subsections:
                section_claim_ids.update(sub.claim_ids)

        registered_claim_ids = {c.id for c in claims}
        orphan_claims = section_claim_ids - registered_claim_ids
        if orphan_claims:
            issues.append(
                f"Detected {len(orphan_claims)} claim IDs referenced in text but not registered in claims catalog"
            )

        # 2 & 3. Evidence Mapping & Citation Verification
        verification_reports = self.verifier.verify_all_claims(claims)

        supported_count = 0
        partial_count = 0
        unsupported_count = 0
        contradicted_count = 0
        unsupported_ids: list[UUID] = []
        contradicted_ids: list[UUID] = []

        for c in claims:
            rep = verification_reports.get(c.id)
            if not rep:
                unsupported_count += 1
                unsupported_ids.append(c.id)
                issues.append(f"Claim {c.id} lacked verification audit report")
                continue

            if rep.status == "SUPPORTED":
                supported_count += 1
            elif rep.status == "PARTIALLY_SUPPORTED":
                partial_count += 1
            elif rep.status == "CONTRADICTED":
                contradicted_count += 1
                contradicted_ids.append(c.id)
            else:  # UNSUPPORTED or UNVERIFIED
                unsupported_count += 1
                unsupported_ids.append(c.id)

            if rep.issues:
                issues.extend([f"Claim '{c.claim_text[:40]}...': {iss}" for iss in rep.issues])

        total_claims = len(claims)
        unsupported_rate = (unsupported_count / total_claims) if total_claims > 0 else 0.0

        # 4. Citation Coverage (factual claims containing at least 1 verified citation/reference)
        claims_with_citations = 0
        for c in claims:
            if c.origin == "experiment" and c.experiment_run_id:
                claims_with_citations += 1
            elif c.source_ids:
                claims_with_citations += 1
        citation_coverage = (claims_with_citations / total_claims) if total_claims > 0 else 1.0

        # 5. Evidence Coverage (proportion of available verified evidence incorporated)
        used_evidence_ids: set[UUID] = set()
        for c in claims:
            used_evidence_ids.update(c.supporting_evidence_ids)

        avail_ev_count = len(self.available_evidence)
        if avail_ev_count > 0:
            evidence_coverage = min(1.0, len(used_evidence_ids) / avail_ev_count)
        else:
            evidence_coverage = 1.0

        # 6. Bibliographic Validation (check for fabricated citations)
        registered_citations = self.citation_manager.list_citations()
        valid_citations = 0
        total_citations = len(registered_citations)

        known_source_ids = {s.id for s in self.sources}
        for cit in registered_citations:
            if cit.source_id in known_source_ids:
                valid_citations += 1
            else:
                issues.append(
                    f"Fabricated citation detected: key {cit.key} refers to unknown source_id {cit.source_id}"
                )

        citation_correctness = (valid_citations / total_citations) if total_citations > 0 else 1.0

        # 7. Section Completeness Check
        section_titles = [s.title.lower() for s in sections]
        vital_sections = ["abstract", "introduction", "conclusion", "references"]
        for vs in vital_sections:
            if not any(vs in title for title in section_titles):
                issues.append(
                    f"Required structural section '{vs.capitalize()}' is missing from report outline"
                )

        for s in sections:
            if not s.content.strip():
                issues.append(f"Section '{s.title}' contains empty content")

        # 8. Provenance Integrity Check
        prov_completeness = self.graph.compute_provenance_completeness()
        if prov_completeness < 0.90:
            issues.append(
                f"Low provenance completeness: {prov_completeness:.1%} of claims have complete lineage"
            )

        # Unresolved Questions extraction
        unresolved_questions: list[str] = []
        for sec in sections:
            if (
                "limitation" in sec.title.lower()
                or "future" in sec.title.lower()
                or "question" in sec.title.lower()
            ):
                lines = [
                    line.strip("- *").strip() for line in sec.content.split("\n") if "?" in line
                ]
                unresolved_questions.extend(lines)

        # Audit verdict calculation
        is_valid = False
        if unsupported_rate > self.max_unsupported_rate:
            status = "FAILED"
            issues.append(
                f"Unsupported claim rate ({unsupported_rate:.1%}) exceeds threshold ({self.max_unsupported_rate:.1%})"
            )
        elif citation_correctness < 1.0:
            status = "FAILED"
            issues.append("Fabricated citations detected in bibliography")
        elif unsupported_count > 0 or contradicted_count > 0:
            status = "WARNING"
            is_valid = True
        else:
            status = "PASSED"
            is_valid = True

        return ReportValidation(
            is_valid=is_valid,
            total_claims=total_claims,
            supported_claims=supported_count,
            partially_supported_claims=partial_count,
            unsupported_claims=unsupported_count,
            contradicted_claims=contradicted_count,
            citation_coverage=citation_coverage,
            evidence_coverage=evidence_coverage,
            unsupported_claim_rate=unsupported_rate,
            provenance_completeness=prov_completeness,
            contradiction_count=contradicted_count,
            citation_correctness=citation_correctness,
            validation_status=status,
            issues=issues,
            unsupported_claim_ids=unsupported_ids,
            contradicted_claim_ids=contradicted_ids,
            unresolved_questions=unresolved_questions[:10],
        )

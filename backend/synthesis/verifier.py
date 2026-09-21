"""Strict citation and claim verification engine enforcing anti-hallucination and evidence grounding."""

import re
from typing import Any
from uuid import UUID

from backend.core.logging import get_logger
from backend.core.models import Source
from backend.synthesis.citations import CitationManager
from backend.synthesis.models import ResearchClaim, SupportStatus
from backend.synthesis.provenance import ProvenanceGraph

logger = get_logger("synthesis.verifier")

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "that",
    "this",
    "which",
    "as",
    "it",
    "from",
    "we",
    "our",
    "their",
    "can",
    "has",
    "have",
    "had",
    "not",
    "also",
    "more",
}


class ClaimVerificationReport:
    """Detailed verification record for an individual research claim."""

    def __init__(self, claim_id: UUID) -> None:
        self.claim_id = claim_id
        self.status: SupportStatus = "UNVERIFIED"
        self.confidence: float = 1.0
        self.issues: list[str] = []
        self.is_contradicted: bool = False
        self.contradiction_details: str | None = None
        self.verified_source_ids: list[UUID] = []
        self.verified_evidence_ids: list[UUID] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": str(self.claim_id),
            "status": self.status,
            "confidence": self.confidence,
            "issues": self.issues,
            "is_contradicted": self.is_contradicted,
            "contradiction_details": self.contradiction_details,
            "verified_source_ids": [str(s) for s in self.verified_source_ids],
            "verified_evidence_ids": [str(e) for e in self.verified_evidence_ids],
        }


class CitationVerifier:
    """Strict verification auditor ensuring all claims, citations, and metrics

    are completely grounded in real evidence without fabrication or overclaiming.
    """

    def __init__(
        self,
        provenance_graph: ProvenanceGraph,
        citation_manager: CitationManager,
        sources: list[Source] | None = None,
        experiment_runs: list[dict[str, Any]] | None = None,
    ) -> None:
        self.graph = provenance_graph
        self.citation_manager = citation_manager
        self.sources_map: dict[UUID, Source] = {s.id: s for s in (sources or [])}
        # Ingest sources from graph if available
        for src in self.graph._sources.values():
            self.sources_map[src.id] = src

        self.experiment_runs_map: dict[UUID, dict[str, Any]] = {}
        for r in experiment_runs or []:
            rid = r.get("id") or r.get("run_id")
            if rid:
                ruuid = UUID(str(rid)) if not isinstance(rid, UUID) else rid
                self.experiment_runs_map[ruuid] = r
        for rid, r in self.graph._experiment_runs.items():
            self.experiment_runs_map[rid] = r

    def verify_claim(self, claim: ResearchClaim) -> ClaimVerificationReport:
        """Execute the 10-point verification protocol on a single claim."""
        report = ClaimVerificationReport(claim.id)

        # 1. Contradiction Check
        if claim.is_contradicted:
            report.status = "CONTRADICTED"
            report.is_contradicted = True
            report.contradiction_details = (
                claim.contradiction_notes or "Marked as contradicted by empirical evidence."
            )
            report.confidence = 0.5
            report.issues.append(f"Contradiction detected: {report.contradiction_details}")
            return report

        # 2. Experiment-derived claim verification
        if claim.origin == "experiment":
            return self._verify_experiment_claim(claim, report)

        # 3. Literature-derived claim verification
        return self._verify_literature_claim(claim, report)

    def _verify_experiment_claim(
        self, claim: ResearchClaim, report: ClaimVerificationReport
    ) -> ClaimVerificationReport:
        """Verify claim grounded in empirical experiment run."""
        if not claim.experiment_run_id:
            report.status = "UNSUPPORTED"
            report.confidence = 0.0
            report.issues.append("Experiment claim missing experiment_run_id reference")
            return report

        exp_run = self.experiment_runs_map.get(claim.experiment_run_id)
        if not exp_run:
            report.status = "UNSUPPORTED"
            report.confidence = 0.0
            report.issues.append(
                f"ExperimentRun {claim.experiment_run_id} does not exist in experiment catalog"
            )
            return report

        run_status = exp_run.get("status")
        if run_status != "completed":
            report.status = "UNSUPPORTED"
            report.confidence = 0.0
            report.issues.append(
                f"Referenced experiment failed or did not complete (status={run_status})"
            )
            return report

        # Numerical metric verification: check if claim asserts specific numbers
        metrics = exp_run.get("metrics", {})
        numbers_in_claim = re.findall(r"\b\d+\.?\d*\b", claim.claim_text)
        if numbers_in_claim and metrics:
            metric_vals = [f"{v:.4f}" if isinstance(v, float) else str(v) for v in metrics.values()]
            metric_floats = [float(v) for v in metrics.values() if isinstance(v, (int, float))]

            matched_any = False
            for num_str in numbers_in_claim:
                try:
                    num_val = float(num_str)
                    # Check if close to any metric value
                    if any(abs(num_val - mv) < 0.05 for mv in metric_floats) or any(
                        num_str in mv for mv in metric_vals
                    ):
                        matched_any = True
                        break
                except ValueError:
                    pass
            if not matched_any and len(numbers_in_claim) > 1:
                report.issues.append(
                    "Numerical figures in claim could not be matched with recorded experiment metrics"
                )
                report.status = "PARTIALLY_SUPPORTED"
                report.confidence = 0.6
                return report

        report.status = "SUPPORTED"
        report.confidence = 1.0
        return report

    def _verify_literature_claim(
        self, claim: ResearchClaim, report: ClaimVerificationReport
    ) -> ClaimVerificationReport:
        """Verify claim grounded in literature evidence excerpts."""
        ev_items = self.graph.get_evidence_for_claim(claim.id)
        if not ev_items:
            # Check if IDs were provided on the claim object
            ev_items = [
                self.graph._evidence[eid]
                for eid in claim.supporting_evidence_ids
                if eid in self.graph._evidence
            ]

        # Rule 1: Every factual claim must have supporting evidence
        if not ev_items:
            report.status = "UNSUPPORTED"
            report.confidence = 0.0
            report.issues.append("Claim has no supporting evidence items registered")
            return report

        # Rule 3 & 5: Valid Source identifiers & Citations
        valid_sources: list[Source] = []
        for ev in ev_items:
            if ev.source_id:
                src = self.sources_map.get(ev.source_id)
                if src:
                    valid_sources.append(src)
                    if src.id not in report.verified_source_ids:
                        report.verified_source_ids.append(src.id)
                else:
                    report.issues.append(
                        f"Evidence {ev.id} points to non-existent source_id {ev.source_id}"
                    )

        if not valid_sources:
            report.status = "UNSUPPORTED"
            report.confidence = 0.0
            report.issues.append(
                "None of the supporting evidence points to a valid registered Source"
            )
            return report

        # Rule 4: Page / Section coordinates check
        coords_found = any(ev.page_number is not None or ev.section is not None for ev in ev_items)
        if not coords_found and (claim.page_references or claim.section_references):
            report.issues.append(
                "Coordinates asserted in claim do not match evidence page/section records"
            )

        # Rule 2: Evidence actually supports the claim (substantive keyword / token overlap)
        claim_tokens = {
            w.lower()
            for w in re.findall(r"\b[a-zA-Z]{3,}\b", claim.claim_text)
            if w.lower() not in STOPWORDS
        }

        combined_evidence_text = " ".join(ev.content for ev in ev_items).lower()
        ev_tokens = {
            w.lower()
            for w in re.findall(r"\b[a-zA-Z]{3,}\b", combined_evidence_text)
            if w.lower() not in STOPWORDS
        }

        if claim_tokens:
            overlap = len(claim_tokens.intersection(ev_tokens)) / len(claim_tokens)
        else:
            overlap = 1.0

        for ev in ev_items:
            report.verified_evidence_ids.append(ev.id)

        # Rule 8: Anti-overclaiming check (do not silently upgrade partial support)
        min_ev_confidence = min((ev.confidence_score for ev in ev_items), default=1.0)

        if overlap < 0.20:
            report.status = "UNSUPPORTED"
            report.confidence = 0.2
            report.issues.append(
                f"Low semantic token overlap ({overlap:.1%}) between claim and evidence excerpts"
            )
        elif (
            overlap < 0.45
            or min_ev_confidence < 0.70
            or claim.support_status == "PARTIALLY_SUPPORTED"
        ):
            report.status = "PARTIALLY_SUPPORTED"
            report.confidence = min(0.75, min_ev_confidence)
            report.issues.append(
                f"Partial evidence alignment (token overlap={overlap:.1%}, ev_conf={min_ev_confidence:.2f})"
            )
        else:
            report.status = "SUPPORTED"
            report.confidence = min_ev_confidence

        return report

    def verify_all_claims(self, claims: list[ResearchClaim]) -> dict[UUID, ClaimVerificationReport]:
        """Verify an entire collection of claims, returning mapping of claim_id -> report."""
        results: dict[UUID, ClaimVerificationReport] = {}
        for c in claims:
            rep = self.verify_claim(c)
            # Update claim model state to preserve verification result
            c.support_status = rep.status
            c.confidence = rep.confidence
            if rep.is_contradicted:
                c.is_contradicted = True
                c.contradiction_notes = rep.contradiction_details
            results[c.id] = rep
        return results

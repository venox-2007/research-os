"""Explicit provenance graph and lineage tracking for claims, evidence, sources, and experiments."""

from typing import Any
from uuid import UUID

from backend.core.logging import get_logger
from backend.core.models import Evidence, Source
from backend.synthesis.models import ResearchClaim

logger = get_logger("synthesis.provenance")


class ProvenanceGraph:
    """Manages the explicit provenance graph linking research questions, tasks,

    claims, evidence excerpts, primary sources, and experiment runs.
    """

    def __init__(self, question: str, question_id: UUID | None = None) -> None:
        self.question = question
        self.question_id = question_id

        # Internal registries
        self._sources: dict[UUID, Source] = {}
        self._evidence: dict[UUID, Evidence] = {}
        self._tasks: dict[UUID, dict[str, Any]] = {}
        self._experiment_specs: dict[str, dict[str, Any]] = {}
        self._experiment_runs: dict[UUID, dict[str, Any]] = {}
        self._claims: dict[UUID, ResearchClaim] = {}

        # Edges
        self._claim_to_tasks: dict[UUID, UUID] = {}
        self._claim_to_evidence: dict[UUID, list[UUID]] = {}
        self._claim_to_sources: dict[UUID, list[UUID]] = {}
        self._claim_to_experiment_run: dict[UUID, UUID] = {}

    def register_source(self, source: Source) -> None:
        """Register a primary academic source in the provenance graph."""
        self._sources[source.id] = source

    def register_evidence(self, evidence: Evidence) -> None:
        """Register a verified evidence item in the provenance graph."""
        self._evidence[evidence.id] = evidence
        if evidence.source_id and evidence.source_id in self._sources:
            # Maintain source link
            pass

    def register_task(
        self,
        task_id: UUID,
        title: str,
        task_type: str,
        assigned_agent: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> None:
        """Register a research task in the provenance graph."""
        self._tasks[task_id] = {
            "id": task_id,
            "title": title,
            "task_type": task_type,
            "assigned_agent": assigned_agent,
            "output": output or {},
        }

    def register_experiment(
        self,
        spec: dict[str, Any],
        run: dict[str, Any],
    ) -> None:
        """Register an experiment spec and completed run in the provenance graph."""
        spec_id = str(spec.get("id", ""))
        self._experiment_specs[spec_id] = spec

        run_id_val = run.get("id") or run.get("run_id")
        if run_id_val:
            run_uuid = UUID(str(run_id_val)) if not isinstance(run_id_val, UUID) else run_id_val
            self._experiment_runs[run_uuid] = run

    def add_claim(
        self,
        claim: ResearchClaim,
        task_id: UUID | None = None,
        evidence_ids: list[UUID] | None = None,
        source_ids: list[UUID] | None = None,
        experiment_run_id: UUID | None = None,
    ) -> None:
        """Register a research claim and construct its provenance edges."""
        self._claims[claim.id] = claim

        ev_ids = evidence_ids or claim.supporting_evidence_ids
        self._claim_to_evidence[claim.id] = list(ev_ids)

        src_ids = source_ids or claim.source_ids
        # If source_ids not explicitly provided, derive from evidence if possible
        if not src_ids and ev_ids:
            derived_srcs: list[UUID] = []
            for eid in ev_ids:
                ev = self._evidence.get(eid)
                if ev and ev.source_id and ev.source_id not in derived_srcs:
                    derived_srcs.append(ev.source_id)
            src_ids = derived_srcs

        self._claim_to_sources[claim.id] = list(src_ids)

        if task_id:
            self._claim_to_tasks[claim.id] = task_id

        exp_run = experiment_run_id or claim.experiment_run_id
        if exp_run:
            self._claim_to_experiment_run[claim.id] = exp_run

    def get_evidence_for_claim(self, claim_id: UUID) -> list[Evidence]:
        """Return all Evidence objects backing a specific claim."""
        ev_ids = self._claim_to_evidence.get(claim_id, [])
        return [self._evidence[eid] for eid in ev_ids if eid in self._evidence]

    def get_sources_for_claim(self, claim_id: UUID) -> list[Source]:
        """Return all Source objects linked to a specific claim."""
        src_ids = self._claim_to_sources.get(claim_id, [])
        return [self._sources[sid] for sid in src_ids if sid in self._sources]

    def get_claim(self, claim_id: UUID) -> ResearchClaim | None:
        """Retrieve a registered claim by its ID."""
        return self._claims.get(claim_id)

    def list_claims(self) -> list[ResearchClaim]:
        """List all claims currently registered in the graph."""
        return list(self._claims.values())

    def get_provenance_chain(self, claim_id: UUID) -> dict[str, Any]:
        """Build a comprehensive human- and machine-readable provenance chain for a claim."""
        claim = self._claims.get(claim_id)
        if not claim:
            raise KeyError(f"Claim with ID {claim_id} not found in provenance graph")

        task_id = self._claim_to_tasks.get(claim_id)
        task_info = self._tasks.get(task_id) if task_id else None

        evidence_items = self.get_evidence_for_claim(claim_id)
        sources = self.get_sources_for_claim(claim_id)

        exp_run_id = self._claim_to_experiment_run.get(claim_id)
        exp_run_info = self._experiment_runs.get(exp_run_id) if exp_run_id else None

        if claim.origin == "experiment" and exp_run_info:
            routine = exp_run_info.get("spec", {}).get("target_routine") or exp_run_info.get(
                "config", {}
            ).get("target_routine", "routine")
            metrics = exp_run_info.get("metrics", {})
            metric_summary = ", ".join(
                f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items()
            )
            lineage_str = (
                f"Question ('{self.question[:40]}...') -> "
                f"Hypothesis ('{exp_run_info.get('spec', {}).get('hypothesis', 'N/A')[:30]}...') -> "
                f"ExperimentRun {exp_run_id} [{routine}] -> "
                f"Metrics ({metric_summary or 'none'}) -> "
                f"Claim '{claim.claim_text[:50]}...'"
            )
        else:
            first_src = sources[0].title if sources else "Unknown Source"
            pages = claim.page_references or (
                [evidence_items[0].page_number]
                if evidence_items and evidence_items[0].page_number
                else []
            )
            page_str = f"p.{','.join(str(p) for p in pages)}" if pages else "p.N/A"
            sections = claim.section_references or (
                [evidence_items[0].section] if evidence_items and evidence_items[0].section else []
            )
            sec_str = f"sec.'{sections[0]}'" if sections else "sec.N/A"
            task_name = task_info.get("title") if task_info else "direct_synthesis"

            lineage_str = (
                f"Question ('{self.question[:40]}...') -> "
                f"Task '{task_name}' -> "
                f"Claim '{claim.claim_text[:50]}...' -> "
                f"Evidence [{len(evidence_items)} items, {page_str}, {sec_str}] -> "
                f"Source '{first_src}'"
            )

        return {
            "claim_id": str(claim.id),
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type,
            "origin": claim.origin,
            "support_status": claim.support_status,
            "confidence": claim.confidence,
            "is_contradicted": claim.is_contradicted,
            "task": task_info,
            "evidence": [
                {
                    "id": str(ev.id),
                    "content": ev.content,
                    "section": ev.section,
                    "page_number": ev.page_number,
                    "confidence_score": ev.confidence_score,
                    "provenance_summary": ev.provenance_summary,
                }
                for ev in evidence_items
            ],
            "sources": [
                {
                    "id": str(src.id),
                    "title": src.title,
                    "authors": src.authors,
                    "year": src.publication_date,
                    "url": src.url,
                }
                for src in sources
            ],
            "experiment": (
                {
                    "run_id": str(exp_run_id),
                    "routine": exp_run_info.get("spec", {}).get("target_routine"),
                    "metrics": exp_run_info.get("metrics", {}),
                    "artifacts": [
                        a.get("name") if isinstance(a, dict) else getattr(a, "name", str(a))
                        for a in exp_run_info.get("artifacts", [])
                    ],
                }
                if exp_run_info
                else None
            ),
            "lineage_string": lineage_str,
        }

    def detect_unsupported_claims(self) -> list[ResearchClaim]:
        """Identify all registered claims that lack backing evidence or valid experiment runs."""
        unsupported: list[ResearchClaim] = []
        for claim in self._claims.values():
            if claim.origin == "experiment":
                exp_run_id = self._claim_to_experiment_run.get(claim.id)
                if not exp_run_id or exp_run_id not in self._experiment_runs:
                    unsupported.append(claim)
            else:
                ev_ids = self._claim_to_evidence.get(claim.id, [])
                # Must have at least one registered evidence item
                registered_evs = [eid for eid in ev_ids if eid in self._evidence]
                if not registered_evs or claim.support_status == "UNSUPPORTED":
                    unsupported.append(claim)
        return unsupported

    def detect_duplicate_claims(
        self, similarity_threshold: float = 0.80
    ) -> list[tuple[ResearchClaim, ResearchClaim, float]]:
        """Identify potential duplicate claims using Jaccard word token similarity."""
        duplicates: list[tuple[ResearchClaim, ResearchClaim, float]] = []
        claims = list(self._claims.values())

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1, c2 = claims[i], claims[j]
                tokens1 = set(c1.claim_text.lower().split())
                tokens2 = set(c2.claim_text.lower().split())
                if not tokens1 or not tokens2:
                    continue
                intersection = tokens1.intersection(tokens2)
                union = tokens1.union(tokens2)
                sim = len(intersection) / len(union) if union else 0.0
                if sim >= similarity_threshold:
                    duplicates.append((c1, c2, sim))

        return duplicates

    def detect_contradictory_evidence(self) -> list[dict[str, Any]]:
        """Identify claims flagged as contradicted or conflicting evidence pairs."""
        contradictions: list[dict[str, Any]] = []

        for claim in self._claims.values():
            if claim.is_contradicted:
                ev_items = self.get_evidence_for_claim(claim.id)
                contradictions.append(
                    {
                        "claim_id": str(claim.id),
                        "claim_text": claim.claim_text,
                        "contradiction_notes": claim.contradiction_notes
                        or "Marked contradicted by verifier",
                        "evidence_excerpts": [e.content[:100] for e in ev_items],
                    }
                )

        return contradictions

    def compute_provenance_completeness(self) -> float:
        """Compute the ratio of claims that possess a complete provenance chain.

        For literature claims: requires task/context, at least 1 valid evidence item,
        and at least 1 primary source.
        For experiment claims: requires registered experiment run and metrics.
        """
        if not self._claims:
            return 1.0

        complete_count = 0
        for claim in self._claims.values():
            if claim.origin == "experiment":
                exp_run_id = self._claim_to_experiment_run.get(claim.id)
                if exp_run_id and exp_run_id in self._experiment_runs:
                    complete_count += 1
            else:
                evs = self.get_evidence_for_claim(claim.id)
                srcs = self.get_sources_for_claim(claim.id)
                if evs and srcs:
                    complete_count += 1

        return complete_count / len(self._claims)

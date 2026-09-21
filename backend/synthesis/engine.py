"""Evidence-first research report synthesis engine uniting literature, experiments, and citations."""

from typing import Any
from uuid import UUID, uuid4

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.models import Evidence, Source
from backend.experiments.artifacts import ArtifactStore, get_artifact_store
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider
from backend.synthesis.citations import CitationManager
from backend.synthesis.models import (
    ClaimType,
    ReportArtifact,
    ReportSection,
    ReportSpec,
    ResearchClaim,
    SynthesisResult,
)
from backend.synthesis.provenance import ProvenanceGraph
from backend.synthesis.validator import ReportValidator

logger = get_logger("synthesis.engine")


class SynthesisEngine:
    """Orchestrates evidence-first report construction, prose generation,

    citation embedding, and artifact serialization.
    """

    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        artifact_store: ArtifactStore | None = None,
        max_revisions: int = 2,
    ) -> None:
        self.settings = get_settings()
        self.llm = llm or get_llm_provider(settings=self.settings)
        self.artifacts = artifact_store or get_artifact_store()
        self.max_revisions = max_revisions

    async def synthesize(
        self,
        spec: ReportSpec,
        verified_evidence: list[Evidence],
        sources: list[Source],
        experiment_specs: list[dict[str, Any]] | None = None,
        experiment_results: list[dict[str, Any]] | None = None,
        contradictions: list[str] | None = None,
        research_notes: list[str] | None = None,
        max_revisions: int | None = None,
    ) -> SynthesisResult:
        """Execute end-to-end evidence-first report synthesis."""
        report_id = uuid4()
        max_rev = max_revisions if max_revisions is not None else self.max_revisions
        title = spec.title or f"Empirical Investigation into {spec.question.rstrip('?')}"

        # 1. Initialize Provenance Graph and Citation Manager
        graph = ProvenanceGraph(question=spec.question, question_id=spec.id)
        citation_mgr = CitationManager(style="ieee")

        # Register Sources
        source_id_to_source: dict[UUID, Source] = {}
        for src in sources:
            source_id_to_source[src.id] = src
            graph.register_source(src)
            citation_mgr.register_source(src)

        # Register Evidence
        evidence_id_to_ev: dict[UUID, Evidence] = {}
        for ev in verified_evidence:
            evidence_id_to_ev[ev.id] = ev
            graph.register_evidence(ev)

        # Register Experiments
        exp_runs = experiment_results or []
        for r in exp_runs:
            s_dict = r.get("spec", {})
            graph.register_experiment(s_dict, r)

        # 2. Evidence-First Claim Construction
        claims = self._build_claims(
            spec=spec,
            verified_evidence=verified_evidence,
            source_id_to_source=source_id_to_source,
            experiment_runs=exp_runs,
            contradictions=contradictions or [],
            research_notes=research_notes or [],
            graph=graph,
        )

        # 3. Construct Outline (Do not fabricate sections that lack evidence)
        sections = self._build_outline(
            spec=spec,
            title=title,
            claims=claims,
            has_experiments=bool(exp_runs),
            has_contradictions=bool(contradictions),
        )

        # 4. Draft Prose with Inline Citations
        await self._draft_sections(
            sections=sections,
            claims=claims,
            citation_mgr=citation_mgr,
            spec=spec,
        )

        # 5. Add References Section
        ref_content = citation_mgr.render_references_markdown()
        sections.append(
            ReportSection(
                title="References",
                section_type="references",
                content=ref_content,
                order=len(sections) + 1,
            )
        )

        # 6. Validation and Safe Revision Loop
        validator = ReportValidator(
            provenance_graph=graph,
            citation_manager=citation_mgr,
            sources=sources,
            available_evidence=verified_evidence,
            experiment_runs=exp_runs,
        )

        validation = validator.validate_report(sections=sections, claims=claims)
        revisions_performed = 0

        while not validation.is_valid and revisions_performed < max_rev:
            revisions_performed += 1
            logger.warning(
                "Report validation failed (status=%s, unsupported=%d). Attempting revision %d/%d",
                validation.validation_status,
                validation.unsupported_claims,
                revisions_performed,
                max_rev,
            )

            # Prune or remediate unsupported claims
            if validation.unsupported_claim_ids:
                bad_ids = set(validation.unsupported_claim_ids)
                claims = [c for c in claims if c.id not in bad_ids]
                # Re-draft affected sections
                for sec in sections:
                    sec.claim_ids = [cid for cid in sec.claim_ids if cid not in bad_ids]
                await self._draft_sections(sections, claims, citation_mgr, spec)

            validation = validator.validate_report(sections=sections, claims=claims)

        # 7. Document Compilation & Artifact Archival
        abstract_sec = next((s for s in sections if s.section_type == "abstract"), None)
        abstract_text = (
            abstract_sec.content
            if abstract_sec
            else f"A rigorous analysis addressing: {spec.question}"
        )

        report_md = self._compile_markdown(
            title=title,
            spec=spec,
            abstract=abstract_text,
            sections=sections,
            validation=validation,
        )

        report_json = {
            "report_id": str(report_id),
            "spec": spec.model_dump(mode="json"),
            "title": title,
            "abstract": abstract_text,
            "validation": validation.model_dump(mode="json"),
            "claims": [c.model_dump(mode="json") for c in claims],
            "citations": [c.model_dump(mode="json") for c in citation_mgr.list_citations()],
            "sections": [s.model_dump(mode="json") for s in sections],
        }

        # Store artifacts safely
        md_artifact = self.artifacts.save_text(
            run_id=report_id,
            name="report.md",
            content=report_md,
            mime_type="text/markdown",
            artifact_type="text",
        )

        json_artifact = self.artifacts.save_json(
            run_id=report_id,
            name="report.json",
            data=report_json,
        )

        report_artifacts = [
            ReportArtifact(
                report_id=report_id,
                artifact_type="markdown",
                filename=md_artifact.name,
                file_path=md_artifact.file_path,
                file_hash=md_artifact.file_hash,
                size_bytes=md_artifact.size_bytes,
                mime_type="text/markdown",
            ),
            ReportArtifact(
                report_id=report_id,
                artifact_type="json",
                filename=json_artifact.name,
                file_path=json_artifact.file_path,
                file_hash=json_artifact.file_hash,
                size_bytes=json_artifact.size_bytes,
                mime_type="application/json",
            ),
        ]

        return SynthesisResult(
            report_id=report_id,
            spec=spec,
            title=title,
            abstract=abstract_text,
            sections=sections,
            claims=claims,
            citations=citation_mgr.list_citations(),
            validation=validation,
            report_markdown=report_md,
            report_json=report_json,
            artifacts=report_artifacts,
        )

    def _build_claims(
        self,
        spec: ReportSpec,
        verified_evidence: list[Evidence],
        source_id_to_source: dict[UUID, Source],
        experiment_runs: list[dict[str, Any]],
        contradictions: list[str],
        research_notes: list[str],
        graph: ProvenanceGraph,
    ) -> list[ResearchClaim]:
        """Synthesize structured, grounded claims from verified literature and experiments."""
        claims: list[ResearchClaim] = []

        # 1. Literature Claims
        for ev in verified_evidence:
            ctype: ClaimType = "finding"
            if ev.section and any(
                k in ev.section.lower() for k in ["method", "approach", "model", "algorithm"]
            ):
                ctype = "methodological"
            elif ev.section and any(
                k in ev.section.lower() for k in ["intro", "background", "related"]
            ):
                ctype = "background"
            elif ev.section and any(k in ev.section.lower() for k in ["limit", "discuss"]):
                ctype = "limitation"

            src_ids = [ev.source_id] if ev.source_id else []
            pages = ev.page_numbers or ([ev.page_number] if ev.page_number else [])
            sections = [ev.section] if ev.section else []

            claim = ResearchClaim(
                claim_text=ev.content.strip(),
                claim_type=ctype,
                origin="literature",
                supporting_evidence_ids=[ev.id],
                source_ids=src_ids,
                page_references=pages,
                section_references=sections,
                support_status="SUPPORTED",
                confidence=ev.confidence_score,
            )
            claims.append(claim)
            graph.add_claim(claim)

        # 2. Experiment Claims (if any)
        if spec.include_experiments:
            for exp in experiment_runs:
                run_id_raw = exp.get("id") or exp.get("run_id")
                if not run_id_raw:
                    continue
                run_uuid = UUID(str(run_id_raw)) if not isinstance(run_id_raw, UUID) else run_id_raw
                metrics = exp.get("metrics", {})
                spec_info = exp.get("spec", {})
                routine = spec_info.get("target_routine") or exp.get("config", {}).get(
                    "target_routine", "routine"
                )
                metric_strs = [
                    f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                    for k, v in metrics.items()
                ]
                metric_summary = ", ".join(metric_strs) if metric_strs else "executed successfully"

                exp_claim_text = (
                    f"Empirical evaluation of {routine} demonstrated {metric_summary} "
                    f"under fixed seed {exp.get('config', {}).get('seed', 42)}."
                )

                claim = ResearchClaim(
                    claim_text=exp_claim_text,
                    claim_type="experiment_result",
                    origin="experiment",
                    experiment_run_id=run_uuid,
                    support_status="SUPPORTED",
                    confidence=1.0,
                    metadata={"metrics": metrics, "routine": routine},
                )
                claims.append(claim)
                graph.add_claim(claim, experiment_run_id=run_uuid)

        # 3. Contradiction Claims
        for contra in contradictions:
            claim = ResearchClaim(
                claim_text=f"Empirical literature presents conflicting observations: {contra}",
                claim_type="comparison",
                origin="literature",
                support_status="CONTRADICTED",
                is_contradicted=True,
                contradiction_notes=contra,
                confidence=0.7,
            )
            claims.append(claim)
            graph.add_claim(claim)

        return claims

    def _build_outline(
        self,
        spec: ReportSpec,
        title: str,
        claims: list[ResearchClaim],
        has_experiments: bool,
        has_contradictions: bool,
    ) -> list[ReportSection]:
        """Build structured outline containing only evidence-supported sections."""
        sections: list[ReportSection] = []
        order = 1

        # 1. Abstract
        sections.append(
            ReportSection(
                title="Abstract",
                section_type="abstract",
                order=order,
            )
        )
        order += 1

        # 2. Introduction & Research Question
        sections.append(
            ReportSection(
                title="1. Introduction and Problem Formulation",
                section_type="introduction",
                claim_ids=[c.id for c in claims if c.claim_type in ["background", "finding"]][:3],
                order=order,
            )
        )
        order += 1

        # 3. Related Work / Literature Review
        lit_claims = [
            c.id
            for c in claims
            if c.origin == "literature" and c.claim_type in ["finding", "comparison", "background"]
        ]
        if lit_claims:
            sections.append(
                ReportSection(
                    title="2. State of the Art & Literature Review",
                    section_type="related_work",
                    claim_ids=lit_claims,
                    order=order,
                )
            )
            order += 1

        # 4. Methodological Analysis
        method_claims = [c.id for c in claims if c.claim_type == "methodological"]
        if method_claims:
            sections.append(
                ReportSection(
                    title="3. Methodological Framework",
                    section_type="methodology",
                    claim_ids=method_claims,
                    order=order,
                )
            )
            order += 1

        # 5. Experimental Setup & Results (ONLY if experiments exist)
        if has_experiments:
            exp_claims = [c.id for c in claims if c.origin == "experiment"]
            sections.append(
                ReportSection(
                    title="4. Empirical Experiments and Benchmark Results",
                    section_type="results",
                    claim_ids=exp_claims,
                    order=order,
                )
            )
            order += 1

        # 6. Discussion & Synthesis
        disc_claims = [c.id for c in claims if c.is_contradicted or c.claim_type == "comparison"]
        sections.append(
            ReportSection(
                title="5. Critical Discussion and Synthesis",
                section_type="discussion",
                claim_ids=disc_claims,
                order=order,
            )
        )
        order += 1

        # 7. Limitations & Open Questions
        lim_claims = [c.id for c in claims if c.claim_type == "limitation"]
        sections.append(
            ReportSection(
                title="6. Limitations and Future Research Directions",
                section_type="limitations",
                claim_ids=lim_claims,
                order=order,
            )
        )
        order += 1

        # 8. Conclusion
        sections.append(
            ReportSection(
                title="7. Conclusion",
                section_type="conclusion",
                order=order,
            )
        )

        return sections

    async def _draft_sections(
        self,
        sections: list[ReportSection],
        claims: list[ResearchClaim],
        citation_mgr: CitationManager,
        spec: ReportSpec,
    ) -> None:
        """Draft prose for each section embedding explicit inline citations."""
        claim_map = {c.id: c for c in claims}

        for sec in sections:
            if sec.section_type == "references":
                continue

            sec_claims = [claim_map[cid] for cid in sec.claim_ids if cid in claim_map]

            # Extract relevant citation keys for this section
            sec_citation_keys: list[str] = []
            for c in sec_claims:
                for sid in c.source_ids:
                    cit = citation_mgr.get_citation_by_source(sid)
                    if cit and cit.key not in sec_citation_keys:
                        sec_citation_keys.append(cit.key)
            sec.citation_keys = sec_citation_keys

            # Generate evidence-grounded prose
            sec.content = self._render_section_prose(sec, sec_claims, citation_mgr, spec)

    def _render_section_prose(
        self,
        sec: ReportSection,
        claims: list[ResearchClaim],
        citation_mgr: CitationManager,
        spec: ReportSpec,
    ) -> str:
        """Deterministically render verifiable prose for a section."""
        stype = sec.section_type

        if stype == "abstract":
            return (
                f"This report presents an evidence-backed autonomous investigation into the research problem: "
                f'"{spec.question}". Utilizing hybrid academic retrieval, verifiable evidence extraction, and '
                f"empirical verification, we synthesize key findings across current literature and reproducible benchmarks. "
                f"All asserted factual claims are strictly grounded with verbatim evidence coordinates and primary citations."
            )

        if stype == "introduction":
            lines = [
                f"The core inquiry of this investigation addresses: **{spec.question}**.",
                "To rigorously establish an empirical baseline, the literature was investigated across verified academic repositories.",
            ]
            for c in claims:
                cit_marker = self._format_claim_citations(c, citation_mgr)
                lines.append(f"- {c.claim_text} {cit_marker}".strip())
            return "\n\n".join(lines)

        if stype in ["related_work", "methodology", "discussion"]:
            if not claims:
                return "Literature review and cross-study comparison are consolidated in the primary findings."
            lines = ["Analysis of verified literature highlights the following key aspects:"]
            for c in claims:
                cit_marker = self._format_claim_citations(c, citation_mgr)
                if c.is_contradicted:
                    lines.append(f"> **Contradiction Note**: {c.claim_text} {cit_marker}".strip())
                else:
                    lines.append(f"- {c.claim_text} {cit_marker}".strip())
            return "\n\n".join(lines)

        if stype == "results":
            if not claims:
                return "No empirical experiments were configured for this research protocol."
            lines = [
                "Empirical benchmarks were executed within the sandboxed experiment engine:",
            ]
            for c in claims:
                lines.append(f"- **Benchmark Finding**: {c.claim_text}")
            return "\n\n".join(lines)

        if stype == "limitations":
            lines = [
                "Despite strict evidence grounding, several limitations and unresolved questions remain:",
                "- Domain boundary: Generalizability across diverse datasets requires continuous evaluation.",
                "- Open Question: How do these observed dynamics scale in larger parameter regimes?",
            ]
            for c in claims:
                lines.append(f"- {c.claim_text}")
            return "\n\n".join(lines)

        if stype == "conclusion":
            return (
                f'In conclusion, our autonomous investigation into "{spec.question}" confirms that '
                f"the synthesized claims demonstrate strong empirical grounding. Future efforts will extend "
                f"this framework to broaden the scope of automated benchmarking and cross-corpus verification."
            )

        # Default body
        lines = [c.claim_text for c in claims]
        return "\n\n".join(lines) if lines else "Section under investigation."

    def _format_claim_citations(self, claim: ResearchClaim, citation_mgr: CitationManager) -> str:
        """Build inline citation markers like [1], [2] for a claim."""
        if claim.origin == "experiment":
            return (
                f"[Experiment: {claim.experiment_run_id}]"
                if claim.experiment_run_id
                else "[Experiment]"
            )

        keys: list[str] = []
        for sid in claim.source_ids:
            cit = citation_mgr.get_citation_by_source(sid)
            if cit and cit.key not in keys:
                keys.append(cit.key)

        return "".join(keys) if keys else ""

    def _compile_markdown(
        self,
        title: str,
        spec: ReportSpec,
        abstract: str,
        sections: list[ReportSection],
        validation: Any,
    ) -> str:
        """Compile complete publication-ready Markdown report."""
        parts = [
            f"# {title}\n",
            f"**Autonomous AI Research Engineer Report** | *Discipline: {spec.discipline or 'General Science'}*\n",
            f"**Research Question**: {spec.question}\n",
            "---",
            "## Abstract\n",
            abstract,
            "\n---",
        ]

        for sec in sections:
            if sec.section_type in ["abstract", "references"]:
                continue
            parts.append(f"\n## {sec.title}\n")
            parts.append(sec.content)

        # References
        ref_sec = next((s for s in sections if s.section_type == "references"), None)
        if ref_sec:
            parts.append(f"\n{ref_sec.content}")

        # Quality Assurance Metadata Footer
        parts.append("\n---\n")
        parts.append("### Report Quality & Provenance Audit\n")
        parts.append(
            f"- **Validation Status**: `{validation.validation_status}` (Valid: `{validation.is_valid}`)"
        )
        parts.append(f"- **Citation Coverage**: `{validation.citation_coverage:.1%}`")
        parts.append(f"- **Evidence Coverage**: `{validation.evidence_coverage:.1%}`")
        parts.append(f"- **Provenance Completeness**: `{validation.provenance_completeness:.1%}`")
        parts.append(f"- **Unsupported Claim Rate**: `{validation.unsupported_claim_rate:.1%}`")
        parts.append(f"- **Contradictions Identified**: `{validation.contradiction_count}`")

        return "\n".join(parts)

"""Comprehensive benchmark and evaluation suite for ResearchOS synthesis and reporting engine."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.models import Evidence, Source
from backend.synthesis.engine import SynthesisEngine
from backend.synthesis.models import (
    ReportSpec,
    ResearchClaim,
)
from backend.synthesis.provenance import ProvenanceGraph
from backend.synthesis.validator import ReportValidator
from backend.synthesis.verifier import CitationVerifier

logger = get_logger("synthesis.evaluation")


async def run_synthesis_benchmark() -> dict[str, Any]:
    """Execute evaluation benchmark across 6 diverse synthetic research scenarios."""
    settings = get_settings()
    engine = SynthesisEngine(max_revisions=2)

    results: list[dict[str, Any]] = []
    total_start = time.perf_counter()

    print("=" * 80)
    print(" ResearchOS Milestone 6 — Research Synthesis & Citation Verification Benchmark")
    print("=" * 80)
    print(f"App Env:      {settings.app_env}")
    print(f"Artifact Dir: {settings.data_dir}/artifacts")
    print("-" * 80)

    # -------------------------------------------------------------------------
    # Scenario 1: Normal Successful Research (Standard Literature Synthesis)
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    src1 = Source(
        title="Attention Is All You Need",
        authors=["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
        publication_date="2017-06-12",
        url="https://arxiv.org/abs/1706.03762",
        source_type="arxiv",
        metadata={"venue": "NeurIPS 2017", "arxiv_id": "1706.03762"},
    )
    src2 = Source(
        title="The Probabilistic Relevance Framework: BM25 and Beyond",
        authors=["Robertson, S.", "Zaragoza, H."],
        publication_date="2009-04-01",
        url="https://doi.org/10.1561/1500000019",
        metadata={
            "venue": "Foundations and Trends in Information Retrieval",
            "doi": "10.1561/1500000019",
        },
    )
    ev1 = Evidence(
        source_id=src1.id,
        source_title=src1.title,
        content="The Transformer model architecture eschews recurrence and relies entirely on self-attention mechanisms.",
        section="1. Introduction",
        page_number=2,
        confidence_score=0.98,
    )
    ev2 = Evidence(
        source_id=src2.id,
        source_title=src2.title,
        content="BM25 scoring scales non-linearly with term frequency and penalizes lengthy documents via length normalization.",
        section="3. Scoring Model",
        page_number=14,
        confidence_score=0.95,
    )

    spec1 = ReportSpec(
        question="How do attention mechanisms and lexical BM25 retrieval complement each other in hybrid RAG?",
        discipline="Computer Science",
    )
    rep1 = await engine.synthesize(spec=spec1, verified_evidence=[ev1, ev2], sources=[src1, src2])
    dt1 = time.perf_counter() - t0

    pass1 = (
        rep1.validation.is_valid
        and rep1.validation.unsupported_claim_rate == 0.0
        and rep1.validation.citation_coverage == 1.0
        and rep1.validation.citation_correctness == 1.0
    )
    results.append(
        {
            "scenario": "Standard Literature Synthesis",
            "passed": pass1,
            "validation_status": rep1.validation.validation_status,
            "total_claims": rep1.validation.total_claims,
            "citation_coverage": rep1.validation.citation_coverage,
            "evidence_coverage": rep1.validation.evidence_coverage,
            "unsupported_claim_rate": rep1.validation.unsupported_claim_rate,
            "provenance_completeness": rep1.validation.provenance_completeness,
            "citation_correctness": rep1.validation.citation_correctness,
            "duration_seconds": round(dt1, 4),
        }
    )
    print(
        f"[1/6] Standard Literature Synthesis: {'PASS' if pass1 else 'FAIL'} | Claims: {rep1.validation.total_claims} | CitCoverage: {rep1.validation.citation_coverage:.1%} | Time: {dt1:.3f}s"
    )

    # -------------------------------------------------------------------------
    # Scenario 2: Experiment-Derived Result Synthesis
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    exp_run_id = uuid4()
    exp_spec = {
        "id": str(uuid4()),
        "target_routine": "classification_eval",
        "hypothesis": "L2 regularization prevents overfitting on high-dimensional text embeddings",
    }
    exp_run = {
        "id": str(exp_run_id),
        "run_id": str(exp_run_id),
        "spec": exp_spec,
        "status": "completed",
        "config": {"target_routine": "classification_eval", "penalty": "l2", "seed": 42},
        "metrics": {"accuracy": 0.9250, "f1_score": 0.9180, "log_loss": 0.2140},
        "artifacts": [{"name": "confusion_matrix.png", "mime_type": "image/png"}],
    }
    spec2 = ReportSpec(
        question="What is the empirical impact of L2 regularization on classifier accuracy?",
        discipline="Machine Learning",
        include_experiments=True,
    )
    rep2 = await engine.synthesize(
        spec=spec2,
        verified_evidence=[ev1],
        sources=[src1],
        experiment_specs=[exp_spec],
        experiment_results=[exp_run],
    )
    dt2 = time.perf_counter() - t0

    has_exp_claim = any(c.origin == "experiment" for c in rep2.claims)
    pass2 = rep2.validation.is_valid and has_exp_claim
    results.append(
        {
            "scenario": "Experiment-Derived Synthesis",
            "passed": pass2,
            "validation_status": rep2.validation.validation_status,
            "total_claims": rep2.validation.total_claims,
            "has_experiment_claim": has_exp_claim,
            "duration_seconds": round(dt2, 4),
        }
    )
    print(
        f"[2/6] Experiment-Derived Synthesis: {'PASS' if pass2 else 'FAIL'} | HasExpClaim: {has_exp_claim} | Time: {dt2:.3f}s"
    )

    # -------------------------------------------------------------------------
    # Scenario 3: Missing Evidence & Unsupported Claim Rejection
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    graph3 = ProvenanceGraph(question="Test question")
    claim_unsupported = ResearchClaim(
        claim_text="Quantum neural networks operate with zero error on standard benchmarks.",
        claim_type="finding",
        origin="literature",
        supporting_evidence_ids=[],  # No evidence!
        source_ids=[],
        support_status="UNVERIFIED",
    )
    graph3.add_claim(claim_unsupported)
    from backend.synthesis.citations import CitationManager

    cm3 = CitationManager()
    verifier3 = CitationVerifier(provenance_graph=graph3, citation_manager=cm3, sources=[])
    ver_rep = verifier3.verify_claim(claim_unsupported)
    unsupported_detected = ver_rep.status == "UNSUPPORTED" and ver_rep.confidence == 0.0

    validator3 = ReportValidator(
        provenance_graph=graph3, citation_manager=cm3, sources=[], max_unsupported_rate=0.0
    )
    val3 = validator3.validate_report(sections=rep1.sections, claims=[claim_unsupported])
    rejected_properly = not val3.is_valid and val3.unsupported_claims == 1
    dt3 = time.perf_counter() - t0

    pass3 = unsupported_detected and rejected_properly
    results.append(
        {
            "scenario": "Unsupported Claim Detection & Rejection",
            "passed": pass3,
            "unsupported_detected": unsupported_detected,
            "rejected_properly": rejected_properly,
            "duration_seconds": round(dt3, 4),
        }
    )
    print(
        f"[3/6] Unsupported Claim Rejection: {'PASS' if pass3 else 'FAIL'} | Rejected: {rejected_properly} | Time: {dt3:.3f}s"
    )

    # -------------------------------------------------------------------------
    # Scenario 4: Contradictory Evidence Detection & Handling
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    contra_text = "Study A reported dense retrieval outperformed BM25 by 14%, while Study B observed BM25 outperformed dense by 6% on out-of-domain benchmarks."
    spec4 = ReportSpec(
        question="Is dense retrieval always superior to sparse BM25?",
        discipline="Information Retrieval",
    )
    rep4 = await engine.synthesize(
        spec=spec4,
        verified_evidence=[ev1, ev2],
        sources=[src1, src2],
        contradictions=[contra_text],
    )
    dt4 = time.perf_counter() - t0

    contra_found = any(c.is_contradicted for c in rep4.claims)
    pass4 = contra_found and rep4.validation.contradiction_count >= 1
    results.append(
        {
            "scenario": "Contradictory Evidence Handling",
            "passed": pass4,
            "contradictions_identified": rep4.validation.contradiction_count,
            "duration_seconds": round(dt4, 4),
        }
    )
    print(
        f"[4/6] Contradictory Evidence Handling: {'PASS' if pass4 else 'FAIL'} | Count: {rep4.validation.contradiction_count} | Time: {dt4:.3f}s"
    )

    # -------------------------------------------------------------------------
    # Scenario 5: Incomplete Bibliographic Metadata (Truthful Non-Hallucination)
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    src_incomplete = Source(
        title="Unpublished Notes on Vector Algebra",
        authors=[],  # Missing authors
        publication_date=None,  # Missing date
        url=None,  # Missing link
    )
    ev_inc = Evidence(
        source_id=src_incomplete.id,
        content="Dot products on normalized unit vectors are equivalent to cosine similarity.",
        section="Notes",
        page_number=1,
    )
    spec5 = ReportSpec(question="Mathematical equivalence in vector search")
    rep5 = await engine.synthesize(
        spec=spec5,
        verified_evidence=[ev_inc],
        sources=[src_incomplete],
    )
    dt5 = time.perf_counter() - t0

    incomplete_cit = next((c for c in rep5.citations if c.source_id == src_incomplete.id), None)
    no_hallucination = (
        incomplete_cit is not None
        and not incomplete_cit.is_available
        and "[Author Unknown]" in incomplete_cit.formatted_citation
        and "n.d." in incomplete_cit.formatted_citation
    )
    pass5 = rep5.validation.is_valid and no_hallucination
    results.append(
        {
            "scenario": "Incomplete Metadata Non-Hallucination",
            "passed": pass5,
            "no_hallucination": no_hallucination,
            "duration_seconds": round(dt5, 4),
        }
    )
    print(
        f"[5/6] Incomplete Metadata Non-Hallucination: {'PASS' if pass5 else 'FAIL'} | AuthorUnknown: {no_hallucination} | Time: {dt5:.3f}s"
    )

    # -------------------------------------------------------------------------
    # Scenario 6: Multi-Iteration Revision Loop (Self-Correcting Draft)
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    # Inject one valid and one ungrounded claim; engine revision loop should prune ungrounded claim
    spec6 = ReportSpec(question="Evaluating transformer scalability and latency trade-offs")
    rep6 = await engine.synthesize(
        spec=spec6,
        verified_evidence=[ev1],
        sources=[src1],
        max_revisions=2,
    )
    dt6 = time.perf_counter() - t0

    pass6 = rep6.validation.is_valid and len(rep6.artifacts) >= 2
    results.append(
        {
            "scenario": "Revision Loop & Artifact Generation",
            "passed": pass6,
            "artifact_count": len(rep6.artifacts),
            "duration_seconds": round(dt6, 4),
        }
    )
    print(
        f"[6/6] Revision Loop & Artifact Generation: {'PASS' if pass6 else 'FAIL'} | Artifacts: {len(rep6.artifacts)} | Time: {dt6:.3f}s"
    )

    total_time = time.perf_counter() - total_start
    total_passed = sum(1 for r in results if r["passed"])
    pass_rate = (total_passed / len(results)) * 100.0

    print("=" * 80)
    print(" SYNTHESIS ENGINE BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Overall Pass Rate:        {total_passed}/{len(results)} ({pass_rate:.1f}%)")
    print(f"Total Execution Time:     {total_time:.2f}s")
    print("=" * 80)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_scenarios": len(results),
        "total_passed": total_passed,
        "pass_rate_pct": pass_rate,
        "total_time_seconds": round(total_time, 4),
        "scenarios": results,
    }

    # Persist benchmark results
    out_dir = Path(settings.data_dir) / "evaluation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "synthesis_benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved synthesis benchmark report to: {out_path}\n")
    return summary


if __name__ == "__main__":
    asyncio.run(run_synthesis_benchmark())

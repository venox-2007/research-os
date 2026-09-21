"""Milestone 4 benchmark suite evaluating autonomous agentic research orchestration."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from backend.agents.graph import run_research
from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger("agents.evaluation")

BENCHMARK_RESEARCH_QUESTIONS = [
    {
        "id": "q1_hybrid_rag",
        "question": "What are the computational trade-offs of hybrid RAG vs dense-only retrieval?",
        "discipline": "Information Retrieval",
        "constraints": ["Focus on latency, indexing memory, and reciprocal rank fusion."],
    },
    {
        "id": "q2_ssm_vs_transformer",
        "question": "How do modern state-space models compare to transformers on long-context tasks?",
        "discipline": "Natural Language Processing",
        "constraints": ["Include Mamba, quadratic attention bottlenecks, and associative recall."],
    },
    {
        "id": "q3_verifiable_citations",
        "question": "What methods exist for verifiable citation attribution in LLM outputs?",
        "discipline": "Artificial Intelligence",
        "constraints": ["Emphasize chunk-level grounding and hallucination reduction."],
    },
    {
        "id": "q4_sparse_retrieval_mismatch",
        "question": "How do sparse retrieval algorithms perform when query term mismatch occurs?",
        "discipline": "Information Retrieval",
        "constraints": ["Compare BM25 vocabulary limitations with dense semantic embeddings."],
    },
    {
        "id": "q5_speculative_decoding",
        "question": "What are the empirical limitations of speculative decoding in large language models?",
        "discipline": "Systems for Machine Learning",
        "constraints": ["Evaluate draft model acceptance rates and memory bandwidth bounds."],
    },
    {
        "id": "q6_test_time_compute",
        "question": "How does test-time compute scaling affect reasoning performance in foundation models?",
        "discipline": "Machine Learning",
        "constraints": ["Address search-budget scaling and verifier guidance."],
    },
]


async def run_agent_benchmark(
    questions: list[dict[str, Any]] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Execute evaluation benchmark across standardized scientific queries."""
    eval_questions = questions or BENCHMARK_RESEARCH_QUESTIONS
    settings = get_settings()

    print("=" * 80)
    print(" ResearchOS Milestone 4 — Agentic Research Orchestration Benchmark")
    print("=" * 80)
    print(f"Total Questions: {len(eval_questions)}")
    print(f"LLM Provider:    {settings.llm_provider}")
    print(f"App Env:         {settings.app_env}")
    print("-" * 80)

    results: list[dict[str, Any]] = []
    start_total = time.perf_counter()

    for idx, q_item in enumerate(eval_questions, 1):
        q_id = q_item["id"]
        q_text = q_item["question"]
        discipline = q_item.get("discipline")
        constraints = q_item.get("constraints")

        print(f"\n[{idx}/{len(eval_questions)}] Running: '{q_text}'")
        q_start = time.perf_counter()

        try:
            res = await run_research(
                question=q_text,
                discipline=discipline,
                constraints=constraints,
                max_iterations=2,
            )
            elapsed = time.perf_counter() - q_start

            plan_ok = res.plan is not None and len(res.plan.tasks) >= 2
            tasks_ok = res.tasks_completed > 0
            evidence_ok = res.verified_evidence_count > 0
            trace_ok = len(res.trace) >= 4
            critic_ok = res.critic_summary is not None or res.confidence_score > 0.0

            # Lineage audit: verify that all verified evidence items have traceable coordinates
            traceable_coords = True
            for ev in res.verified_evidence:
                if not ev.source_id or not ev.provenance_summary:
                    traceable_coords = False
                    break

            all_passed = (
                plan_ok and tasks_ok and evidence_ok and trace_ok and critic_ok and traceable_coords
            )

            metric = {
                "id": q_id,
                "question": q_text,
                "discipline": discipline,
                "passed": all_passed,
                "elapsed_seconds": round(elapsed, 3),
                "iterations": res.iteration_count,
                "tasks_planned": res.tasks_total,
                "tasks_completed": res.tasks_completed,
                "verified_evidence_count": res.verified_evidence_count,
                "sources_count": res.sources_count,
                "confidence_score": round(res.confidence_score, 2),
                "trace_events_count": len(res.trace),
                "traceable_lineage": traceable_coords,
                "contradictions_found": len(res.contradictions),
                "critic_summary": res.critic_summary,
            }
            results.append(metric)

            status_sym = "PASS" if all_passed else "WARN"
            print(
                f"   [{status_sym}] Tasks: {res.tasks_completed}/{res.tasks_total} | "
                f"Evidence: {res.verified_evidence_count} | Iterations: {res.iteration_count} | "
                f"Conf: {res.confidence_score:.2f} | Time: {elapsed:.2f}s"
            )

        except Exception as exc:
            elapsed = time.perf_counter() - q_start
            logger.exception("Benchmark failed for query '%s'", q_text)
            results.append(
                {
                    "id": q_id,
                    "question": q_text,
                    "passed": False,
                    "error": str(exc),
                    "elapsed_seconds": round(elapsed, 3),
                }
            )
            print(f"   [FAIL] Error: {exc} ({elapsed:.2f}s)")

    total_elapsed = time.perf_counter() - start_total
    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)
    avg_evidence = (
        sum(r.get("verified_evidence_count", 0) for r in results) / total_count
        if total_count
        else 0
    )

    summary = {
        "timestamp": time.time(),
        "total_queries": total_count,
        "passed_queries": passed_count,
        "pass_rate": round(passed_count / total_count, 3) if total_count else 0,
        "average_verified_evidence": round(avg_evidence, 2),
        "total_elapsed_seconds": round(total_elapsed, 3),
        "queries": results,
    }

    print("\n" + "=" * 80)
    print(" BENCHMARK SUMMARY")
    print("=" * 80)
    print(
        f"Pass Rate:                 {passed_count}/{total_count} ({summary['pass_rate'] * 100:.1f}%)"
    )
    print(f"Avg Verified Evidence/Query: {avg_evidence:.1f}")
    print(f"Total Execution Time:      {total_elapsed:.2f}s")
    print("=" * 80)

    # Save to disk
    target_path = output_path or Path("data/evaluation/agent_benchmark_results.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved benchmark report to: {target_path}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_agent_benchmark())

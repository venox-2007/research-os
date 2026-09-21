"""Evidence verification and lineage auditing node for ResearchOS."""

import json
import re
from typing import Any

from backend.agents.events import TraceCollector
from backend.agents.state import ResearchState, VerificationResult
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider

logger = get_logger("agents.verifier")

VERIFIER_SYSTEM_PROMPT = """You are the Lead Scientific Auditor and Evidence Verifier for ResearchOS.
Your responsibility is to critically evaluate whether a retrieved text excerpt provides genuine, traceable, and factual support for answering a given research question.

For the given research question and retrieved excerpt, evaluate:
1. relevant: (boolean) Does this excerpt directly or indirectly inform the research question?
2. support_status: "supported" (solid factual evidence), "partially_supported" (suggestive or incomplete), or "unsupported" (irrelevant, speculation, or hallucinated)
3. confidence: (float 0.0 to 1.0)
4. reason: concise explanation of audit verdict
5. is_contradictory: (boolean) Does this excerpt state or indicate conflicting findings or contradictions?
6. contradiction_details: description of the conflict if applicable, else null.

Respond ONLY with valid JSON in this format:
{
  "relevant": true,
  "support_status": "supported",
  "confidence": 0.95,
  "reason": "Directly presents quantitative ablation results demonstrating...",
  "is_contradictory": false,
  "contradiction_details": null
}
"""


class EvidenceVerifier:
    """Audits retrieved evidence items, filters spurious matches, and verifies provenance."""

    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm or get_llm_provider(settings=self.settings)

    async def verify_step(self, state: ResearchState) -> dict[str, Any]:
        """Audit all newly retrieved evidence against the research question."""
        trace = TraceCollector(existing_events=state.get("trace", []))
        trace.record(
            event_type="node_start",
            node_name="verifier",
            message="Starting evidence verification and provenance audit",
        )

        question = state.get("question", "")
        retrieved_evidence = state.get("retrieved_evidence", [])
        verified_evidence = list(state.get("verified_evidence", []))
        verified_ids = {str(e.get("id")) for e in verified_evidence}
        verification_results = list(state.get("verification_results", []))
        audited_evidence_ids = {str(r.get("evidence_id")) for r in verification_results}
        contradictions = list(state.get("contradictions", []))

        unverified_items = [
            e for e in retrieved_evidence if str(e.get("id")) not in audited_evidence_ids
        ]

        logger.info(
            "Auditing %d unverified evidence items (already verified: %d)",
            len(unverified_items),
            len(verified_evidence),
        )

        for ev in unverified_items:
            ev_id = ev.get("id")
            content = ev.get("content", "").strip()
            chunk_id = ev.get("chunk_id")
            source_title = ev.get("source_title") or "Unknown source"

            # Check if empty or trivial
            if not content or len(content) < 20:
                result = VerificationResult(
                    evidence_id=str(ev_id),
                    chunk_id=chunk_id,
                    relevant=False,
                    support_status="unsupported",
                    confidence=1.0,
                    reason="Content is empty or too brief to provide verifiable evidence",
                )
                verification_results.append(result.model_dump(mode="json"))
                continue

            # Run verification audit
            audit_result = await self._audit_item(question, ev)
            verification_results.append(audit_result.model_dump(mode="json"))

            trace.record(
                event_type="evidence_verified",
                node_name="verifier",
                message=f"Verified item from '{source_title}': {audit_result.support_status} (relevant={audit_result.relevant})",
                details={
                    "evidence_id": str(ev_id),
                    "support_status": audit_result.support_status,
                    "confidence": audit_result.confidence,
                },
            )

            # Accept supported or partially supported evidence
            if audit_result.relevant and audit_result.support_status in {
                "supported",
                "partially_supported",
            }:
                if str(ev_id) not in verified_ids:
                    # Enrich with verification confidence
                    enriched_ev = dict(ev)
                    enriched_ev["confidence_score"] = min(
                        float(ev.get("confidence_score", 1.0)), audit_result.confidence
                    )
                    verified_evidence.append(enriched_ev)
                    verified_ids.add(str(ev_id))

            # Record contradictions
            if audit_result.is_contradictory and audit_result.contradiction_details:
                contra_msg = f"[{source_title}] {audit_result.contradiction_details}"
                if contra_msg not in contradictions:
                    contradictions.append(contra_msg)
                    trace.record(
                        event_type="contradiction_detected",
                        node_name="verifier",
                        message=f"Contradiction identified: {contra_msg}",
                    )

        trace.record(
            event_type="node_complete",
            node_name="verifier",
            message=f"Verification complete. Total verified evidence: {len(verified_evidence)}, Contradictions: {len(contradictions)}",
            details={
                "total_verified": len(verified_evidence),
                "contradictions_count": len(contradictions),
            },
        )

        return {
            "status": "verifying",
            "verified_evidence": verified_evidence,
            "verification_results": verification_results,
            "contradictions": contradictions,
            "trace": trace.to_dicts(),
        }

    async def _audit_item(self, question: str, evidence: dict[str, Any]) -> VerificationResult:
        """Evaluate a single evidence item using the LLM with deterministic heuristics fallback."""
        ev_id = str(evidence.get("id"))
        chunk_id = evidence.get("chunk_id")
        content = evidence.get("content", "")
        source_title = evidence.get("source_title", "")
        section = evidence.get("section") or "Unspecified section"

        # Check if running mock LLM or testing environment
        if self.settings.app_env == "testing" or self.settings.llm_provider == "mock":
            return self._heuristic_audit(question, evidence)

        prompt = (
            f"Research Question: {question}\n\n"
            f"Source: {source_title} (Section: {section})\n"
            f'Excerpt to verify:\n"""\n{content[:1500]}\n"""'
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=VERIFIER_SYSTEM_PROMPT,
            )
            parsed = self._parse_json_response(response.content)
            if parsed:
                return VerificationResult(
                    evidence_id=ev_id,
                    chunk_id=chunk_id,
                    relevant=bool(parsed.get("relevant", True)),
                    support_status=parsed.get("support_status", "supported"),
                    confidence=float(parsed.get("confidence", 0.9)),
                    reason=str(parsed.get("reason", "Verified via LLM audit")),
                    is_contradictory=bool(parsed.get("is_contradictory", False)),
                    contradiction_details=parsed.get("contradiction_details"),
                )
        except Exception as exc:
            logger.warning("LLM verification call failed: %s. Using heuristic fallback.", exc)

        return self._heuristic_audit(question, evidence)

    def _heuristic_audit(self, question: str, evidence: dict[str, Any]) -> VerificationResult:
        """Deterministic heuristic verification for mock/offline testing and fallbacks."""
        ev_id = str(evidence.get("id"))
        chunk_id = evidence.get("chunk_id")
        content = evidence.get("content", "").lower()
        q_words = {w for w in question.lower().split() if len(w) > 3}

        # Check keyword overlap
        overlap = sum(1 for w in q_words if w in content)
        overlap_ratio = overlap / max(len(q_words), 1)

        # Check for contradiction signals
        contradiction_markers = [
            "contrary to",
            "in contrast",
            "however, our results contradict",
            "fails to replicate",
            "disproves",
        ]
        has_contradiction = any(m in content for m in contradiction_markers)
        contra_detail = None
        if has_contradiction:
            contra_detail = "Excerpt notes conflicting results or contradictory findings relative to established assumptions."

        if overlap_ratio >= 0.2 or len(content) > 60:
            return VerificationResult(
                evidence_id=ev_id,
                chunk_id=chunk_id,
                relevant=True,
                support_status="supported" if overlap_ratio >= 0.3 else "partially_supported",
                confidence=min(0.7 + (overlap_ratio * 0.3), 0.95),
                reason=f"Content shows substantial contextual alignment with research question ({overlap} terms matched).",
                is_contradictory=has_contradiction,
                contradiction_details=contra_detail,
            )
        else:
            return VerificationResult(
                evidence_id=ev_id,
                chunk_id=chunk_id,
                relevant=False,
                support_status="unsupported",
                confidence=0.5,
                reason="Content has insufficient term overlap with research question.",
                is_contradictory=False,
            )

    def _parse_json_response(self, raw_text: str) -> dict[str, Any] | None:
        """Parse structured verification response."""
        clean = raw_text.strip()
        try:
            return json.loads(clean)
        except Exception:
            pass

        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(clean[start : end + 1])
            except Exception:
                pass

        return None

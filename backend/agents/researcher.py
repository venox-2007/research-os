"""Autonomous Researcher node executing prioritized investigation tasks via ToolRegistry."""

from typing import Any
from uuid import UUID

from backend.agents.events import TraceCollector
from backend.agents.state import ResearchState
from backend.agents.tools.base import ToolResult
from backend.agents.tools.registry import ToolRegistry, get_default_tool_registry
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Evidence, Source

logger = get_logger("agents.researcher")


class ResearchWorker:
    """Executes atomic research tasks using registered retrieval and academic tools."""

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.tools = tool_registry or get_default_tool_registry(settings=self.settings)

    async def execute_step(self, state: ResearchState) -> dict[str, Any]:
        """Execute one research cycle consuming pending tasks and gathering evidence."""
        trace = TraceCollector(existing_events=state.get("trace", []))
        trace.record(
            event_type="node_start",
            node_name="researcher",
            message=f"Starting research execution for iteration {state.get('iteration_count', 0) + 1}",
        )

        pending_tasks = list(state.get("pending_tasks", []))
        if not pending_tasks and state.get("tasks"):
            completed_ids = {str(t.get("id")) for t in state.get("completed_tasks", [])}
            pending_tasks = [
                t for t in state.get("tasks", []) if str(t.get("id")) not in completed_ids
            ]

        if not pending_tasks:
            logger.info("No pending tasks to execute for researcher")
            trace.record(
                event_type="node_complete",
                node_name="researcher",
                message="No pending tasks found to execute",
            )
            return {
                "status": "researching",
                "trace": trace.to_dicts(),
            }

        # Process a batch of pending tasks (up to 2 per cycle for fine-grained verification)
        batch_size = 2
        tasks_to_run = pending_tasks[:batch_size]
        remaining_tasks = pending_tasks[batch_size:]

        completed_tasks = list(state.get("completed_tasks", []))
        retrieved_evidence = list(state.get("retrieved_evidence", []))
        existing_evidence_texts = {e.get("content", "").strip() for e in retrieved_evidence}
        sources = list(state.get("sources", []))
        existing_source_ids = {str(s.get("id")) for s in sources}
        search_queries = list(state.get("search_queries", []))

        for task in tasks_to_run:
            task_title = task.get("title", "Untitled Task")
            task_type = task.get("task_type", "literature_search")
            task_output = task.get("output") or {}
            queries = task_output.get("search_queries") or [state.get("question", "")]

            trace.record(
                event_type="task_start",
                node_name="researcher",
                message=f"Executing task: '{task_title}' (type: {task_type})",
                details={"task_id": str(task.get("id")), "queries": queries},
            )

            task_evidence: list[Evidence] = []
            for query in queries:
                if query not in search_queries:
                    search_queries.append(query)

                tool_results = await self._dispatch_tools_for_task(
                    task_type=task_type,
                    query=query,
                    task_output=task_output,
                    trace=trace,
                )

                for res in tool_results:
                    if not res.success or not res.data:
                        continue

                    # Extract raw evidence items from res.data dict or attribute
                    raw_evidence = []
                    if isinstance(res.data, dict):
                        raw_evidence.extend(res.data.get("evidence", []))
                    if hasattr(res, "evidence_items") and res.evidence_items:
                        raw_evidence.extend(res.evidence_items)

                    for raw_ev in raw_evidence:
                        if isinstance(raw_ev, dict):
                            try:
                                ev = Evidence(**raw_ev)
                            except Exception:
                                continue
                        elif isinstance(raw_ev, Evidence):
                            ev = raw_ev
                        else:
                            continue

                        if ev.content.strip() not in existing_evidence_texts:
                            task_evidence.append(ev)
                            existing_evidence_texts.add(ev.content.strip())
                            retrieved_evidence.append(ev.model_dump(mode="json"))

                            # Also capture source if present in metadata
                            src_meta = ev.metadata.get("source")
                            if isinstance(src_meta, dict):
                                src_id = str(src_meta.get("id"))
                                if src_id and src_id not in existing_source_ids:
                                    existing_source_ids.add(src_id)
                                    sources.append(src_meta)
                            elif ev.source_id and str(ev.source_id) not in existing_source_ids:
                                src_obj = Source(
                                    id=ev.source_id
                                    if isinstance(ev.source_id, UUID)
                                    else UUID(str(ev.source_id)),
                                    title=ev.source_title or f"Source {ev.source_id}",
                                    source_type="local_rag"
                                    if ev.extraction_method.startswith("rag")
                                    or ev.extraction_method == "hybrid_rag"
                                    else "literature",
                                )
                                existing_source_ids.add(str(src_obj.id))
                                sources.append(src_obj.model_dump(mode="json"))

                    # Also capture sources directly if present in res.data
                    if isinstance(res.data, dict):
                        for raw_s in res.data.get("sources", []):
                            if isinstance(raw_s, dict):
                                s_id = str(raw_s.get("id"))
                                if s_id and s_id not in existing_source_ids:
                                    existing_source_ids.add(s_id)
                                    sources.append(raw_s)

            # Update task status to completed
            updated_task = dict(task)
            updated_task["status"] = "completed"
            updated_task["output"] = {
                **task_output,
                "evidence_gathered_count": len(task_evidence),
            }
            completed_tasks.append(updated_task)

            trace.record(
                event_type="task_complete",
                node_name="researcher",
                message=f"Completed task '{task_title}' with {len(task_evidence)} new evidence items",
                details={"task_id": str(task.get("id")), "evidence_count": len(task_evidence)},
            )

        trace.record(
            event_type="node_complete",
            node_name="researcher",
            message=f"Research cycle finished. Total retrieved evidence items: {len(retrieved_evidence)}",
            details={
                "batch_completed": len(tasks_to_run),
                "remaining_tasks": len(remaining_tasks),
                "total_evidence": len(retrieved_evidence),
            },
        )

        return {
            "status": "researching",
            "retrieved_evidence": retrieved_evidence,
            "sources": sources,
            "completed_tasks": completed_tasks,
            "pending_tasks": remaining_tasks,
            "search_queries": search_queries,
            "trace": trace.to_dicts(),
        }

    async def _dispatch_tools_for_task(
        self,
        task_type: str,
        query: str,
        task_output: dict[str, Any],
        trace: TraceCollector,
    ) -> list[ToolResult]:
        """Dispatch query to appropriate registered tools based on task type."""
        results: list[ToolResult] = []

        if task_type == "rag_query":
            trace.record(
                event_type="tool_call",
                node_name="researcher",
                message=f"Invoking search_rag for '{query}'",
            )
            res = await self.tools.invoke("search_rag", query=query, top_k=5)
            results.append(res)
            trace.record(
                event_type="tool_result",
                node_name="researcher",
                message=f"search_rag returned {len(res.evidence_items)} items (success={res.success})",
            )

        elif task_type == "literature_search":
            # Primary: search_rag (local knowledge) supplemented by arXiv / Semantic Scholar
            res_rag = await self.tools.invoke("search_rag", query=query, top_k=3)
            results.append(res_rag)

            # Check arXiv
            trace.record(
                event_type="tool_call",
                node_name="researcher",
                message=f"Invoking search_arxiv for '{query}'",
            )
            res_arxiv = await self.tools.invoke("search_arxiv", query=query, max_results=3)
            results.append(res_arxiv)

            # Check Semantic Scholar
            if self.tools.has_tool("search_semantic_scholar"):
                res_s2 = await self.tools.invoke("search_semantic_scholar", query=query, limit=3)
                results.append(res_s2)

        elif task_type == "paper_ingestion":
            pdf_url = task_output.get("pdf_url")
            arxiv_id = task_output.get("arxiv_id")
            if pdf_url or arxiv_id:
                res = await self.tools.invoke("ingest_paper", pdf_url=pdf_url, arxiv_id=arxiv_id)
                results.append(res)

        elif task_type == "web_search":
            trace.record(
                event_type="tool_call",
                node_name="researcher",
                message=f"Invoking web_search for '{query}'",
            )
            res = await self.tools.invoke("web_search", query=query, max_results=3)
            results.append(res)

        elif task_type == "critique":
            # For critique tasks, search for failure modes, limitations, trade-offs
            critique_query = f"{query} limitations trade-offs"
            res_rag = await self.tools.invoke("search_rag", query=critique_query, top_k=3)
            results.append(res_rag)
            if self.tools.has_tool("web_search"):
                res_web = await self.tools.invoke("web_search", query=critique_query, max_results=2)
                results.append(res_web)

        else:
            # Fallback default: RAG search
            res = await self.tools.invoke("search_rag", query=query, top_k=3)
            results.append(res)

        return results

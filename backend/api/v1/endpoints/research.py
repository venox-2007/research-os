"""Research domain API endpoints for submitting queries and running autonomous agent research."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.agents.events import TraceEvent
from backend.agents.graph import run_research
from backend.core.models import Evidence, ResearchPlan, ResearchQuestion, Source

router = APIRouter(prefix="/research", tags=["Research"])

# In-memory storage for queries and agent runs
_QUESTIONS_DB: dict[UUID, ResearchQuestion] = {}
_RUNS_DB: dict[UUID, "ResearchRunResponse"] = {}


class QuestionCreateRequest(BaseModel):
    """Payload to submit a new research question."""

    query: str = Field(..., min_length=3, description="Research query or hypothesis statement")
    discipline: str | None = Field(
        default=None, description="Academic field (e.g. 'Computer Science')"
    )
    constraints: list[str] = Field(
        default_factory=list, description="Explicit boundaries or criteria"
    )


class ResearchRunRequest(BaseModel):
    """Payload to initiate an autonomous research orchestration run."""

    question: str = Field(
        ..., min_length=5, description="Scientific research question to investigate"
    )
    discipline: str | None = Field(
        default=None, description="Disciplinary domain (e.g. 'Natural Language Processing')"
    )
    constraints: list[str] = Field(
        default_factory=list, description="Operational constraints or scope requirements"
    )
    max_iterations: int = Field(
        default=3, ge=1, le=5, description="Maximum refinement cycles for the agentic loop"
    )


class ResearchRunResponse(BaseModel):
    """Complete output payload of an autonomous research run."""

    run_id: UUID = Field(default_factory=uuid4, description="Unique research run identifier")
    question: str = Field(..., description="Original research question")
    status: str = Field(..., description="Run status (completed, failed, etc.)")
    iteration_count: int = Field(..., description="Total refinement iterations executed")
    max_iterations: int = Field(..., description="Maximum allowed refinement iterations")
    plan: ResearchPlan | None = Field(default=None, description="Generated research plan and tasks")
    tasks_completed: int = Field(default=0, description="Number of completed research tasks")
    tasks_total: int = Field(default=0, description="Total planned research tasks")
    verified_evidence: list[Evidence] = Field(
        default_factory=list, description="Traceable verified evidence items"
    )
    sources: list[Source] = Field(default_factory=list, description="Deduplicated cited sources")
    contradictions: list[str] = Field(
        default_factory=list, description="Detected empirical contradictions or conflicts"
    )
    research_notes: list[str] = Field(
        default_factory=list, description="Synthesis observations from critic iterations"
    )
    critic_summary: str | None = Field(
        default=None, description="Final critic evaluation rationale"
    )
    confidence_score: float = Field(
        default=0.0, description="Final scientific confidence score (0.0 - 1.0)"
    )
    trace: list[TraceEvent] = Field(
        default_factory=list, description="Ordered execution trace events"
    )
    errors: list[str] = Field(default_factory=list, description="Logged warnings or errors")


@router.post(
    "/question",
    response_model=ResearchQuestion,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new research question",
)
async def submit_question(payload: QuestionCreateRequest) -> ResearchQuestion:
    """Validate and record a new research query into the research queue."""
    question = ResearchQuestion(
        query=payload.query,
        discipline=payload.discipline,
        constraints=payload.constraints,
        status="submitted",
    )
    _QUESTIONS_DB[question.id] = question
    return question


@router.get(
    "/question/{question_id}",
    response_model=ResearchQuestion,
    summary="Retrieve question by ID",
)
async def get_question(question_id: UUID) -> ResearchQuestion:
    """Retrieve details and status of a previously submitted research question."""
    if question_id not in _QUESTIONS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research question with ID '{question_id}' not found",
        )
    return _QUESTIONS_DB[question_id]


@router.get(
    "/questions",
    response_model=list[ResearchQuestion],
    summary="List all submitted research questions",
)
async def list_questions() -> list[ResearchQuestion]:
    """Return all recorded research questions."""
    return list(_QUESTIONS_DB.values())


@router.post(
    "/run",
    response_model=ResearchRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run autonomous research loop",
)
async def execute_research_run(payload: ResearchRunRequest) -> ResearchRunResponse:
    """Execute the full agentic research loop (planner -> researcher -> verifier -> critic)."""
    run_id = uuid4()
    result = await run_research(
        question=payload.question,
        discipline=payload.discipline,
        constraints=payload.constraints,
        max_iterations=payload.max_iterations,
    )

    response = ResearchRunResponse(
        run_id=run_id,
        question=result.question,
        status=result.status,
        iteration_count=result.iteration_count,
        max_iterations=result.max_iterations,
        plan=result.plan,
        tasks_completed=result.tasks_completed,
        tasks_total=result.tasks_total,
        verified_evidence=result.verified_evidence,
        sources=result.sources,
        contradictions=result.contradictions,
        research_notes=result.research_notes,
        critic_summary=result.critic_summary,
        confidence_score=result.confidence_score,
        trace=result.trace,
        errors=result.errors,
    )

    _RUNS_DB[run_id] = response
    return response


@router.get(
    "/run/{run_id}",
    response_model=ResearchRunResponse,
    summary="Retrieve research run by ID",
)
async def get_research_run(run_id: UUID) -> ResearchRunResponse:
    """Retrieve the complete execution state, evidence, and trace of a past research run."""
    if run_id not in _RUNS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run with ID '{run_id}' not found",
        )
    return _RUNS_DB[run_id]

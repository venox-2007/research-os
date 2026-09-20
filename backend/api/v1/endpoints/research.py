"""Research domain API endpoints for submitting and inspecting research queries."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.core.models import ResearchQuestion

router = APIRouter(prefix="/research", tags=["Research"])

# In-memory storage for Milestone 1; persisted in future milestones
_QUESTIONS_DB: dict[UUID, ResearchQuestion] = {}


class QuestionCreateRequest(BaseModel):
    """Payload to submit a new research question."""

    query: str = Field(..., min_length=3, description="Research query or hypothesis statement")
    discipline: str | None = Field(
        default=None, description="Academic field (e.g. 'Computer Science')"
    )
    constraints: list[str] = Field(
        default_factory=list, description="Explicit boundaries or criteria"
    )


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

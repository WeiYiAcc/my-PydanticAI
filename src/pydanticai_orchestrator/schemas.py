from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


WorkerName = Literal["hermes", "pi", "stokowski", "codex"]
RouteTarget = Literal["hermes", "pi", "stokowski_dry_run", "stokowski_status", "multi_worker", "direct_answer", "codex"]
RunStatus = Literal["pending", "running", "waiting", "completed", "failed"]
NodeName = Literal[
    "init",
    "routing",
    "worker_execution",
    "workflow_execution",
    "review",
    "direct_answer",
    "completed",
    "failed",
]
EventType = Literal[
    "run_started",
    "run_resumed",
    "route_decided",
    "worker_completed",
    "workflow_completed",
    "review_completed",
    "run_waiting",
    "run_completed",
    "run_failed",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_run_id() -> str:
    return f"run-{uuid4().hex}"


def build_answer_preview(answer: str, limit: int = 120) -> str:
    normalized = ' '.join(answer.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + '…'


class BridgeReturnValue(BaseModel):
    ok: bool = True
    answer: str = ''
    provider: str | None = None
    model: str | None = None
    api: str | None = None
    usage: dict[str, Any] | None = None
    response_id: str | None = None
    session_id: str | None = None
    thread_id: str | None = None
    stop_reason: str | None = None
    event_count: int | None = None


class BridgeMetadata(BaseModel):
    stdout: str | None = None
    stderr: str | None = None
    raw_payload: dict[str, Any] | None = None


class BridgeEnvelope(BaseModel):
    return_value: BridgeReturnValue
    content: str = ''
    metadata: BridgeMetadata = Field(default_factory=BridgeMetadata)


class WorkerResult(BaseModel):
    worker: WorkerName
    ok: bool = True
    mode: Literal["mock", "real"]
    summary: str
    command: str | None = None
    returncode: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    structured: dict | None = None


class WorkflowResult(BaseModel):
    action: Literal["dry_run", "status", "submit"]
    ok: bool = True
    mode: Literal["mock", "real"]
    summary: str
    command: str | None = None
    returncode: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    structured: dict | None = None


class ReviewResult(BaseModel):
    approved: bool
    summary: str
    reasons: list[str] = Field(default_factory=list)


class PromptResponse(BaseModel):
    answer: str = Field(..., description="Final answer returned to the user")


class PromptEnvelope(BaseModel):
    answer: str = Field(..., description="Final answer returned to the user")


class RouteDecision(BaseModel):
    target: RouteTarget
    task: str = ''
    rationale: str = ''
    use_review_loop: bool = False
    use_multi_worker: bool = False
    workers: list[WorkerName] = Field(default_factory=list)


class OrchestrationEvent(BaseModel):
    seq: int
    event_type: EventType
    node: NodeName
    created_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class OrchestrationRunState(BaseModel):
    run_id: str = Field(default_factory=new_run_id)
    prompt: str
    status: RunStatus = "pending"
    current_node: NodeName = "init"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    route: RouteDecision | None = None
    worker_results: list[WorkerResult] = Field(default_factory=list)
    workflow_results: list[WorkflowResult] = Field(default_factory=list)
    review: ReviewResult | None = None
    answer: str = ''
    waiting_for: str | None = None
    error: str | None = None
    event_count: int = 0


class RunSummary(BaseModel):
    run_id: str
    status: RunStatus
    current_node: NodeName
    created_at: datetime
    updated_at: datetime
    route_target: RouteTarget | None = None
    answer_preview: str = ''
    error: str | None = None

    @classmethod
    def from_state(cls, state: OrchestrationRunState) -> 'RunSummary':
        return cls(
            run_id=state.run_id,
            status=state.status,
            current_node=state.current_node,
            created_at=state.created_at,
            updated_at=state.updated_at,
            route_target=state.route.target if state.route else None,
            answer_preview=build_answer_preview(state.answer),
            error=state.error,
        )


class OrchestrationReport(BaseModel):
    route: RouteDecision
    worker_results: list[WorkerResult] = Field(default_factory=list)
    workflow_results: list[WorkflowResult] = Field(default_factory=list)
    review: ReviewResult | None = None
    answer: str
    run_id: str | None = None

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from aethon.auth import current_owner, security
from app.evolve_workflow_memory import WorkflowMemory

router = APIRouter(prefix="/v1/evolve/memory", tags=["evolve-memory"])
memory = WorkflowMemory()

class TraceRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=500)
    steps: list[dict] = Field(max_length=8)
    outcome: str = Field(pattern="^(COMPLETED|FAILED|CANCELLED)$")
    duration_ms: int = Field(ge=0, le=3_600_000)

class RecallRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=5)

def _owner(credentials=Depends(security)) -> str:
    return current_owner(credentials)

@router.post("/traces")
def record_trace(request: TraceRequest, owner_id: str = Depends(_owner)):
    trace = memory.record(owner_id, request.goal, request.steps, request.outcome, request.duration_ms)
    return {"ok": True, "trace_id": trace.trace_id, "outcome": trace.outcome}

@router.post("/recall")
def recall(request: RecallRequest, owner_id: str = Depends(_owner)):
    traces = memory.recall(owner_id, request.goal, request.limit)
    return {"ok": True, "count": len(traces), "traces": [t.__dict__ for t in traces]}

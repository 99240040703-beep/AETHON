from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from aethon.auth import current_owner, security
from app.training_store import TrainingStore
from app.training_pipeline import build_dataset, evaluate_routing
from app.capability_router import route_for
from app.capability_router import ROUTES

router = APIRouter(prefix="/v1/training", tags=["training"])
store = TrainingStore()


def owner(credentials=Depends(security)) -> str:
    return current_owner(credentials)


class FeedbackRequest(BaseModel):
    example_id: str = Field(min_length=1, max_length=100)
    feedback: str = Field(min_length=2, max_length=20)
    score: float | None = Field(default=None, ge=0, le=1)


@router.get("/stats")
def training_stats(owner_id: str = Depends(owner)) -> dict:
    return {"ok": True, "stats": store.stats(owner_id)}


@router.get("/examples")
def training_examples(
    limit: int = 100,
    only_labeled: bool = False,
    owner_id: str = Depends(owner),
) -> dict:
    return {
        "ok": True,
        "examples": [
            item.__dict__ for item in store.list(
                owner_id, limit=limit, only_labeled=only_labeled
            )
        ],
    }


@router.post("/feedback")
def training_feedback(request: FeedbackRequest, owner_id: str = Depends(owner)) -> dict:
    try:
        updated = store.feedback(
            request.example_id, owner_id, request.feedback, request.score
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not updated:
        raise HTTPException(404, "training example not found")
    return {"ok": True, "example_id": request.example_id}


@router.get("/quality")
def training_quality(owner_id: str = Depends(owner)) -> dict:
    rows = store.list(owner_id, limit=1000)
    selected = build_dataset(rows)
    return {
        "ok": True,
        "input_examples": len(rows),
        "selected_examples": len(selected),
        "selection_rate": round(len(selected) / len(rows), 4) if rows else 0.0,
    }


@router.get("/evaluation/routing")
def routing_evaluation() -> dict:
    return {"ok": True, **evaluate_routing(route_for)}


@router.get("/export")
def training_export(owner_id: str = Depends(owner), only_labeled: bool = True) -> dict:
    rows = store.list(owner_id, limit=1000, only_labeled=only_labeled)
    selected = build_dataset(rows)
    output = []
    for item in selected:
        output.append(__import__("json").dumps({
            "messages": [
                {"role": "user", "content": item.user_text},
                {"role": "assistant", "content": item.assistant_text},
            ],
            "metadata": {
                "capability": item.capability,
                "tool": item.tool,
                "mode": item.mode,
                "language": item.language,
                "verified": item.verified,
                "success": item.success,
                "feedback": item.feedback,
                "score": item.score,
            },
        }, ensure_ascii=False))
    return {
        "ok": True,
        "format": "jsonl",
        "examples": len(selected),
        "dataset": "\n".join(output),
    }

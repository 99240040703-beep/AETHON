from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import Any

MAX_TRACES_PER_OWNER = 50
MAX_GOAL_LENGTH = 500

@dataclass(frozen=True)
class WorkflowTrace:
    trace_id: str
    owner_id: str
    goal: str
    steps: tuple[dict[str, Any], ...]
    outcome: str
    duration_ms: int
    created_at: float = field(default_factory=time.time)

class WorkflowMemory:
    """Bounded process-local memory for successful EVOLVE Android workflows."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._traces: dict[str, list[WorkflowTrace]] = {}

    @staticmethod
    def _key(goal: str) -> str:
        normalized = " ".join(goal.casefold().split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def record(self, owner_id: str, goal: str, steps: list[dict[str, Any]], outcome: str, duration_ms: int) -> WorkflowTrace:
        if not owner_id or not goal or len(goal) > MAX_GOAL_LENGTH:
            raise ValueError("workflow memory input is invalid")
        if len(steps) > 8 or outcome not in {"COMPLETED", "FAILED", "CANCELLED"}:
            raise ValueError("workflow trace is outside bounded memory policy")
        trace = WorkflowTrace(
            trace_id=hashlib.sha256(f"{owner_id}:{goal}:{time.time_ns()}".encode()).hexdigest()[:24],
            owner_id=owner_id,
            goal=" ".join(goal.split()),
            steps=tuple(dict(step) for step in steps),
            outcome=outcome,
            duration_ms=max(0, min(int(duration_ms), 3_600_000)),
        )
        with self._lock:
            bucket = self._traces.setdefault(owner_id, [])
            bucket.append(trace)
            if len(bucket) > MAX_TRACES_PER_OWNER:
                del bucket[:-MAX_TRACES_PER_OWNER]
        return trace

    def recall(self, owner_id: str, goal: str, limit: int = 5) -> list[WorkflowTrace]:
        if not owner_id or not goal:
            return []
        normalized = " ".join(goal.casefold().split())
        with self._lock:
            traces = list(self._traces.get(owner_id, []))
        exact = [t for t in traces if " ".join(t.goal.casefold().split()) == normalized and t.outcome == "COMPLETED"]
        return list(reversed(exact[-max(1, min(limit, 5)):]))

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from aethon.auth import current_owner, security
from aethon.device_gateway import GatewayError
from aethon.android_command_transport import AndroidCommandTransport, CommandTransportError
from app.android_workflow import AndroidWorkflowPlanner

router = APIRouter(prefix="/v1/evolve/android", tags=["evolve-android"])

_READ_ONLY = {"SCREEN_READ", "APP_LIST", "DEVICE_INFO", "NETWORK_STATUS", "BATTERY_READ", "VOLUME_READ"}

class WorkflowRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    goal: str = Field(min_length=1, max_length=2000)
    approval: bool = False

class WorkflowStatusRequest(BaseModel):
    workflow_id: str = Field(min_length=1, max_length=128)

def _owner(credentials=Depends(security)) -> str:
    return current_owner(credentials)

def _gateway():
    from aethon.device_gateway_api import gateway
    return gateway

@router.post("/workflows")
def create_workflow(request: WorkflowRequest, owner_id: str = Depends(_owner)):
    planner = AndroidWorkflowPlanner()
    try:
        steps = planner.plan(request.goal)
        encoded = planner.encode(steps)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if any(step["capability"] not in _READ_ONLY for step in encoded) and not request.approval:
        raise HTTPException(403, "explicit execution approval required for this Android workflow")

    try:
        device = _gateway().status(device_id=request.device_id, owner_id=owner_id)
    except GatewayError as exc:
        raise HTTPException(404, str(exc)) from exc

    granted = set(device["capabilities"])
    missing = [step["capability"] for step in encoded if step["capability"] not in granted]
    if missing:
        raise HTTPException(403, "device capabilities not granted: " + ", ".join(sorted(set(missing))))

    workflow_id = str(uuid.uuid4())
    workflow = {
        "id": workflow_id,
        "state": "RUNNING",
        "steps": encoded,
        "next_index": 1,
        "attempts": {},
    }
    first = encoded[0]
    try:
        command = AndroidCommandTransport().enqueue_workflow_step(
            owner_id=owner_id,
            device_id=request.device_id,
            capability=first["capability"],
            arguments=first["arguments"],
            workflow=workflow,
            ttl_seconds=15,
        )
    except CommandTransportError as exc:
        raise HTTPException(409, "workflow could not be queued") from exc

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "status": "RUNNING",
        "goal": request.goal,
        "step_count": len(encoded),
        "next": {
            "command_id": command.command_id,
            "step_index": 0,
            "capability": command.capability,
        },
    }

@router.get("/workflows/{workflow_id}")
def workflow_status(workflow_id: str, owner_id: str = Depends(_owner)):
    workflow = AndroidCommandTransport().workflow(workflow_id=workflow_id, owner_id=owner_id)
    if workflow is None:
        raise HTTPException(404, "workflow not found")
    return {"ok": True, **workflow}

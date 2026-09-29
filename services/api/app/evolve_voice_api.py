from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from aethon.auth import current_owner, security
from app.evolve_voice import (
    VoiceSession,
    VoiceTransitionError,
    new_voice_session,
)

router = APIRouter(prefix="/v1/evolve/voice", tags=["evolve-voice"])
_sessions: dict[str, VoiceSession] = {}


class SessionCreateRequest(BaseModel):
    language: str = Field(default="en-IN", min_length=2, max_length=20)


class WakeRequest(BaseModel):
    phrase: str = Field(min_length=1, max_length=200)


class TranscriptRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=8000)


def owner(credentials=Depends(security)) -> str:
    return current_owner(credentials)


def _session(session_id: str, owner_id: str) -> VoiceSession:
    session = _sessions.get(session_id)
    if session is None or session.owner_id != owner_id:
        raise HTTPException(404, "voice session not found")
    return session


def _payload(session: VoiceSession) -> dict:
    return {
        "ok": True,
        "session_id": session.session_id,
        "state": session.state,
        "language": session.language,
        "wake_phrase": session.wake_phrase,
        "last_transcript": session.last_transcript,
        "updated_at": session.updated_at,
    }


@router.post("/sessions")
def create_session(request: SessionCreateRequest, owner_id: str = Depends(owner)):
    session = new_voice_session(owner_id, language=request.language)
    _sessions[session.session_id] = session
    return _payload(session)


@router.get("/sessions/{session_id}")
def get_session(session_id: str, owner_id: str = Depends(owner)):
    return _payload(_session(session_id, owner_id))


@router.post("/sessions/{session_id}/wake")
def wake(session_id: str, request: WakeRequest, owner_id: str = Depends(owner)):
    session = _session(session_id, owner_id)
    try:
        session.wake(request.phrase)
    except VoiceTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _payload(session)


@router.post("/sessions/{session_id}/listen")
def listen(session_id: str, owner_id: str = Depends(owner)):
    session = _session(session_id, owner_id)
    try:
        session.begin_listening()
    except VoiceTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _payload(session)


@router.post("/sessions/{session_id}/transcript")
def transcript(session_id: str, request: TranscriptRequest, owner_id: str = Depends(owner)):
    session = _session(session_id, owner_id)
    try:
        session.accept_transcript(request.transcript)
    except VoiceTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _payload(session)


@router.post("/sessions/{session_id}/speaking")
def speaking(session_id: str, owner_id: str = Depends(owner)):
    session = _session(session_id, owner_id)
    try:
        session.begin_speaking()
    except VoiceTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _payload(session)


@router.post("/sessions/{session_id}/sleep")
def sleep(session_id: str, owner_id: str = Depends(owner)):
    session = _session(session_id, owner_id)
    try:
        session.sleep()
    except VoiceTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _payload(session)


@router.post("/sessions/{session_id}/stop")
def stop(session_id: str, owner_id: str = Depends(owner)):
    session = _session(session_id, owner_id)
    session.stop()
    return _payload(session)

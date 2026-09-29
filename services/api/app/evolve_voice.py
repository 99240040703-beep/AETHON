from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from time import time
from uuid import uuid4


class VoiceState(StrEnum):
    SLEEPING = "SLEEPING"
    WAKING = "WAKING"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    STOPPED = "STOPPED"


class VoiceTransitionError(ValueError):
    pass


@dataclass
class VoiceSession:
    session_id: str
    owner_id: str
    language: str = "en-IN"
    state: VoiceState = VoiceState.SLEEPING
    wake_phrase: str = "Hey Evolve"
    last_transcript: str | None = None
    updated_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = time()

    def _move(self, state: VoiceState) -> "VoiceSession":
        self.state = state
        self.updated_at = time()
        return self

    def wake(self, phrase: str) -> "VoiceSession":
        if self.state not in {VoiceState.SLEEPING, VoiceState.STOPPED}:
            raise VoiceTransitionError(f"cannot wake from {self.state}")
        if phrase.strip().casefold() != self.wake_phrase.casefold():
            raise VoiceTransitionError("wake phrase not recognized")
        return self._move(VoiceState.WAKING)

    def begin_listening(self) -> "VoiceSession":
        if self.state != VoiceState.WAKING:
            raise VoiceTransitionError(f"cannot listen from {self.state}")
        return self._move(VoiceState.LISTENING)

    def accept_transcript(self, transcript: str) -> "VoiceSession":
        text = transcript.strip()
        if not text:
            raise VoiceTransitionError("transcript cannot be empty")
        if self.state != VoiceState.LISTENING:
            raise VoiceTransitionError(f"cannot accept transcript from {self.state}")
        self.last_transcript = text
        return self._move(VoiceState.PROCESSING)

    def begin_speaking(self) -> "VoiceSession":
        if self.state != VoiceState.PROCESSING:
            raise VoiceTransitionError(f"cannot speak from {self.state}")
        return self._move(VoiceState.SPEAKING)

    def sleep(self) -> "VoiceSession":
        if self.state not in {VoiceState.WAKING, VoiceState.SPEAKING, VoiceState.PROCESSING}:
            raise VoiceTransitionError(f"cannot sleep from {self.state}")
        return self._move(VoiceState.SLEEPING)

    def stop(self) -> "VoiceSession":
        return self._move(VoiceState.STOPPED)


def new_voice_session(owner_id: str, *, language: str = "en-IN") -> VoiceSession:
    return VoiceSession(
        session_id=str(uuid4()),
        owner_id=owner_id,
        language=language,
    )

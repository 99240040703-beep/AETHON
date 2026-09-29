from app.evolve_voice import (
    VoiceState,
    VoiceTransitionError,
    new_voice_session,
)


def test_voice_session_full_lifecycle():
    session = new_voice_session("owner-1", language="en-IN")

    assert session.state == VoiceState.SLEEPING
    session.wake("Hey Evolve")
    assert session.state == VoiceState.WAKING

    session.begin_listening()
    session.accept_transcript("What is today's date?")
    assert session.state == VoiceState.PROCESSING
    assert session.last_transcript == "What is today's date?"

    session.begin_speaking()
    assert session.state == VoiceState.SPEAKING

    session.sleep()
    assert session.state == VoiceState.SLEEPING


def test_wrong_wake_phrase_is_rejected():
    session = new_voice_session("owner-1")

    try:
        session.wake("Hey Assistant")
    except VoiceTransitionError:
        pass
    else:
        raise AssertionError("wrong wake phrase must be rejected")

    assert session.state == VoiceState.SLEEPING


def test_invalid_transition_is_rejected():
    session = new_voice_session("owner-1")

    try:
        session.begin_listening()
    except VoiceTransitionError:
        pass
    else:
        raise AssertionError("listening before wake must be rejected")

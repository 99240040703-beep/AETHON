from app.training_store import TrainingStore


def test_training_store_records_feedback_and_exports_jsonl():
    store = TrainingStore("")
    item = store.record(
        owner_id="owner-1",
        session_id="session-1",
        request_id="request-1",
        user_text="calculate 2 + 2",
        assistant_text="4",
        capability="CALCULATOR",
        tool="calculator",
        mode="task",
        language="en-US",
        verified=True,
        success=True,
    )

    assert store.stats("owner-1")["examples"] == 1
    assert store.feedback(item.example_id, "owner-1", "good", 1.0)
    exported = store.export_jsonl("owner-1")
    assert '"role": "user"' in exported
    assert '"role": "assistant"' in exported
    assert '"score": 1.0' in exported


def test_training_store_is_owner_scoped():
    store = TrainingStore("")
    store.record(
        owner_id="owner-a",
        user_text="hello",
        assistant_text="hi",
    )
    assert store.list("owner-b") == []

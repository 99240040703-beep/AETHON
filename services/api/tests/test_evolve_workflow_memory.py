from app.evolve_workflow_memory import WorkflowMemory

def test_memory_records_and_recalls_only_successful_exact_goal():
    memory = WorkflowMemory()
    steps = [{"capability":"OPEN_APP","arguments":{"app":"Settings"}}]
    memory.record("owner-1","Open Settings",steps,"COMPLETED",120)
    memory.record("owner-1","Open Settings",steps,"FAILED",200)
    memory.record("owner-1","Open Chrome",steps,"COMPLETED",100)
    found = memory.recall("owner-1","open settings")
    assert len(found) == 1
    assert found[0].outcome == "COMPLETED"

def test_memory_is_isolated_by_owner():
    memory = WorkflowMemory()
    memory.record("owner-1","Open Settings",[],"COMPLETED",10)
    assert memory.recall("owner-2","Open Settings") == []

def test_memory_is_bounded():
    memory = WorkflowMemory()
    for i in range(60):
        memory.record("owner-1",f"goal-{i}",[],"COMPLETED",1)
    assert len(memory._traces["owner-1"]) == 50

from app.android_workflow import AndroidWorkflowPlanner

def test_evolve_android_workflow_is_bounded_and_semantic():
    planner = AndroidWorkflowPlanner()
    steps = planner.plan("open settings and tap Wi-Fi")
    encoded = planner.encode(steps)
    assert len(encoded) <= 8
    assert encoded[0]["capability"] == "OPEN_APP"
    assert encoded[1]["capability"] == "SCREEN_READ"
    assert encoded[2]["capability"] == "SCREEN_CLICK"
    assert encoded[2]["arguments"]["text"] == "Wi-Fi"

def test_evolve_android_workflow_rejects_unknown_goal():
    planner = AndroidWorkflowPlanner()
    try:
        planner.plan("delete all my files")
    except ValueError:
        return
    assert False, "unsafe/unbounded workflow should be rejected"

def test_evolve_select_action_candidate_fails_closed_on_ambiguity():
    planner = AndroidWorkflowPlanner()
    step = {"capability":"SCREEN_CLICK","arguments":{"text":"Settings"}}
    snapshot = {"connected":True,"nodes":[
        {"text":"Settings","enabled":True,"clickable":True},
        {"text":"Settings","enabled":True,"clickable":True},
    ]}
    assert planner.select_action_candidate(step, snapshot) is None

def test_evolve_select_action_candidate_requires_semantic_capability():
    planner = AndroidWorkflowPlanner()
    step = {"capability":"SCREEN_CLICK","arguments":{"text":"Wi-Fi"}}
    snapshot = {"connected":True,"elements":[
        {"text":"Wi-Fi","enabled":True,"clickable":True},
    ]}
    assert planner.select_action_candidate(step, snapshot)["text"] == "Wi-Fi"

def test_evolve_verification_is_state_based():
    planner = AndroidWorkflowPlanner()
    step = {"capability":"SCREEN_READ","arguments":{"maxNodes":250},
            "verify":{"contains_any":["Wi-Fi network"]}}
    assert planner.verify(step, {"connected":True,"elements":[{"text":"Wi-Fi network"}]})
    assert not planner.verify(step, {"connected":True,"elements":[{"text":"Bluetooth"}]})

def test_evolve_verification_fails_closed_when_disconnected():
    planner = AndroidWorkflowPlanner()
    step = {"capability":"SCREEN_READ","arguments":{"maxNodes":250},
            "verify":{"contains_any":["Wi-Fi"]}}
    assert not planner.verify(step, {"connected":False,"elements":[]})

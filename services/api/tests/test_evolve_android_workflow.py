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

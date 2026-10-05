from app.capability_router import route_for


def test_routes_natural_language_capabilities():
    assert route_for("open this url https://example.com").tool == "web_fetch"
    assert route_for("do deep research on AI agents").tool == "web_research"
    assert route_for("make a bar chart from this").tool == "chart"
    assert route_for("calculate 25 * 4").capability == "CALCULATOR"


def test_capability_routes_include_creation_and_device():
    names = {route.capability for route in __import__("app.capability_router", fromlist=["ROUTES"]).ROUTES}
    assert {"WEBSITE_GENERATION", "IMAGE_GENERATION", "VIDEO_GENERATION", "DEVICE"}.issubset(names)

from app.capability_router import route_for
from app.training_pipeline import DEFAULT_EVALUATION_SET, evaluate_routing


def test_astra_capability_regression_benchmark():
    result = evaluate_routing(route_for, DEFAULT_EVALUATION_SET)

    assert result["total"] == 11
    assert result["passed"] == 11
    assert result["accuracy"] == 1.0

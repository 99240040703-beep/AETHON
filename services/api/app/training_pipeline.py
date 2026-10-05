from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.training_store import TrainingExample


@dataclass(frozen=True)
class QualityDecision:
    accepted: bool
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationCase:
    prompt: str
    expected_capability: str | None = None
    expected_tool: str | None = None
    expected_keywords: tuple[str, ...] = ()


def assess(example: TrainingExample) -> QualityDecision:
    reasons: list[str] = []
    score = 1.0

    if len(example.user_text.strip()) < 3:
        score -= 0.35
        reasons.append("prompt_too_short")
    if len(example.assistant_text.strip()) < 3:
        score -= 0.45
        reasons.append("response_too_short")
    if not example.success:
        score -= 0.45
        reasons.append("unsuccessful")
    if not example.verified:
        score -= 0.10
        reasons.append("unverified")
    if example.feedback in {"bad", "incorrect", "not_useful"}:
        score -= 0.80
        reasons.append("negative_feedback")
    if example.feedback in {"good", "correct", "useful"}:
        score = min(1.0, score + 0.10)

    score = max(0.0, min(1.0, score))
    return QualityDecision(score >= 0.60, round(score, 4), tuple(reasons))


def build_dataset(
    examples: Iterable[TrainingExample],
    *,
    min_score: float = 0.60,
    require_verified: bool = False,
) -> list[TrainingExample]:
    result: list[TrainingExample] = []
    seen: set[tuple[str, str]] = set()
    for example in examples:
        decision = assess(example)
        if decision.score < min_score or not decision.accepted:
            continue
        if require_verified and not example.verified:
            continue
        key = (example.user_text.strip().lower(), example.assistant_text.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(example)
    return result


def evaluate_case(
    case: EvaluationCase,
    *,
    capability: str | None,
    tool: str | None,
    response: str,
) -> dict:
    checks = {
        "capability": case.expected_capability is None or capability == case.expected_capability,
        "tool": case.expected_tool is None or tool == case.expected_tool,
        "keywords": all(k.lower() in response.lower() for k in case.expected_keywords),
    }
    passed = all(checks.values())
    return {"passed": passed, "checks": checks}


DEFAULT_EVALUATION_SET = (
    EvaluationCase("calculate 25 * 4", expected_capability="CALCULATOR", expected_tool="calculator"),
    EvaluationCase("research AI agents", expected_capability="WEB_RESEARCH", expected_tool="web_research"),
    EvaluationCase("open this url https://example.com", expected_capability="WEB_FETCH", expected_tool="web_fetch"),
    EvaluationCase("make a bar chart from this data", expected_capability="CHART", expected_tool="chart"),
    EvaluationCase("build a website for a portfolio", expected_capability="WEBSITE_GENERATION"),
)


def evaluate_routing(router, cases: Iterable[EvaluationCase] = DEFAULT_EVALUATION_SET) -> dict:
    results = []
    for case in cases:
        route = router(case.prompt)
        results.append(
            evaluate_case(
                case,
                capability=route.capability if route else None,
                tool=route.tool if route else None,
                response="",
            )
        )
    passed = sum(item["passed"] for item in results)
    total = len(results)
    return {"passed": passed, "total": total, "accuracy": round(passed / total, 4) if total else 0.0, "results": results}

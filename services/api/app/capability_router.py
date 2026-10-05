from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethon.schemas import RiskClass


@dataclass(frozen=True)
class CapabilityRoute:
    capability: str
    intents: tuple[str, ...]
    tool: str | None = None
    mode: str = "task"
    requires_confirmation: bool = False


# One normalized routing table for the complete ASTRA capability surface.
# Runtime-specific integrations remain behind their existing tools/fabrics.
ROUTES: tuple[CapabilityRoute, ...] = (
    CapabilityRoute("WEB_SEARCH", ("search", "web search", "find online", "latest", "news", "current"), "web_search"),
    CapabilityRoute("WEB_FETCH", ("open url", "open website", "fetch page", "read this url", "visit this url"), "web_fetch"),
    CapabilityRoute("WEB_RESEARCH", ("research", "deep research", "investigate", "compare sources", "verify"), "web_research"),
    CapabilityRoute("CALCULATOR", ("calculate", "calculator", "calc"), "calculator"),
    CapabilityRoute("CHART", ("bar chart", "line chart", "pie chart", "histogram", "scatter plot"), "chart"),
    CapabilityRoute("DATA_ANALYSIS", ("analyze data", "analyze dataset", "csv", "excel", "spreadsheet"), "data_analyze"),
    CapabilityRoute("IMAGE_GENERATION", ("generate image", "create image", "draw", "make a logo", "make a poster"), mode="creation"),
    CapabilityRoute("VIDEO_GENERATION", ("generate video", "create video", "make a video"), mode="creation"),
    CapabilityRoute("DESIGN_GENERATION", ("create design", "design this", "make a design", "poster design"), mode="creation"),
    CapabilityRoute("WEBSITE_GENERATION", ("build website", "create website", "make website", "develop website"), mode="creation"),
    CapabilityRoute("DEVICE", ("open app", "launch app", "tap", "click", "scroll", "swipe", "type in", "press back"), "device", mode="device", requires_confirmation=True),
    CapabilityRoute("AGENTS", ("do this for me", "complete this", "handle this", "autonomously"), mode="agent"),
)


def route_for(text: str) -> CapabilityRoute | None:
    value = " ".join(text.casefold().split())
    for route in ROUTES:
        if any(marker in value for marker in route.intents):
            return route
    return None


def capability_summary() -> list[dict[str, Any]]:
    return [
        {
            "capability": route.capability,
            "intents": list(route.intents),
            "tool": route.tool,
            "mode": route.mode,
            "requires_confirmation": route.requires_confirmation,
        }
        for route in ROUTES
    ]

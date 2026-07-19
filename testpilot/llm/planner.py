"""Planner specialist (M5).

Supported intent → FlowSpec
Uses system prompt from prompts/planner.md
Always validates output with Pydantic.
Falls back deterministically on any error or DEMO_MODE.
"""
from typing import Dict, Any

from testpilot.models import FlowSpec
from testpilot.llm.llm_client import call_llm_structured


def plan_flow(user_intent: str, mutation_id: str = "testid_removed") -> tuple[FlowSpec, str]:
    """Return (FlowSpec, reasoning_mode)."""
    context: Dict[str, Any] = {
        "user_intent": user_intent,
        "mutation_id": mutation_id,
    }
    return call_llm_structured("planner", context, FlowSpec)

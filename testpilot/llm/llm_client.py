"""LLM client with DEMO_MODE fallback and error handling for M5.

Uses langchain-openai ChatOpenAI against OpenRouter.
Always falls back to deterministic behavior when:
- DEMO_MODE=true
- No API key
- Any error (timeout, bad JSON, schema validation failure, provider error)
"""
import json
import os
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from testpilot.config import DEMO_MODE, OPENROUTER_API_KEY, LLM_MODEL
from testpilot.llm.prompt_loader import load_system_prompt


T = TypeVar("T", bound=BaseModel)


def _get_llm() -> Optional[ChatOpenAI]:
    """Return a configured ChatOpenAI or None if we must use fallback."""
    if DEMO_MODE:
        return None
    key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        return None
    try:
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", LLM_MODEL),
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            request_timeout=30,
        )
    except Exception:
        return None


def _build_context(context: Dict[str, Any]) -> str:
    """Build a small, targeted context string. Never include full HTML, traces, or raw screenshots."""
    # Only allow a safe subset of fields
    allowed = {
        "user_intent",
        "mutation_id",
        "failed_step",
        "original_locator",
        "error_excerpt",
        "expected_assertion",
        "candidate_buttons",
        "dom_excerpt",
    }
    safe = {k: v for k, v in context.items() if k in allowed and v}
    # Truncate long fields
    for k in list(safe.keys()):
        if isinstance(safe[k], str) and len(safe[k]) > 800:
            safe[k] = safe[k][:797] + "..."
    return json.dumps(safe, ensure_ascii=False, indent=2)


def call_llm_structured(
    specialist: str,
    context: Dict[str, Any],
    model_class: Type[T],
) -> tuple[T, str]:
    """
    Call the narrow LLM specialist or fall back.

    Returns (parsed_model, reasoning_mode)
    reasoning_mode is "llm" or "fallback"
    """
    llm = _get_llm()
    system_prompt = load_system_prompt(specialist)  # type: ignore[arg-type]

    user_context = _build_context(context)
    user_message = f"Context (targeted only):\n{user_context}\n\nOutput ONLY valid JSON matching the schema."

    if llm is None:
        # Deterministic fallback
        fallback = _deterministic_fallback(specialist, context, model_class)
        return fallback, "fallback"

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        # Use simple invoke + manual JSON parse for maximum compatibility
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # Extract JSON if wrapped in ```json ... ```
        text = str(content).strip()
        if text.startswith("```"):
            # crude extraction
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]

        data = json.loads(text)
        parsed = model_class.model_validate(data)
        return parsed, "llm"

    except (json.JSONDecodeError, ValidationError, Exception):
        # Any failure → deterministic fallback
        fallback = _deterministic_fallback(specialist, context, model_class)
        return fallback, "fallback"


def _deterministic_fallback(
    specialist: str,
    context: Dict[str, Any],
    model_class: Type[T],
) -> T:
    """Return a safe deterministic object matching the requested model."""
    from testpilot.workflow.diagnosis import get_deterministic_diagnosis
    from testpilot.workflow.repair import get_deterministic_repair_proposal
    from testpilot.models import FlowSpec, FlowStep

    mutation = context.get("mutation_id", "testid_removed")
    intent = context.get("user_intent", "Add the blue backpack to cart and confirm the cart count is 1.")
    failed_step = context.get("failed_step", "add_blue_backpack")

    if specialist == "planner":
        # Always return the golden FlowSpec for the slice (validated)
        return FlowSpec(
            name="add_blue_backpack_to_cart",
            steps=[
                FlowStep(action="goto", target="storefront"),
                FlowStep(action="click", target="add_blue_backpack"),
                FlowStep(action="assert", target="cart_count", expected="1"),
            ],
        )  # type: ignore[return-value]

    if specialist == "diagnosis":
        return get_deterministic_diagnosis(mutation, failed_step=failed_step)  # type: ignore[return-value]

    if specialist == "repair":
        return get_deterministic_repair_proposal(mutation, failed_step=failed_step)  # type: ignore[return-value]

    # Last resort minimal valid object
    return model_class()  # may fail if no defaults; caller should handle

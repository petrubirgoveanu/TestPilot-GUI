"""Diagnosis specialist (M5).

Failure evidence → Diagnosis
Uses system prompt from prompts/diagnosis.md
Always validates with Pydantic.
Falls back to deterministic on any issue or DEMO_MODE.
"""
from typing import Dict, Any

from testpilot.models import Diagnosis
from testpilot.llm.llm_client import call_llm_structured


def diagnose_failure(
    mutation_id: str,
    failed_step: str = "add_blue_backpack",
    error_excerpt: str = "",
    original_locator: str = "",
) -> tuple[Diagnosis, str]:
    """Return (Diagnosis, reasoning_mode)."""
    context: Dict[str, Any] = {
        "mutation_id": mutation_id,
        "failed_step": failed_step,
        "error_excerpt": error_excerpt,
        "original_locator": original_locator,
    }
    return call_llm_structured("diagnosis", context, Diagnosis)

"""Repair specialist (M5).

Evidence + Diagnosis → RepairProposal
Uses system prompt from prompts/repair.md
Always validates with Pydantic.
Falls back deterministically.
"""
from typing import Dict, Any

from testpilot.models import RepairProposal, Diagnosis
from testpilot.llm.llm_client import call_llm_structured


def propose_repair(
    mutation_id: str,
    diagnosis: Diagnosis | None = None,
    failed_step: str = "add_blue_backpack",
    error_excerpt: str = "",
) -> tuple[RepairProposal, str]:
    """Return (RepairProposal, reasoning_mode)."""
    context: Dict[str, Any] = {
        "mutation_id": mutation_id,
        "failed_step": failed_step,
        "error_excerpt": error_excerpt,
    }
    if diagnosis:
        context["diagnosis_reason"] = diagnosis.reason
        context["suggested_strategy"] = diagnosis.suggested_strategy

    return call_llm_structured("repair", context, RepairProposal)

"""Deterministic Diagnosis for M3 (no LLM).

For the slice, diagnosis is hard-coded for the single supported mutation.
Later (M5) this will be replaced by LLM specialist behind same interface.
"""
from typing import Any, Dict

from testpilot.models import Diagnosis


DETERMINISTIC_DIAGNOSIS_TEXT = (
    "The test failed because the UI refactor removed "
    'data-testid="add-backpack". The business button still exists and has '
    'the accessible name “Add Blue Backpack”.'
)


def get_deterministic_diagnosis(
    mutation_id: str,
    failed_step: str = "add_blue_backpack",
    error_excerpt: str = "",
) -> Diagnosis:
    """Return the fixed Diagnosis for the known slice mutation."""
    if mutation_id == "testid_removed":
        return Diagnosis(
            category="locator_not_found",
            reason=DETERMINISTIC_DIAGNOSIS_TEXT,
            failed_step=failed_step,
            repairable=True,
            suggested_strategy="repaired",
        )
    # Fallback for unknown (still deterministic, minimal)
    return Diagnosis(
        category="other",
        reason="Failure observed. No automated repair available for this mutation in the slice.",
        failed_step=failed_step,
        repairable=False,
        suggested_strategy="brittle",
    )

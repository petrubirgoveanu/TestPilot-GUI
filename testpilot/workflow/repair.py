"""Deterministic Repair proposal for M3 (no LLM).

Locked for the slice:
- For testid_removed: propose the role-based locator.
- Never auto-apply.
- Max two proposals per run (enforced by caller state).
"""
from testpilot.models import RepairProposal


DETERMINISTIC_REPAIR_LOCATOR = 'page.get_by_role("button", name="Add Blue Backpack")'


def get_deterministic_repair_proposal(
    mutation_id: str,
    failed_step: str = "add_blue_backpack",
) -> RepairProposal:
    """Return the fixed repair proposal for the supported mutation."""
    if mutation_id == "testid_removed":
        return RepairProposal(
            strategy="repaired",
            new_locator=DETERMINISTIC_REPAIR_LOCATOR,
            rationale=(
                "UI refactor removed data-testid but the button remains "
                "uniquely identifiable by role + accessible name."
            ),
            confidence=0.98,
        )
    # Conservative fallback for unknown mutations in slice
    return RepairProposal(
        strategy="brittle",
        new_locator="page.get_by_test_id('add-backpack')",
        rationale="No known semantic repair for this mutation in the slice.",
        confidence=0.1,
    )

"""Core data contracts for the Minimum Demoable Slice.

Intent is separated from implementation.
FlowSpec describes business steps.
Locators are resolved separately using brittle vs repaired strategies.
"""

from pydantic import BaseModel
from typing import Literal, Optional

class FlowStep(BaseModel):
    """Business step. 'target' is a logical identifier, not a locator string."""
    action: Literal["goto", "click", "assert"]
    target: str
    expected: Optional[str] = None

class FlowSpec(BaseModel):
    name: str
    steps: list[FlowStep]

# =============================================================================
# GOLDEN PATH - locked
# =============================================================================
GOLDEN_INTENT: str = (
    "Add the blue backpack to cart and confirm the cart count is 1."
)

GOLDEN_FLOWSPEC = FlowSpec(
    name="add_blue_backpack_to_cart",
    steps=[
        FlowStep(action="goto", target="storefront"),
        FlowStep(action="click", target="add_blue_backpack"),
        FlowStep(action="assert", target="cart_count", expected="1"),
    ],
)

# =============================================================================
# Locator resolution (the only thing that changes on repair)
# =============================================================================

# For the brittle (original) test we use the fragile data-testid.
# For the repaired version we use the stable semantic locator.
# These are resolved at execution time, never stored in the FlowSpec.

def resolve_locator(page, target: str, strategy: Literal["brittle", "repaired"]):
    """Return a Playwright locator for the given logical target and strategy."""
    if target == "add_blue_backpack":
        if strategy == "brittle":
            return page.get_by_test_id("add-backpack")
        return page.get_by_role("button", name="Add Blue Backpack")

    if target == "cart_count":
        return page.get_by_test_id("cart-count")

    raise ValueError(f"Unknown target: {target}")


# =============================================================================
# M3 Deterministic Repair contracts (Pydantic v2)
# =============================================================================

from typing import Literal

class Diagnosis(BaseModel):
    """Structured diagnosis for a test failure (deterministic or LLM)."""
    category: Literal["locator_not_found", "assertion_failed", "timeout", "other"]
    reason: str
    failed_step: str
    repairable: bool = True
    suggested_strategy: Literal["brittle", "repaired", "role"] = "repaired"


class RepairProposal(BaseModel):
    """A single proposed locator repair. Never auto-applied."""
    strategy: Literal["brittle", "repaired", "role"]
    new_locator: str  # e.g. 'page.get_by_role("button", name="Add Blue Backpack")'
    rationale: str
    confidence: float


class ValidationResult(BaseModel):
    """Result of running the validator checks on a proposed repair."""
    passed: bool
    checks: list[str]  # e.g. ["unique", "visible", "enabled", "click_success", "cart_count==1"]
    error: Optional[str] = None


class RunState(BaseModel):
    """Lightweight state for a healing run (used by M3 deterministic flow + later UI)."""
    run_id: str
    mutation_id: str
    status: Literal["passed", "failed", "healed", "needs_human_review", "rejected"]
    attempts: int = 0
    diagnosis: Optional[Diagnosis] = None
    proposal: Optional[RepairProposal] = None
    approved: bool = False
    validation: Optional[ValidationResult] = None
    final_locator: Optional[str] = None
    manifest_path: Optional[str] = None

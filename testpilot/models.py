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

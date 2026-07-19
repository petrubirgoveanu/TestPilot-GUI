"""Repair validator for M3.

Performs the exact safety checks required before accepting a repair:
- exactly one matching element
- visible
- enabled
- click succeeds
- cart count becomes "1"

This is deterministic. No LLM.
"""
from typing import List

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError

from testpilot.models import ValidationResult
from testpilot.models import resolve_locator


def validate_repair_candidate(
    page: Page,
    *,
    timeout_ms: int = 5000,
) -> ValidationResult:
    """Run the required validator checks on the repaired locator for the slice.

    The repaired locator is fixed for the demo slice:
        page.get_by_role("button", name="Add Blue Backpack")
    """
    checks: List[str] = []
    candidate = page.get_by_role("button", name="Add Blue Backpack")

    try:
        # 1. Unique
        count = candidate.count()
        if count != 1:
            return ValidationResult(
                passed=False,
                checks=checks,
                error=f"Expected exactly 1 match, got {count}",
            )
        checks.append("unique")

        # 2. Visible
        if not candidate.is_visible():
            return ValidationResult(passed=False, checks=checks, error="Candidate not visible")
        checks.append("visible")

        # 3. Enabled
        if not candidate.is_enabled():
            return ValidationResult(passed=False, checks=checks, error="Candidate not enabled")
        checks.append("enabled")

        # 4. Click + assertion
        candidate.click(timeout=timeout_ms)
        checks.append("click_success")

        cart = resolve_locator(page, "cart_count", "brittle")
        expect(cart).to_have_text("1", timeout=timeout_ms)
        checks.append("cart_count==1")

        return ValidationResult(passed=True, checks=checks)

    except PlaywrightTimeoutError as e:
        return ValidationResult(passed=False, checks=checks, error=f"timeout: {str(e)[:200]}")
    except Exception as e:
        return ValidationResult(passed=False, checks=checks, error=str(e)[:300])

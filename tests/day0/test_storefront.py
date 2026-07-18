"""Day 0 baseline tests using the golden path.

GOLDEN_INTENT (from testpilot/models.py):
    "Add the blue backpack to cart and confirm the cart count is 1."

FlowSpec is business intent only. Locators are resolved at runtime via resolve_locator().

These tests prove:
- baseline passes using brittle strategy
- mutated fails using brittle strategy
- after repair the journey passes on mutated UI using repaired strategy

Run:
  # Preferred (agents must use background_process):
  #   background_process start with: python -m http.server 8080 --directory demo_site
  # Human quick start (two terminals or background):
  python -m http.server 8080 --directory demo_site
  pytest tests/day0 -q --tracing retain-on-failure --screenshot only-on-failure
"""
from playwright.sync_api import Page, expect

from testpilot.models import (
    resolve_locator,
)

BASE = "http://localhost:8080"

def test_golden_path_baseline_passes_with_brittle(page: Page):
    """Baseline passes with the original fragile locator (brittle strategy)."""
    page.goto(f"{BASE}/index.html?mutation=baseline")
    btn = resolve_locator(page, "add_blue_backpack", "brittle")
    # EXPECTED: PASS — brittle locator (data-testid) exists on baseline page
    btn.click()
    resolve_locator(page, "cart_count", "brittle").wait_for()
    expect(resolve_locator(page, "cart_count", "brittle")).to_have_text("1")


def test_golden_path_mutated_fails_with_brittle(page: Page):
    """Mutated UI causes the brittle locator to fail."""
    page.goto(f"{BASE}/index.html?mutation=testid_removed")
    btn = resolve_locator(page, "add_blue_backpack", "brittle")
    # EXPECTED: FAIL — brittle locator (data-testid) was removed by JS on this mutation
    # The click will timeout waiting for get_by_test_id("add-backpack")
    btn.click()
    expect(resolve_locator(page, "cart_count", "brittle")).to_have_text("1")


def test_golden_path_after_repair_works_on_mutated(page: Page):
    """Repaired strategy succeeds on the mutated storefront."""
    page.goto(f"{BASE}/index.html?mutation=testid_removed")
    btn = resolve_locator(page, "add_blue_backpack", "repaired")
    # EXPECTED: PASS — repaired locator uses role+name (still present after mutation)
    btn.click()
    expect(resolve_locator(page, "cart_count", "brittle")).to_have_text("1")

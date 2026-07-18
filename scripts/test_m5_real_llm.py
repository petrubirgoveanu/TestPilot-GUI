"""Manually test the real LLM path for M5 (optional — requires API key + network).

Run from the project root:
    set DEMO_MODE=false
    set OPENROUTER_API_KEY=sk-or-...
    set LLM_MODEL=openai/gpt-4o-mini
    python scripts\test_m5_real_llm.py

WARNING: This makes real network calls to OpenRouter and will consume API credits.
Do NOT run this in CI or automated test suites.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

demo = os.environ.get("DEMO_MODE", "true").lower()
key = os.environ.get("OPENROUTER_API_KEY", "")

if demo == "true" or not key:
    print("ERROR: Set DEMO_MODE=false and OPENROUTER_API_KEY=<your-key> before running.")
    print("  set DEMO_MODE=false")
    print("  set OPENROUTER_API_KEY=sk-or-...")
    sys.exit(1)

from testpilot.llm.planner import plan_flow
from testpilot.llm.diagnosis import diagnose_failure
from testpilot.llm.repair import propose_repair

print("=== Planner (real LLM) ===")
spec, mode = plan_flow("Add the blue backpack to cart and confirm the cart count is 1.")
print("mode:", mode, " | name:", spec.name)

print("\n=== Diagnosis (real LLM) ===")
d, mode = diagnose_failure("testid_removed", error_excerpt="waiting for get_by_test_id")
print("mode:", mode, " | category:", d.category)

print("\n=== Repair (real LLM) ===")
p, mode = propose_repair("testid_removed")
print("mode:", mode, " | new_locator:", p.new_locator)

print()
print("All modes must be 'llm' when a valid key is provided.")
print("Bad JSON / timeout / schema errors must still produce 'fallback' (tested separately).")

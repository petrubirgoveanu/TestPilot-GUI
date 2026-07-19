"""Verify M5 context builder excludes forbidden fields and truncates long values.

Run from the project root:
    python scripts\verify_m5_context.py

No network calls are made.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testpilot.llm.llm_client import _build_context

ctx = {
    "user_intent": "Add the blue backpack to cart and confirm the cart count is 1.",
    "mutation_id": "testid_removed",
    "error_excerpt": "x" * 2000,       # long — must be truncated to 800 chars
    "full_html": "<html>...</html>",   # must be excluded (not in whitelist)
    "trace": "long trace...",          # must be excluded
}

result = _build_context(ctx)
print("=== Built context ===")
print(result)
print()

parsed = json.loads(result)

print("=== Checks ===")
print("full_html excluded :", "full_html" not in parsed)   # must be True
print("trace excluded     :", "trace" not in parsed)       # must be True
print(
    "error_excerpt len  :",
    len(parsed.get("error_excerpt", "")),
    "<= 800:",
    len(parsed.get("error_excerpt", "")) <= 800,
)

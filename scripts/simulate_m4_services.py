"""Fast Simulation via Services — Windows-compatible equivalent of Section 5 in how-to-test-m4.md.

Run from the project root:
    python scripts/simulate_m4_services.py

Requires:
    - python -m http.server 8080 running (see Section 2 of how-to-test-m4.md)
    - All requirements installed: pip install -r requirements.txt
"""
import sys
import os

# Ensure the project root (parent of scripts/) is on sys.path so testpilot is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testpilot.ui import services


print("=== Baseline ===")
print(services.get_mutation_description("baseline"))
print(services.build_target_url("baseline"))

print("\n=== Remove test ID ===")
print(services.get_mutation_description("testid_removed"))
print(services.build_target_url("testid_removed"))

print("\n=== Run on testid_removed (real brittle runner) ===")
# To watch the browser run visibly, change headless=True to headless=False below.
# To slow down each Playwright action (e.g. 500ms pause between steps), pass slow_mo_ms=500.
# Example: services.run_original_regression("testid_removed", headless=False)  # visible browser
run = services.run_original_regression("testid_removed", headless=True)
print("status:", run["status"])
print("proposal present:", run.get("proposal") is not None)
print("diagnosis snippet:", (run.get("diagnosis") or {}).get("reason", "")[:80])

if run.get("proposal"):
    print("\n=== Approve & Validate (real validator + repaired run) ===")
    approved = services.approve_and_validate(run, headless=True)
    print("approved:", approved.get("approved"))
    print("final_status:", approved.get("final_status"))
    print("validation checks:", (approved.get("validation") or {}).get("checks"))
    print("manifest:", approved.get("manifest_path"))

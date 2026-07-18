"""Verify M5 DEMO_MODE and missing-key fallback behaviour.

Run from the project root:
    python scripts\verify_m5_fallback.py

No network calls are made. Expected output: all modes = 'fallback'.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import testpilot.config as cfg
import testpilot.llm.llm_client as client
from testpilot.llm.planner import plan_flow
from testpilot.llm.diagnosis import diagnose_failure
from testpilot.llm.repair import propose_repair

# --- Step 1: DEMO_MODE=true forces fallback ---
os.environ["DEMO_MODE"] = "true"

print("=== DEMO_MODE=true ===")
_, mode = plan_flow("Add the blue backpack to cart and confirm the cart count is 1.")
print("Planner mode  :", mode)          # must be 'fallback'

_, mode = diagnose_failure("testid_removed")
print("Diagnosis mode:", mode)          # must be 'fallback'

_, mode = propose_repair("testid_removed")
print("Repair mode   :", mode)          # must be 'fallback'

# --- Step 2: Missing API key forces fallback ---
os.environ["DEMO_MODE"] = "false"
os.environ["OPENROUTER_API_KEY"] = ""

# Re-import to pick up env changes (config is read at import time in some modules)
importlib.reload(cfg)
importlib.reload(client)

llm = client._get_llm()
print("\n=== Missing API key ===")
print("_get_llm() returns None (fallback):", llm is None)  # must be True

"""Verify reasoning_mode is recorded in run manifests (M5).

Run from the project root:
    python scripts\verify_m5_manifest.py

No network calls are made. Uses a temporary directory for the test manifest.
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testpilot.reporting.run_manifest import write_manifest

print("=== reasoning_mode manifest check ===")

with tempfile.TemporaryDirectory() as tmp:
    data = {
        "run_id": "test-m5-001",
        "mutation_id": "testid_removed",
        "status": "healed",
        "reasoning_mode": "llm",
    }
    path = write_manifest("test-m5-001", data, root=os.path.join(tmp, "artifacts"))
    loaded = json.load(open(path))
    recorded = loaded.get("reasoning_mode")
    print("reasoning_mode recorded:", recorded)
    print("Check passed           :", recorded == "llm")

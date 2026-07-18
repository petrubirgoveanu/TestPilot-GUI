"""Verify M5 system prompts load correctly from prompts/*.md.

Run from the project root:
    python scripts\verify_m5_prompts.py

No network calls are made.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testpilot.llm.prompt_loader import load_system_prompt

print("=== System Prompt Check ===")
for specialist in ("planner", "diagnosis", "repair"):
    txt = load_system_prompt(specialist)
    has_json = "JSON" in txt or "json" in txt.lower()
    print(f"{specialist:10s}  len={len(txt):5d}  contains 'JSON': {has_json}")

print()
print("All prompts must: have len > 0 and contain 'JSON' (schema instructions).")

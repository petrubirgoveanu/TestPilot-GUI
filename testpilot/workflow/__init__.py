"""Deterministic (M3) + LLM (M5+) workflow package for TestPilot.

Contains:
- deterministic diagnosis + repair proposal
- validator enforcing the required safety checks
- approval gate (explicit human approval required)
- run state machine helpers

No LLM calls in this package for M3. DEMO_MODE + deterministic fallbacks only.
"""

"""LLM specialists package for M5 (narrow, prompt-driven).

Contains:
- prompt loading
- LLM client (with DEMO_MODE + error fallback)
- planner, diagnosis, repair specialists (structured + Pydantic validated)
- targeted context builders
- deterministic fallbacks

All tests must use mocks or DEMO_MODE. Never make real OpenRouter calls in the test suite.
"""

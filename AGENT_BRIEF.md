# TestPilot — AI Agent Briefing

You are an autonomous implementation agent.

## Mandatory Rules (non-negotiable)

1. You **must** use the tools listed in the "AVAILABLE TOOLS & HOW TO USE THEM" section at the top of `implementation-prompt`.
2. **Never** edit or write any file without first calling `read` on it.
3. Use `glob` + `grep` to discover the current state before assuming structure.
4. Every command the prompt says to run must be executed with `bash` (or `background_process` for long-running servers). Report the **real** stdout/stderr.
5. For the Gradio app and any long-running server: always use `background_process`. Never use `&`, `nohup`, or manual terminal starts.
6. Use `webfetch` (never guess) for any external content.
7. After **every** milestone:
   - Run the exact test commands listed.
   - Record real results in `docs/implementation-log.md` using the exact format.
   - Never claim success unless the tests actually passed in the tool output.
8. `DEMO_MODE=true` must always work with network disabled for tests.
9. Human approval is a hard gate. Never auto-apply repairs.
10. Stop and clearly report when any gate fails. Do not invent passing results.

## Scope Lock

- Only the Minimum Demoable Slice (one golden intent, one mutation: `testid_removed`).
- Python 3.11 + Gradio Blocks + sync Playwright + Pydantic v2 + OpenRouter `gpt-4o-mini`.
- LangGraph **only after** the deterministic loop is green.
- Render deployment attempt required.

## How to Work

- Read `implementation-prompt` fully before starting each milestone.
- Implement one milestone at a time.
- After finishing a milestone's code, run the exact "Run and pass" commands using tools.
- Update `docs/implementation-log.md` with real output.
- Ask the user (via `question` tool) only when genuinely stuck on a decision.

Follow the rules strictly. Quality over speed.

## M2 Execution Lessons (add to every future session)
- Storefront server must be pre-started (background_process or manual) on port 8080 serving demo_site. background_process will fail with "port in use" if something is already listening.
- The mutated brittle test waits a full 30s by design. Full integration runs frequently exceed agent tool timeouts (120s default). Use:
  - `python -m pytest "tests/integration/...::specific_test" -q --tb=line`
  - or direct `python -c "from testpilot.browser.runner import run_brittle_journey; print(run_brittle_journey('testid_removed'))"` for fast Post-M2 verification.
- Always create `__init__.py` (even empty) in new `testpilot/subdir/` packages.
- Prefer the exact 6 Post-M* python -c checks in milestone-checklist.md over full pytest when time is limited.
- Manifest always written. Screenshot only on failure. Truncate error excerpts early.
- Day-0 / M1 tests must still pass after M2 changes (they did — 2 passed, 1 failed as designed).

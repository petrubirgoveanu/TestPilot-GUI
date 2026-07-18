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

## M3 Execution Lessons (add to every future session)
- Runner must support strategy="brittle"|"repaired" (generalize run_journey) before or during M3. M2 brittle-only API is not sufficient for "full repaired journey after approval".
- Healing coordinator (execute_deterministic_healing) must drive the runner with the chosen strategy AND run the validator inside a live Playwright page context for the mutation.
- Approval is a HARD explicit gate: pass approve=True only on real user action. Default must stay False. Tests must assert that validation is skipped when not approved.
- Validator must literally implement the five checks exactly: count==1, visible, enabled, click succeeds, cart-count==1. These are non-negotiable.
- After any M3 change run the three manual full loops exactly:
  1. baseline → healed immediately (no proposal)
  2. testid_removed + approve=True → diagnosis + proposal + validation pass + repaired rerun → HEALED + full manifest
  3. Independent second testid_removed + approve
  Then inspect artifacts/<run_id>/run_manifest.json for diagnosis/proposal/approved/validation/repaired_result.

## M4 Execution Lessons (add to every future session)
- Keep Gradio callbacks **thin**. Put all real work (runner calls, M3 deterministic healing, validation) in `testpilot/ui/services.py`. Layout only wires components and calls services. This enables unit testing without launching the full app.
- Gradio queue API changed: use `demo.queue(default_concurrency_limit=1)`. The old `concurrency_count` kwarg can cause TypeError on current Gradio versions.
- Mutation radio selection **must** produce the exact URL that the real runner will use (`http://.../index.html?mutation=...`). Previews are not decorative — they must match the JS behavior in `demo_site/index.html`.
- Approval gate visibility is controlled in the UI: "Approve & Validate Repair" / "Reject" only appear when a proposal exists and `approved` is false. Enforce this both in services result shape and `gr.update(visible=...)`.
- For fast iteration during M4, use direct `python -c "from testpilot.ui import services; ..."` calls (run_original_regression + approve_and_validate) instead of always clicking in the browser. Pass `headless=False` when you want to watch Playwright.
- Still requires the external storefront on 8080. Brittle failures take ~30s by design.
- Always start the Gradio app with `background_process` (never & or nohup). Verify reachability with urllib or webfetch.
- After approve, the healing-style manifest must contain diagnosis, proposal, approved, validation.checks, repaired_result.
- New subpackage (`testpilot/ui/`) needs an `__init__.py`.
- Re-run full `python -m pytest tests/unit -q` after any change that touches runner or services.
- M4 is still 100% deterministic — no OpenRouter, no LLM code paths. All tests and manual flows must prove this.
- Sequence rule: M3 (tests green + 3 recorded loops) must be complete before starting M4. M4 is only a surface over the real M2 runner + M3 services.
- See `docs/how-to-test-m4.md` for the exact manual acceptance steps + simulation commands.
- The 30s brittle timeout and external storefront prerequisite still apply. Use python -c for healing flows during dev.
- New subpackages (testpilot/workflow) require __init__.py.
- Re-run units that import runner symbols immediately after runner edits.
- Healing manifests are rich (contain state machine); runner-only manifests stay minimal. Both must be valid JSON.
- Windows: never rely on Unix pipes (| head). Use Select-Object / Select-String.
- M3 is 100% deterministic. Must pass with DEMO_MODE=true and no network. No real OpenRouter calls allowed in tests or manual verification.

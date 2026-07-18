# TestPilot — Milestone Quick Reference (Slice Only)

**Golden Intent (locked):**  
"Add the blue backpack to cart and confirm the cart count is 1."

**Only mutation until slice is green:** `testid_removed`

**Core contracts:** `testpilot/models.py` (GOLDEN_FLOWSPEC + `resolve_locator(page, target, "brittle"|"repaired")`)

**Agent Rules (always):**
- Read before edit (`read` tool).
- Use `background_process` for any long-running server (Gradio, http.server).
- All commands via `bash` or `background_process`. Report real output.
- Record every milestone in `docs/implementation-log.md` (real results only).
- Never claim "done" without actual tool-verified passing runs.
- DEMO_MODE + static storefront must work with no network.
- Human approval is a hard gate. No auto-repair.

**Flat layout:** `from testpilot.models import ...` (PYTHONPATH=. or editable install).

---

## M1 — Controlled Storefront (Static)

**Objective**  
Maintain the existing static storefront that supports the golden journey and the one mutation.

**Key Files**  
- `demo_site/index.html` (already present)
- `tests/day0/test_storefront.py` (already has baseline + role tests)

**What to Do**  
- Serve with `python -m http.server ... --directory demo_site`
- Mutation via `?mutation=baseline` vs `?mutation=testid_removed`
- `data-testid="add-backpack"` present only on baseline
- Button always findable by role + name "Add Blue Backpack"
- Click increments `data-testid="cart-count"` from 0 to 1

**Run & Verify**  
```bash
python -m http.server 8080 --directory demo_site
pytest tests/day0 -q
pytest -q
```

**Exit**  
Real browser proves:
- Baseline passes with brittle locator
- testid_removed fails with brittle locator
- Both still work via repaired locator (role)

Do not start M2 until this gate is green with tool output.

### Post-M1 Verification (Human / Independent Agent Must Confirm)

**Required checks (run these exactly):**

1. Static server serves the file without Python web framework:
   ```bash
   python -m http.server 8080 --directory demo_site
   ```
   - Confirm only static HTML/JS is used (no FastAPI/Flask/etc. processes running for the storefront).

2. Baseline mutation works with brittle locator:
   ```bash
   pytest tests/day0 -q -k "baseline" --tb=short
   ```
   - Must show: `passed`

3. testid_removed mutation fails with brittle locator:
   ```bash
   pytest tests/day0 -q -k "testid_removed" --tb=short
   ```
   - Must show: `failed`
   - Must contain evidence of `data-testid` not found or similar.

4. Repaired locator works on both mutations:
   ```bash
   pytest tests/day0 -q --tb=line
   ```
   - All tests pass when using `resolve_locator(..., "repaired")`.

5. Mutation behavior is visible in the actual HTML:
   ```bash
   # baseline
   (Get-Content demo_site\index.html -Raw) | Select-String -Pattern 'data-testid="add-backpack"'
   # mutated (you can temporarily edit the query param in a test or use curl + grep)
   ```

6. Record the full verification run in `docs/implementation-log.md` with:
   - Exact commands executed
   - Full real output (stdout + stderr)
   - Pass/fail conclusion
   - Any limitations observed

Only after a human (or separate agent) has completed and logged all 6 items is M1 considered verified.

---

## M2 — Playwright Runner + Artifacts (Brittle Only)

**Prerequisite**  
M1 green. Storefront serves both mutations. Existing tests prove pass/fail.

**Objective**  
Create reusable sync runner that executes the brittle journey and produces evidence.

**Must Produce**  
- `testpilot/browser/runner.py` (or equivalent)
- Unique `run_id`
- `artifacts/<run_id>/` containing:
  - screenshot on failure
  - `run_manifest.json`
  - error excerpt, failed_step, mutation_id, status, etc.
- Runner callable like `run_brittle_journey(mutation_id=...)`

**Required Behavior (exact brittle flow from M1)**  
```python
page.goto(url_with_mutation)
page.get_by_test_id("add-backpack").click()
expect(...cart-count...).to_have_text("1")
```

**Run & Verify**  
```bash
# Start storefront if needed (use background_process)
pytest tests/day0 -q
pytest tests/integration -q   # or wherever you put runner tests
pytest -q
```

**Exit**  
- Baseline run → passed + manifest
- testid_removed run → failed + screenshot + manifest
- All artifacts under `artifacts/<run_id>/`
- Real Playwright output captured via tools

Do not proceed until M2 runner is proven with actual tool runs.

### Post-M2 Verification (Human / Independent Agent Must Confirm)

**Required checks (execute via tools):**

1. Runner module exists and can be imported:
   ```bash
   python -c "from testpilot.browser import runner; print('import OK')"
   ```

2. Baseline run produces a clean pass + manifest:
   ```bash
   # Example (adjust to actual runner API)
   python -c "
   from testpilot.browser.runner import run_brittle_journey
   result = run_brittle_journey(mutation_id='baseline')
   print(result)
   "
   ```
   - `status` == "passed"
   - `manifest_path` exists and is valid JSON
   - No screenshot required on pass (but allowed)

3. testid_removed run produces a real failure + artifacts:
   ```bash
   python -c "
   from testpilot.browser.runner import run_brittle_journey
   result = run_brittle_journey(mutation_id='testid_removed')
   print(result)
   "
   ```
   - `status` == "failed"
   - `failed_step` is a logical target (e.g. "add_blue_backpack")
   - `screenshot_path` exists and file size > 0
   - `run_manifest.json` exists under `artifacts/<run_id>/`
   - Error excerpt is present and truncated (not the full stack)

4. Artifact directory hygiene:
   ```bash
   # List the run folder
   Get-ChildItem artifacts -Recurse | Where-Object { $_.FullName -match '<run_id>' }
   ```
   - Only files for this run_id are inside `artifacts/<run_id>/`
   - No stray files at `artifacts/` root from this run

5. Reproducibility:
   - Run the same mutation twice.
   - Confirm different `run_id` each time.
   - Confirm artifacts go to different folders.

6. Full verification log entry in `docs/implementation-log.md` containing:
   - All commands used
   - Complete real output
   - Pass/fail per check
   - Any environment notes (e.g. port used, Windows path handling)

M2 is only verified when a human (or separate agent) has performed and logged all items above.

---

## M3 — Deterministic Repair + Human Approval + Validation

**Prerequisite**  
M2 runner works and can produce failure artifacts for testid_removed.

**Objective**  
Hard-coded diagnosis + repair proposal + explicit approval + validation + full rerun.

**Deterministic Content (locked for slice)**  
Diagnosis: "The test failed because the UI refactor removed data-testid=... The business button still exists..."
Repair proposal: `page.get_by_role("button", name="Add Blue Backpack").click()`

**Must Implement**  
- Deterministic diagnosis + proposal functions
- `Approve & Validate Repair` button (never auto-apply)
- Validator: count==1, visible, enabled, click succeeds, cart-count==1
- After approval: rerun full journey with repaired locator
- Max 2 attempts → `needs_human_review`
- Write every state to manifest

**Run & Verify**  
Create tests as needed, then:
```bash
pytest tests/unit -q
pytest tests/integration -q
pytest tests/e2e -q
pytest -q
```

**Manual Requirement**  
Execute end-to-end 3 times manually:
baseline pass → mutated failure → approve → validate → healed

Record real results in `docs/implementation-log.md`.

**Exit**  
All tests green + 3 clean manual deterministic loops recorded.

Do not start M4 until this is done.

### Post-M3 Verification (Human / Independent Agent Must Confirm)

**Required checks (must all be executed with real tools):**

1. Deterministic diagnosis and proposal are hard-coded (no LLM calls):
   ```bash
   python -c "
   from testpilot.workflow import diagnosis, repair   # or wherever you placed them
   d = diagnosis.get_deterministic_diagnosis(...)
   r = repair.get_deterministic_proposal(...)
   print(d, r)
   "
   ```
   - Must return the exact strings defined in the spec.
   - No network / OpenRouter activity.

2. Approval gate is real:
   - Start the component that holds the approval state.
   - Trigger a failure.
   - Confirm validation **does not run** until explicit "approve" action.
   - Use tool commands or UI clicks (via code) to prove this.

3. Validator enforces the three checks:
   ```bash
   # Run the validator directly or via the flow with a good candidate
   # Then deliberately feed it bad candidates (wrong name, hidden, multiple matches)
   ```
   - Must reject: count != 1, not visible, not enabled.
   - Must accept only the single correct repaired button.

4. Full end-to-end deterministic loop (3+ times):
   - Use the actual flow (not just unit tests).
   - Baseline pass → testid_removed brittle failure → deterministic proposal → explicit approve → validation → full rerun passes with repaired locator.
   - Record the three full runs in `docs/implementation-log.md` with commands + real outputs.

5. Manifest records the full state machine:
   - Check the final manifest for this run.
   - Must contain: failure, proposal, approval decision, validation result, final HEALED status.
   - No "approved" without an explicit approval step in the log/manifest.

6. Human verification log entry:
   - All commands + full output.
   - Confirmation that no LLM was involved.
   - Confirmation that approval was mandatory.
   - Any deviations or limitations.

M3 is only accepted after a human (or separate agent) has independently run and logged all checks.

---

## M4 — Gradio UI (Wired to Real Runner + Deterministic)

**Prerequisite**  
M2 runner + M3 deterministic repair/approval fully working.

**Objective**  
Single-page Gradio Blocks app that drives the real flow.

**Must Have**  
- "UI Change Lab" with `gr.Radio` (Baseline / Remove test ID)
- Mutation selection actually changes the URL passed to the runner
- Before/after preview (use `gr.HTML`)
- Run button
- Timeline of states
- Screenshot + error + diagnosis (start with deterministic from M3)
- Repair diff (brittle vs repaired locator)
- Approve / Reject buttons (real gate)
- Final HEALED state only after validated rerun
- Download manifest

**Important**  
- First make UI use the **real M2 runner** + **M3 deterministic outputs**.
- No real OpenRouter calls in M4.
- Use Gradio queue + `concurrency_id="browser_runner"`.

**Run & Verify**  
```bash
# Use background_process for the app
pytest tests/unit -q
pytest tests/integration -q   # UI handler tests
pytest -q
```

Manual acceptance (9 steps in prompt):
- Mutation changes actual runner target
- Run produces real failure + screenshot
- Approval only appears when proposal pending
- Approve leads to validated healed run

**Exit**  
Graphical selection drives real Playwright + deterministic loop works end-to-end in the UI.

### Post-M4 Verification (Human / Independent Agent Must Confirm)

**Required checks (run these manually or via tools):**

1. App starts cleanly (use `background_process`):
   ```bash
   # Start
   # Then inspect logs / port
   ```
   - Gradio UI is reachable at the expected address.
   - No startup errors related to missing modules or ports.

2. Mutation selector actually affects the runner:
   - Select "Baseline" → run → confirm the runner receives `baseline` (check logs or manifest).
   - Select "Remove test ID" → run → confirm the runner receives `testid_removed`.
   - This must be the **real runner from M2**, not a mock.

3. UI shows real evidence from the run:
   - After a failing run on `testid_removed`:
     - Screenshot is visible in the UI (or downloadable).
     - Error excerpt is shown.
     - Diagnosis panel shows the deterministic diagnosis text.
     - Repair diff shows the before/after locator change.

4. Approval gate works in the UI:
   - Run a failing case.
   - Confirm "Approve & Validate Repair" button is **not** clickable/enabled before a proposal exists.
   - After proposal appears, click Approve.
   - Confirm the UI only then proceeds to validation + rerun.

5. Full UI-driven loop succeeds:
   - Baseline → pass (green).
   - testid_removed → failure + proposal.
   - Approve → validation passes → final HEALED status.
   - Manifest is downloadable and contains the full history.

6. Concurrency & safety (quick smoke):
   - Attempt two runs quickly.
   - Confirm browser actions are serialized (no overlapping Playwright sessions).

7. Log everything:
   - Record in `docs/implementation-log.md`:
     - Exact start command (`background_process`).
     - UI actions performed (or code that drove them).
     - Full relevant output / screenshots of the UI state.
     - Final pass/fail conclusion.

M4 is only verified after a human (or separate agent) has performed and logged these checks.

---

## M5 — Pydantic + Real LLM Specialists (with System Prompts)

**Prerequisite**  
M4 green with deterministic loop.

**Objective**  
Introduce real (but narrow) LLM calls behind the same interfaces.

**Models**  
FlowStep, FlowSpec, Diagnosis, RepairProposal, ValidationResult, RunResult.

**Specialists (each with dedicated system prompt)**  
- `prompts/planner.md` → FlowSpec
- `prompts/diagnosis.md` → Diagnosis
- `prompts/repair.md` → RepairProposal

**Rules (strict)**  
- Load `.md` as system message
- Temperature 0
- JSON only + Pydantic validation
- Targeted context only (never full HTML/trace)
- DEMO_MODE / error → deterministic fallback
- Record `reasoning_mode`

**No** general agents, no sub-agents, no raw code execution.

**Run & Verify**  
```bash
pytest tests/unit -q
pytest tests/integration/test_llm_services.py -q
pytest -q
```

Must work with internet disabled in DEMO_MODE.

### Post-M5 Verification (Human / Independent Agent Must Confirm)

**Required checks:**

1. Real LLM path works when key is present:
   - Set a valid `OPENROUTER_API_KEY`.
   - Run a case that exercises Planner / Diagnosis / Repair.
   - Confirm actual API calls are made (check logs or token usage if available).
   - Output must be valid Pydantic models.

2. DEMO_MODE / fallback works with no network:
   ```bash
   $env:DEMO_MODE="true"   # or export DEMO_MODE=true
   # Run the same cases
   ```
   - Must produce correct deterministic output.
   - No network calls attempted.
   - `reasoning_mode: "fallback"` (or equivalent) recorded in manifest.

3. System prompts are actually loaded:
   ```bash
   # Inspect or add a small debug print / test that shows the loaded prompt text
   # Confirm it contains the expected instructions / schema / examples
   ```

4. Error handling:
   - Simulate bad JSON or provider error.
   - Confirm fallback is used cleanly and the run continues.

5. All tests still pass with both modes:
   ```bash
   pytest tests/unit -q
   pytest tests/integration -q
   pytest -q
   ```

6. Full log entry in `docs/implementation-log.md` with:
   - Commands and environment variables used
   - Real outputs for both real-LLM and fallback paths
   - Confirmation that system prompts were loaded
   - Any rate-limit / cost notes

M5 is only accepted after independent verification of the above.

---

## M6 — LangGraph Workflow (Optional, Only If Previous Are Solid)

**Prerequisite**  
M1–M5 stable. Deterministic loop green multiple times.

**Objective**  
Minimal LangGraph that orchestrates the full flow with approval gate.

**Graph**  
plan → execute → (pass | fail → diagnose → propose → await_approval → validate → rerun)

**Requirements**  
- Every transition written to manifest
- UI shows state
- Use deterministic stubs first (`DEMO_MODE=true`)
- No live LLM in graph tests

**Run & Verify**  
```bash
pytest tests/unit/test_graph.py -q
pytest tests/integration/test_workflow.py -q
pytest -q
```

Every branch tested.

### Post-M6 Verification (Human / Independent Agent Must Confirm) — Only If M6 Was Implemented

**Required checks:**

1. Graph can be imported and visualized (or at least instantiated):
   ```bash
   python -c "
   from testpilot.workflow import graph   # or wherever the compiled graph lives
   print('graph OK')
   "
   ```

2. Deterministic path through the full graph:
   - Use `DEMO_MODE=true` / deterministic stubs.
   - Drive a complete pass → fail → diagnose → propose → approve → validate → healed flow.
   - Every state transition must be recorded in the manifest.

3. All documented branches have tests and pass:
   - Pass branch
   - Fail → proposal → approve → success
   - Fail → proposal → reject
   - Second failure → `needs_human_review`

4. No live LLM calls during graph tests (unless explicitly testing the LLM nodes with stubs).

5. UI reflects graph state (if the UI was updated for the graph).

6. Log the verification run(s) with full commands and output.

M6 is only verified if it was actually implemented and the above checks pass.

---

## M7 — LangSmith (Strictly Optional)

Only if you want traces. Never required for functionality or submission.

### Post-M7 Verification (Optional)

If LangSmith tracing was enabled:

- Confirm traces appear for planner/diagnosis/repair decisions.
- Confirm no traces contain secrets or full HTML.
- Document the tracing toggle and how to disable it.

Otherwise mark as "Not implemented / skipped for the slice".

---

## M8 — Evaluation Suite

**Files**  
`evals/repair_cases.json` + `run_evals.py`

**Minimum**  
One case for `testid_removed`.

Measure:
- Schema validity
- Expected category / failed step
- Healing success rate
- Approval compliance

**Run**  
```bash
python evals/run_evals.py
```

### Post-M8 Verification (Human / Independent Agent Must Confirm)

**Required checks:**

1. `evals/repair_cases.json` contains at least one realistic case for the locked mutation.
2. `run_evals.py` runs cleanly and produces a summary report.
3. Metrics are actually computed (not just printed as "TODO").
4. The report shows reasonable numbers for the deterministic + LLM paths (when applicable).
5. Log the exact command + full output + summary numbers in `docs/implementation-log.md`.

---

## M9 — Docker + CI + Render Attempt

**Docker**  
Official Playwright Python image.  
`docker build -t testpilot .`  
`docker run --rm -p 7860:7860 --env-file .env testpilot`

**CI** (`.github/workflows/ci.yml`)  
- Checkout, Python 3.11, deps, Chromium
- Run unit + integration + e2e
- Start storefront
- Run evals
- Upload artifacts on failure
- No secrets, no LLM calls, deterministic

**Render**  
Attempt public Docker Web Service deployment by the checkpoint.

**Exit**  
- Local Docker works
- At least one real GitHub Actions run green after push
- Artifacts uploaded on failure

### Post-M9 Verification (Human / Independent Agent Must Confirm)

**Required checks:**

1. Local Docker build succeeds:
   ```bash
   docker build -t testpilot-slice .
   ```

2. Container runs and serves the app (smoke):
   ```bash
   docker run --rm -p 7860:7860 --env DEMO_MODE=true testpilot-slice
   ```
   - App becomes reachable on port 7860.
   - Basic health or landing page visible.

3. GitHub Actions workflow file is valid and at least one real run (after push) is green:
   - Check the Actions tab.
   - Confirm unit + integration + e2e (or storefront) jobs passed.
   - Confirm no secret leakage in logs.

4. Render attempt (or documented fallback):
   - If a public Render URL was created, verify it is reachable in incognito.
   - If Render was not possible, document exactly why and what commands were tried.
   - Record the final deployed (or fallback) state.

5. All artifacts from CI failures are actually uploaded and downloadable.

6. Full verification log entry with commands + outputs for build, run, CI status, and deployment result.

---

**Global Reminders for Every Milestone**
- Use tools for everything.
- Start servers with `background_process`.
- Record real commands + output in the log.
- Fix all failures before next milestone.
- Scope is frozen: one intent, one mutation, one repair category.

Keep this file open while implementing.

## Verification Process (MANDATORY After Every Milestone)

**Critical rule:**
The implementing agent (or developer) **must not** claim a milestone is complete by themselves.

After the code is written and the "Run & Verify" commands have been executed successfully:

1. A **human** (or a completely separate verification agent) must perform the "Post-MX Verification" checks listed below each milestone.
2. All checks must be run using real tools (`bash`, `background_process`, `read`, `grep`, etc.).
3. Record the **exact commands + full real output** (stdout + stderr) for each check.
4. Append a clear verification entry to `docs/implementation-log.md` in the required format.
5. Only when **all** verification items for that milestone have passed **and** been logged is the milestone considered accepted.

This two-person / two-agent gate prevents hallucinated success and keeps the project honest.

---

## Post-Milestone Verification Templates

The **Post-MX Verification** sections (located directly after each milestone's "Do not proceed" statement) are the **official minimum required human or separate-agent checks**.

They are **not optional**. A milestone is not considered accepted until:
- All listed verification items have been executed with real tools,
- Full command + output has been captured,
- Results have been appended to `docs/implementation-log.md`.

Use the exact commands (or equivalent that achieves the same proof). Add more checks if your implementation introduces additional behavior that needs proving.

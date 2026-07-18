# TestPilot — Milestone Quick Reference (Slice Only)

> **For new humans (or agents) reading this for the first time — recommended order**  
> 1. Header + Golden Intent + Scope + Agent Rules (what is locked and the non-negotiable rules).  
> 2. "What we are actually verifying in M1 (the three tests)" — read this before looking at code.  
> 3. "How a browser actually runs under pytest" — the core mental model (pytest runner vs real browser).  
> 4. "How to watch the tests interact with the real browser" — learn `--headed --slowmo`.  
> 5. Command flag reference (lookup table, not something to memorize on first read).  
> 6. Then follow the milestones top to bottom.  
>
> This document is deliberately structured as **understanding → commands → verification**.

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

**M2-specific gotchas (add to every future read):**
- Storefront server must be pre-started (port 8080, demo_site). background_process will reject if port busy.
- The "should fail" test waits full 30s — use targeted pytest nodes or direct python -c for verification to avoid timeout kills.
- Always create package __init__.py files for new testpilot subpackages.
- Prefer direct python -c for Post-M* verification when full pytest would exceed tool time limits.

**Flat layout:** `from testpilot.models import ...` (PYTHONPATH=. or editable install).

---

## How to read this document (recommended top-to-bottom order for new users)

**Goal of this ordering:**  
Prevent the common failure mode of "just copy-paste commands without understanding what is being proven or how the browser is actually involved."

Recommended first-pass reading order:

1. **Header block** (Golden Intent, only mutation, core contracts, agent rules, flat layout)  
   Establishes what is locked for the entire slice and the non-negotiable process rules.

2. **"What we are actually verifying in M1 (the three tests)"** (right after the reading guide)  
   This is the heart of the first gate.  
   - Table of the three tests + expected outcomes  
   - Why one test is *supposed* to fail  
   - How the mutation is implemented (static HTML + tiny JS reading `?mutation=...`)  
   Read this *before* opening the test file.

3. **"How a browser actually runs under pytest"** (Pytest vs Playwright vs pytest-playwright)  
   Explains the stack:  
   - pytest = test runner + reporting + selection  
   - Playwright = real browser automation (the thing that actually clicks)  
   - pytest-playwright = the plugin that starts the browser and injects the `page` fixture  
   Also explains headless by default and why you see Playwright stack traces in failures.

4. **"How to watch the tests interact with the real browser"**  
   Practical: `--headed --slowmo=700` (and how to use `page.pause()`).  
   This directly answers "I can't see any browser".

5. **Command flag reference**  
   Lookup table for every flag you will encounter (`-q`, `--tb=short`, `-k`, `::[chromium]`, `background_process`, etc.).  
   Not meant to be memorized on first read.

6. **M1 section and later milestones**  
   Now the "Run & Verify" blocks and Post-MX verification steps will be meaningful because you already understand:
   - what the tests are actually asserting
   - that a real browser is running (even when headless)
   - why certain commands use specific flags

This structure follows the principle: **concept → mechanism → observation → reference → application**.

---

## How a browser actually runs under pytest (Pytest vs Playwright vs pytest-playwright)

This is the most important mental model for the entire project.

**pytest** is only the test runner and framework.
- It finds files and functions that start with `test_`
- It runs them, catches exceptions, produces `.F.` summaries, supports `-q`, `--tb=short`, `-k`, `::`, etc.
- pytest itself has zero knowledge of browsers.

**Playwright** is the actual browser automation library.
- It launches real Chromium (or Firefox/WebKit).
- Your code calls `page.goto()`, `btn.click()`, `expect(...).to_have_text(...)`.
- When you see a stack trace starting with `playwright._impl._errors.TimeoutError`, a real browser instance was driving a real page.

**pytest-playwright** is the small pytest plugin that connects the two.
- When you write `def test_foo(page: Page):`, the plugin:
  - Starts a browser (Chromium by default)
  - Creates a fresh page
  - Injects that `page` object into your test function
  - Closes the browser after the test
- It also parametrizes every test by browser name. That is why collected tests are named `...[chromium]`.

**Headless by default**
- Playwright runs the browser **headless** (no visible window) unless you explicitly ask otherwise.
- This is why you usually see nothing on screen when you run `pytest`.
- The browser is still running — it is just invisible. The Playwright stack traces in failures are the proof.

**Why the output you saw proves a real browser was used**

```
python -m pytest tests/day0 -q --tb=short
.F.                                                                   [100%]
```

- `python -m pytest` starts the pytest runner.
- `.F.` means two tests passed, one failed (the middle one is *supposed* to fail for M1).

```
FAILED ...::test_golden_path_mutated_fails_with_brittle[chromium]
tests\day0\test_storefront.py:44: in test_...
    btn.click()
...
E   playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded.
E     - waiting for get_by_test_id("add-backpack")
```

- The test executed `btn.click()` using the brittle locator.
- A real Playwright-controlled Chromium tried for 30 seconds to find that element on the live page served at `http://localhost:8080`.
- Because of the mutation, the element was never there → timeout.
- The `playwright._impl` frames in the traceback are the smoking gun that a real browser session happened.

```
1 failed, 2 passed in 31.76s
```

- pytest's summary. Almost all the wall time was the deliberate 30-second wait on the "should fail" test.

This combination is why we say "we have both pytest and Playwright":
- pytest gives us structure, selection, reporting, and the fixture injection.
- Playwright (via the plugin) actually launches and controls the browser.

---

## What we are actually verifying in M1 (the three tests)

These three tests are the **only thing that must be green** before you are allowed to start M2.

They prove a very specific, narrow claim:

> A controlled UI change (`testid_removed`) breaks the original regression test (brittle locator).  
> The same business journey can be rescued by switching to a stable locator (repaired strategy).  
> Both versions still perform the real user action and assertion.

### The three tests, line by line

| Test name | Mutation in URL | Locator strategy | What the test does | Expected outcome |
|-----------|-----------------|------------------|--------------------|------------------|
| `test_golden_path_baseline_passes_with_brittle` | `?mutation=baseline` | brittle (`get_by_test_id`) | `page.goto(...)` → click using `data-testid="add-backpack"` → wait for cart count → assert it is "1" | **PASS** |
| `test_golden_path_mutated_fails_with_brittle` | `?mutation=testid_removed` | brittle (`get_by_test_id`) | Same as above, but the `data-testid` no longer exists | **FAILS** (Timeout looking for the locator) — this is *by design* |
| `test_golden_path_after_repair_works_on_mutated` | `?mutation=testid_removed` | repaired (`get_by_role`) | `page.goto(...)` → click using accessible name "Add Blue Backpack" → assert cart count "1" | **PASS** |

All three tests live in `tests/day0/test_storefront.py` and use the helper:

```python
from testpilot.models import resolve_locator

# Brittle path (what originally existed in the test)
btn = resolve_locator(page, "add_blue_backpack", "brittle")   # → page.get_by_test_id("add-backpack")

# Repaired path
btn = resolve_locator(page, "add_blue_backpack", "repaired")  # → page.get_by_role("button", name="Add Blue Backpack")
```

The `GOLDEN_FLOWSPEC` in `testpilot/models.py` only talks about **business steps** ("click add_blue_backpack", "assert cart_count == 1"). The locator strategy is deliberately kept out of the spec so that repair only changes *how* we find the element, not the intent.

### How the mutation actually happens (the storefront)

`demo_site/index.html` is static HTML + a few lines of client-side JS. No backend.

```html
<button id="add-btn">Add Blue Backpack</button>
<span id="count" data-testid="cart-count">0</span>
```

The JS reads `?mutation=...` from the URL:
- `baseline` → adds `data-testid="add-backpack"` to the button
- `testid_removed` → **removes** the `data-testid`

The visible text, role, and click behavior never change. Only the brittle locator breaks.

This is why:
- The baseline brittle test passes
- The mutated brittle test fails with "waiting for get_by_test_id("add-backpack")"
- The repaired test still succeeds on the mutated page

---

## How a browser actually runs under pytest (Pytest vs Playwright vs pytest-playwright)

This is the most important mental model for the entire project.

**pytest** is only the test runner and framework.
- It finds files and functions that start with `test_`
- It runs them, catches exceptions, produces `.F.` summaries, supports `-q`, `--tb=short`, `-k`, `::`, etc.
- pytest itself has zero knowledge of browsers.

**Playwright** is the actual browser automation library.
- It launches real Chromium (or Firefox/WebKit).
- Your code calls `page.goto()`, `btn.click()`, `expect(...).to_have_text(...)`.
- When you see a stack trace starting with `playwright._impl._errors.TimeoutError`, a real browser instance was driving a real page.

**pytest-playwright** is the small pytest plugin that connects the two.
- When you write `def test_foo(page: Page):`, the plugin:
  - Starts a browser (Chromium by default)
  - Creates a fresh page
  - Injects that `page` object into your test function
  - Closes the browser after the test
- It also parametrizes every test by browser name. That is why collected tests are named `...[chromium]`.

**Headless by default**
- Playwright runs the browser **headless** (no visible window) unless you explicitly ask otherwise.
- This is why you usually see nothing on screen when you run `pytest`.
- The browser is still running — it is just invisible. The Playwright stack traces in failures are the proof.

**Why the output you saw proves a real browser was used**

```
python -m pytest tests/day0 -q --tb=short
.F.                                                                   [100%]
```

- `python -m pytest` starts the pytest runner.
- `.F.` means two tests passed, one failed (the middle one is *supposed* to fail for M1).

```
FAILED ...::test_golden_path_mutated_fails_with_brittle[chromium]
tests\day0\test_storefront.py:44: in test_...
    btn.click()
...
E   playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded.
E     - waiting for get_by_test_id("add-backpack")
```

- The test executed `btn.click()` using the brittle locator.
- A real Playwright-controlled Chromium tried for 30 seconds to find that element on the live page served at `http://localhost:8080`.
- Because of the mutation, the element was never there → timeout.
- The `playwright._impl` frames in the traceback are the smoking gun that a real browser session happened.

```
1 failed, 2 passed in 31.76s
```

- pytest's summary. Almost all the wall time was the deliberate 30-second wait on the "should fail" test.

This combination is why we say "we have both pytest and Playwright":
- pytest gives us structure, selection, reporting, and the fixture injection.
- Playwright (via the plugin) actually launches and controls the browser.

---

## How to watch the tests interact with the real browser

By default everything is fast and invisible. Use these two flags:

- `--headed` — open a visible Chromium window
- `--slowmo=MS` — pause after every Playwright action (goto, click, type, etc.)

**Recommended first "I want to see it" commands** (after starting the server):

```bash
# Terminal 1
python -m http.server 8080 --directory demo_site
```

```bash
# Terminal 2 — watch the baseline test in slow motion
python -m pytest "tests/day0/test_storefront.py::test_golden_path_baseline_passes_with_brittle[chromium]" \
  --headed --slowmo=700 -q --tb=short
```

```bash
# Watch the repaired test on the mutated UI
python -m pytest "tests/day0/test_storefront.py::test_golden_path_after_repair_works_on_mutated[chromium]" \
  --headed --slowmo=700 -q --tb=short
```

```bash
# Watch the "should fail" test time out looking for the missing data-testid
python -m pytest "tests/day0/test_storefront.py::test_golden_path_mutated_fails_with_brittle[chromium]" \
  --headed --slowmo=500 -q --tb=short
```

Higher values (1000–1500) make it very easy to follow by eye. Lower values (300–500) are still observable but faster.

You can also add `page.pause()` inside a test temporarily if you want the Playwright Inspector to let you step through actions manually.

---

### Command flag reference (used throughout this checklist)

**Why we document exact flags everywhere**  
Every flag changes behavior. Future implementers (human or agent) must understand **why** a flag is present or absent so they can decide whether to keep, remove, or change it.

- `python -m pytest ...` (instead of bare `pytest`)  
  Runs pytest as a Python module. On Windows this is more reliable (avoids shebang/PATH problems). We use it consistently so commands work the same on Windows, Linux, and in CI.

- `tests/day0/test_storefront.py::test_foo[chromium]`  
  This is a **pytest node ID**: `file::test_function[browser]`.  
  Playwright's pytest plugin automatically parametrizes every test by browser, so the actual collected name ends with `[chromium]`.  
  We quote the whole string on Windows because `::` is special to PowerShell/cmd (it would treat it as a path otherwise).  
  We include `[chromium]` when we want the **exact** test.

- `-k "substring"` (keyword expression)  
  Selects tests whose id or docstring contains the substring.  
  We prefer this over `::` node IDs in many places because it works without quoting on Windows and is easier to read.  
  Example: `-k "baseline_passes"` will match the baseline test even if the exact parametrization changes.

- `-q` (quiet)  
  Only prints a summary line (e.g. `2 passed, 1 failed`).  
  We use `-q` in verification commands so the output that gets copied into `docs/implementation-log.md` stays small and focused on the result, not on collection noise.

- `--tb=short`  
  Shows a short traceback: the assertion line + a few frames.  
  Good default for "did it pass or fail?" checks. We want enough info to debug, but not 50 lines of internal frames.

- `--tb=line`  
  Even shorter: just `file:line: AssertionError`.  
  Used when we only care that the test reached the right point (e.g. during repair validation runs).

- `--tb=no` (sometimes used in CI/logs)  
  Suppresses tracebacks completely. Only the summary is shown. We avoid it in early milestones so failures are still debuggable.

- No `-s` (we usually omit it)  
  `-s` would show `print()` output and live logs. We omit it in verification runs so logs stay clean. When debugging a specific failure we may temporarily add `-s`.

- No `--headed` (we almost never pass it)  
  Playwright runs headlessly by default in these tests. We only use headed mode locally when actively debugging a locator or timing issue.

- `python -m http.server 8080 --directory demo_site`  
  Uses Python's built-in static server.  
  `8080` = the port the tests hard-code as `BASE = "http://localhost:8080"`.  
  `--directory demo_site` = only serve the controlled storefront, nothing else. This proves we are **not** using any web framework for M1.

- `background_process start ...` (agent/Kilo tool)  
  The mandated way to start long-running servers from within the agent.  
  We document it so humans know the equivalent manual command, and agents never fall back to `&` or `nohup`.

- `python -c "code here"`  
  Quick one-liner to import a module, call a function directly, or inspect state without writing a test file. Very useful for Post-MX verification steps.

- `docker run --rm -p 7860:7860 --env DEMO_MODE=true ...`  
  `--rm` = delete the container after it exits (keeps the machine clean).  
  `-p 7860:7860` = forward the container's port 7860 to the host so you can reach the Gradio UI.  
  `--env DEMO_MODE=true` = run without calling real LLMs or external services.

- `pytest -q` (full suite with no path)  
  Runs **every** test discovered under the configured testpaths (see `pytest.ini`).  
  We run the full suite at the end of each milestone to make sure we didn't break earlier work.

- `pytest tests/unit -q`, `pytest tests/integration -q`, `pytest tests/e2e -q`  
  We split by marker/layer so we can run fast feedback loops (unit first) before the slower browser tests.

When a command **omits** a flag, it is usually intentional (e.g. no `--headed`, no `-s`, no real API key). The comments next to the commands explain the reason.

---

## How to read this document (recommended top-to-bottom order for new users)

1. **Header + Golden Intent + Scope**  
   Understand what is frozen for the slice.

2. **"What we are actually verifying in M1"** (new big section)  
   Read this before looking at any test code. It explains the three tests, why one is *supposed* to fail, and how the mutation works in the storefront.

3. **"How a browser actually runs under pytest"** (Pytest / Playwright / pytest-playwright)  
   This is the mental model you need for every later milestone. Read it once, refer back to it often.

4. **"How to watch the tests interact with the real browser"** (headed + slowmo)  
   Learn how to make the browser visible and slow so you can observe behavior instead of guessing.

5. **Command flag reference**  
   Treat this as a lookup table. You do not need to memorize it on first read.

6. **M1 section**  
   Now the commands and Post-M1 checks will make sense in context.

7. **M2 and later**  
   Only after you have internalized the M1 picture (browser really runs, mutation is real, brittle vs repaired is the only difference).

This order is deliberately **understanding → commands → verification**, not the other way around.

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
# 1. Start the controlled static storefront (required by the tests)
#    Preferred for agents:
#      background_process start with: python -m http.server 8080 --directory demo_site
#    Human alternative (two terminals or background):
python -m http.server 8080 --directory demo_site

# 2. Run only the M1 storefront tests (the three golden path tests)
#    -q            → quiet: show only a summary line (dots + final counts)
#    --tb=short    → short tracebacks: failing assertion + minimal stack (enough to debug, not noisy)
# See the big explanatory sections at the top of this document for what these tests actually prove
# and how a real browser is running under the hood even though you see nothing.
python -m pytest tests/day0 -q --tb=short

# 3. Run the full test suite as a final safety check
#    -q → keep output small
python -m pytest -q
```

**Important — how the M1 tests actually work**  
See the detailed explanation at the very top of this document:

- "## What we are actually verifying in M1 (the three tests)"
- Table of the three tests + expected outcomes
- How the `?mutation=...` + JS in `demo_site/index.html` actually creates the broken state
- Why one test is *supposed* to fail

Do not start M2 until you understand that section. The commands below will then make sense.

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
   - `python -m http.server` = built-in static server (no web framework).
   - `8080` = port.
   - `--directory demo_site` = serve only the demo_site folder.
   - Confirm only static HTML/JS is used (no FastAPI/Flask/etc. processes running for the storefront).

2. Baseline test passes with brittle locator:
   ```bash
   # Use the full file path + parametrized node id (playwright adds [chromium])
   python -m pytest "tests/day0/test_storefront.py::test_golden_path_baseline_passes_with_brittle[chromium]" -q --tb=short
   ```
   - `::test_...[chromium]` = exact node ID (file + function + browser param).
   - `-q` = quiet (only summary).
   - `--tb=short` = short traceback.
   - Must show: `passed`

   Safer cross-platform alternative (recommended):
   ```bash
   python -m pytest tests/day0 -q -k "baseline_passes_with_brittle" --tb=short
   ```
   - `-k "..."` = keyword filter (matches test name). No `::` so it works on Windows without quoting issues.

3. testid_removed mutation causes the brittle test to fail:
   ```bash
   python -m pytest "tests/day0/test_storefront.py::test_golden_path_mutated_fails_with_brittle[chromium]" -q --tb=short
   ```
   - Same flags as above.
   - Must show: `failed`
   - Must contain evidence of data-testid / locator not found or similar (the point of the controlled mutation).

   Safer alternative:
   ```bash
   python -m pytest tests/day0 -q -k "mutated_fails_with_brittle" --tb=short
   ```

4. Repaired locator works on the mutated storefront:
   ```bash
   python -m pytest "tests/day0/test_storefront.py::test_golden_path_after_repair_works_on_mutated[chromium]" -q --tb=line
   ```
   - `--tb=line` = ultra-short traceback (just file:line).
   - Must show: `passed`

   Safer alternative:
   ```bash
   python -m pytest tests/day0 -q -k "after_repair_works_on_mutated" --tb=line
   ```

5. Mutation behavior / logic is present in the storefront (client-side JS):
   ```bash
   # Cross-platform portable check (source contains the JS that adds/removes the attribute)
   grep -n 'data-testid' demo_site/index.html || python -c "
   import re
   with open('demo_site/index.html') as f:
       print('found' if re.search(r'add-backpack', f.read()) else 'not found')
   "
   ```
   - The static source always contains the logic string (because JS decides at runtime).
   - Real presence/absence is proven by the passing vs failing tests above (the tests navigate with the query param and exercise the JS).

   Windows users: the grep or the python one-liner above both work in PowerShell / cmd.

6. Record the full verification run in `docs/implementation-log.md` with:
   - Exact commands executed
   - Full real output (stdout + stderr)
   - Pass/fail conclusion per test
   - Server start method used (background_process or manual)
   - Any environment notes (port, Windows path handling, etc.)

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
# 1. Start the storefront (only if your runner does not start it itself)
#    background_process start: python -m http.server 8080 --directory demo_site

# 2. Run the original M1 storefront tests (they must still pass)
python -m pytest tests/day0 -q --tb=short

# 3. Run the new runner/integration tests you just wrote
python -m pytest tests/integration -q --tb=short   # adjust path if you put runner tests elsewhere

# 4. Full suite as final gate
python -m pytest -q
```

Why we run these specific commands:
- `tests/day0` proves we did not break the original golden path while adding the runner.
- `tests/integration` exercises the new `run_brittle_journey(...)` API.
- Final `pytest -q` catches any accidental breakage in other layers.

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
   # python -c = run a one-liner snippet directly (no test file needed)
   python -c "from testpilot.browser import runner; print('import OK')"
   ```
   - This proves the module is importable and has no immediate syntax/import errors.

2. Baseline run produces a clean pass + manifest:
   ```bash
   # Example (adjust to actual runner API)
   python -c "
   from testpilot.browser.runner import run_brittle_journey
   result = run_brittle_journey(mutation_id='baseline')
   print(result)
   "
   ```
   - `mutation_id='baseline'` tells the runner which version of the storefront to hit.
   - We print the whole result dict so we can inspect `status`, `manifest_path`, etc.
   - Expected:
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
   - `mutation_id='testid_removed'` forces the storefront into the broken state.
   - Expected:
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

### M2 Lessons Learned (from real implementation)
These came from actual tool runs, collection issues, timeouts, and verification friction:

- **Storefront server is external**: `run_brittle_journey` and integration tests assume `python -m http.server 8080 --directory demo_site` is **already running**. `background_process start` will fail with "port already in use" if something is listening. Always start it first (background_process id or manual two terminals). Direct `python -c` calls and pytest will hang or error without it.
- **The "fail" test intentionally waits 30s**: M1 design makes `testid_removed + brittle` hit a full `TimeoutError`. Full `pytest tests/integration` can exceed agent tool timeouts (120s). 
  - Run **specific tests**: `python -m pytest "tests/integration/test_runner.py::test_..." -q --tb=line`
  - Or use **direct python -c** snippets for Post-M2 verification (much faster feedback, no pytest overhead).
- **Package __init__.py required**: Subpackages (`testpilot/browser/`, `testpilot/reporting/`) need an `__init__.py` (can be empty) for clean imports like `from testpilot.browser import runner`.
- **Prefer targeted verification order**:
  1. `python -m pytest tests/unit -q` (fast, no browser)
  2. One slow integration at a time
  3. The 6 Post-M2 `python -c` checks exactly as written (they prove the runner without waiting for full suite)
- **Artifacts & manifests**: Always ensure dir before write. Use timestamp+micro run_id. Manifest is written on **every** run (pass or fail). Screenshot only on fail.
- **Error excerpt truncation**: Enforce early (800 chars) — this data will later go to LLM prompts.
- **No auto-start fixture in M2**: Explicit decision. Keep storefront start explicit until later milestones.
- **Pytest collection noise**: Ignore asyncio / langsmith / playwright plugin warnings during `--collectonly`. As long as tests collect and run, they are fine.
- **Reproducibility**: Same mutation twice must produce different run_id + different `artifacts/<run_id>/` folders.
- **CRLF on Windows**: Git may warn on commit for .py/.md. Harmless for the slice; .gitattributes or consistent LF can be added later.

When implementing M2 (or re-verifying), follow the exact Post-M2 checks with real tool output. Do not claim "M2 green" until the 6 checks + unit tests pass and log is updated.

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
python -m pytest tests/unit -q          # fast, no browser
python -m pytest tests/integration -q   # runner + workflow integration
python -m pytest tests/e2e -q           # real Playwright (slowest)
python -m pytest -q                     # full suite as final gate
```

We run the layers in order of speed so you get early failure signals before the expensive browser tests.

**Manual Requirement**  
Execute end-to-end 3 times manually:
baseline pass → mutated failure → approve → validate → healed

Record real results in `docs/implementation-log.md`.

**Practical testing guide**  
See `docs/how-to-test-m3.md` for copy-paste commands to run the full M3 loop with visible browser (`--headed`, `headless=False`, `approve=True`). Includes the 3 required loops + manifest inspection.

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

### M3 Lessons Learned (from real implementation — 2026-07-18)
These came from actual tool runs, gate bugs, runner API gaps, and verification friction:

- **Runner generalization is required in M3**: The M2-only `run_brittle_journey` is insufficient. You must add `run_journey(..., strategy="brittle"|"repaired")` (and keep the old name as a wrapper) so the healing flow can actually execute the repaired journey after validation.
- **Healing coordinator must drive real browser**: `execute_deterministic_healing` (or equivalent) must call the runner for the brittle pass, produce diagnosis+proposal, then on explicit `approve=True` open a live page, run the validator (count/visible/enabled/click/assert), and if valid call the runner again with repaired strategy. Do not fake this with mocks for the slice.
- **Approval is a hard boolean gate**: The function must default `approve=False`. When False, validation must not run and final status must not be "healed". The later UI must only call with `approve=True` on an explicit user click of "Approve & Validate Repair".
- **Validator is the source of truth**: It must literally perform exactly these five checks in order for the repaired candidate: count()==1, is_visible(), is_enabled(), click(), expect(cart-count).to_have_text("1"). Any other behavior fails the contract.
- **Three full deterministic loops are mandatory**: After code + tests, a human (or separate agent) must execute and record:
  1. baseline → healed immediately (no proposal)
  2. testid_removed + approve=True → diagnosis + proposal + validation pass + repaired rerun → HEALED
  3. Independent second mutated+approve run
  Inspect the healing manifest for diagnosis, proposal, approved, validation.checks, repaired_result.
- **The 30s brittle timeout and external storefront prerequisite still apply exactly as in M2**. Use targeted pytest nodes or direct `python -c "from testpilot.workflow.healing import execute_deterministic_healing; ..."` for fast feedback. Never rely on full `pytest tests/integration` during active M3 work.
- **New subpackages need `__init__.py`**: `testpilot/workflow/` requires an (empty) `__init__.py`.
- **Re-run units after runner edits**: Any change to `testpilot/browser/runner.py` must be followed by `python -m pytest tests/unit -q` (especially tests importing `run_brittle_journey`).
- **Healing manifests are rich**: They contain the full state machine (diagnosis/proposal/validation). Runner-only manifests stay minimal. Both must be valid.
- **Windows shell**: Do not use Unix pipes (`| head`). Use PowerShell `Select-Object`, `Select-String`, `Out-String`.
- **M3 is 100% deterministic**: Must work with `DEMO_MODE=true`, no network, no OpenRouter calls. All tests and the three manual loops must prove this.
- **Sequence discipline**: Finish M3 (tests green + 3 recorded loops) before touching any Gradio UI code (M4). In M4 the UI will call the real M2/M3 services.

When implementing or re-verifying M3, follow the Post-M3 checks and record everything in `docs/implementation-log.md`. Only declare M3 complete after the three manual loops + manifest inspection have been performed by someone other than the primary implementer.

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
# Use background_process for the app (never & or nohup)
python -m pytest tests/unit -q
python -m pytest tests/integration -q   # UI handler tests (these call the real runner)
python -m pytest -q
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

### M4 Lessons Learned (from real implementation — 2026-07-18)
- **Keep callbacks thin**: All real logic (runner calls, M3 deterministic diagnosis/repair/validator/approval) lives in `testpilot/ui/services.py`. The Gradio layout only wires components and calls services. This is what made the 8 unit tests possible without launching the full app.
- **Gradio queue API**: `queue(concurrency_count=...)` can raise TypeError on current versions. Use `demo.queue(default_concurrency_limit=1)`. Always test the actual installed Gradio.
- **Mutation drives the real runner**: The radio must produce the exact `?mutation=...` URL used by `run_journey` / `run_original_regression`. Previews are not decorative — they must match the JS mutation behavior in `demo_site/index.html`.
- **Approval gate visibility**: "Approve & Validate Repair" and "Reject" must only become visible when a proposal exists and has not been approved yet. Enforce in both the service result and `gr.update(visible=...)`.
- **Fast simulation beats clicking**: During development use direct `python -c "from testpilot.ui import services; run_original_regression(...); approve_and_validate(...)"`. Add `headless=False` when you want to watch the browser.
- **Storefront + 30s timeout still rule**: Same external prerequisite and slow failure behavior as M2/M3. Use targeted nodes or services calls.
- **Launch the app with background_process**: Never & or nohup. Verify with urllib/webfetch. Check logs on failure (e.g. queue kwarg error).
- **Manifests are the audit**: After approve, the manifest must contain diagnosis, proposal, approved, validation.checks, repaired_result (services write the healing-style manifest).
- **New subpackage needs __init__.py**: `testpilot/ui/` required one.
- **Re-run full unit layer** after touching runner or services (M2/M3 tests import them).
- **M4 is 100% deterministic**: No OpenRouter, no LLM. All tests and the 9 manual acceptance steps must prove this.
- **Sequence discipline**: M3 must be fully green (tests + 3 recorded loops) before any Gradio code. M4 is only a thin UI over the existing M2 runner + M3 services.
- See the dedicated `docs/how-to-test-m4.md` for exact steps, simulation commands, and the 9 manual acceptance checklist.

When implementing or re-verifying M4, follow the Post-M4 checks and record everything. Only declare M4 complete after independent verification of the 7 items above plus the live UI flows.

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
python -m pytest tests/unit -q
python -m pytest tests/integration/test_llm_services.py -q   # only the LLM-related integration tests
python -m pytest -q
```

Must work with internet disabled in DEMO_MODE.

We run the specific LLM integration file so we can see both the real-LLM path (when a key is present) and the DEMO_MODE fallback path in the same command set.

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

### M5 Lessons Learned (from real implementation — 2026-07-18)
- **Automated tests must never call the real LLM**. The spec is strict: "Test suite never makes a real OpenRouter call." Always force `DEMO_MODE=true` or mock `_get_llm` / `ChatOpenAI.invoke` in integration tests.
- **Return (result, reasoning_mode) from every specialist**. The mode ("llm" or "fallback") must be propagated to RunResult and written to manifests.
- **Context building is sacred**: Use a strict whitelist of fields only. Truncate long strings (~800 chars). Never pass full HTML, traces, raw screenshots, base64, or unlimited logs — even for the real LLM path.
- **System prompts are loaded from files at runtime**. `prompts/<specialist>.md` content is the fixed system message. The user's natural language intent is **never** used as a system prompt.
- **Pydantic validation on every path**. Invalid JSON, schema error, provider error, or timeout → immediate deterministic fallback.
- **Fallback must be first-class and identical to M3**. Planner falls back to GOLDEN_FLOWSPEC. Diagnosis and Repair fall back to the existing deterministic functions in `testpilot/workflow/`.
- **Patch the right object in tests**. `patch.object(llm_client.ChatOpenAI, "invoke", ...)` or provide a full MagicMock instance. Patching the wrong name often fails silently.
- **Check DEMO_MODE and missing key early** in `llm_client.py`, before any network attempt.
- **Re-run the full unit layer** after introducing the `testpilot/llm/` package (models and reporting helpers are widely imported).
- **M5 still follows narrow-specialist rules**: No sub-agents, no autonomous browsing, no raw code execution. Human approval remains a hard gate (unchanged).
- **Sequence discipline**: M4 must be solid and verified before introducing LLM specialists. The deterministic path must continue to work unchanged for DEMO_MODE and CI.
- See the dedicated `docs/how-to-test-m5.md` for DEMO_MODE verification steps, mocked integration test patterns, context inspection, and optional real-key manual testing.

Only declare M5 complete after a human (or separate agent) has run the Post-M5 checks and the lessons above have been applied.

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
python -m pytest tests/unit/test_graph.py -q
python -m pytest tests/integration/test_workflow.py -q
python -m pytest -q
```

Every branch tested.

We run the graph-specific unit and integration tests first (they use deterministic stubs), then the full suite to make sure nothing else broke.

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

This is **not** a pytest command. It is a custom evaluation runner that executes the cases in `evals/repair_cases.json` and prints healing/approval metrics. We run it explicitly because it is part of the acceptance criteria even though it is not under `pytest`.

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

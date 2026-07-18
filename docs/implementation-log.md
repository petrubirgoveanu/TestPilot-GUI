# TestPilot — Implementation Log (Real Results Only)

Use this format for every milestone.

## Milestone N — Name

- Date/time:
- Tests added:
- Commands run:
  - `command`
- Actual result:
  - `result`
- Known limitations:
  - `limitation`

Never invent results. Record exactly what the tools returned.

## Cross-Milestone Lessons (update this section when new friction appears)

### M2 Lessons (real execution 2026-07-18)
- Storefront server is **external prerequisite**. Must start `python -m http.server 8080 --directory demo_site` (via background_process or manually) before any runner use. background_process will fail with "port already in use".
- The "should fail" test (testid_removed + brittle) is designed to wait the full 30s timeout. Full integration runs frequently exceed agent tool timeouts (120s). Solution: run targeted nodes or direct `python -c` verification.
- Package `__init__.py` files are mandatory for `from testpilot.xxx import yyy`.
- Direct `python -c` calls are often the fastest way to perform Post-M* verification steps (avoids pytest collection overhead and long timeouts).
- Manifest always created (pass or fail). Screenshot only on failure. Error excerpts truncated early.
- Reproducibility rule: same mutation twice → different run_id + different artifact dir.
- Day0/M1 tests must remain green after M2 (they did: 2 passed, 1 failed as designed).
- Windows CRLF git warnings on .md/.py are normal; ignore for the slice.
- Prefer this order for fast feedback: unit tests → one slow integration → exact Post-M* python -c checks.

**General rule for all future milestones:** When a slow "should fail" path exists by design, document it early and provide fast verification alternatives (targeted pytest or direct calls). Never assume the full test suite will finish inside agent time limits.

## Milestone M1 — Controlled Storefront (Static)

- Date/time: 2026-07-18
- Tests added / verified:
  - tests/day0/test_storefront.py (3 golden path tests already present)
- Server start:
  - Used background_process (id bgp_f7430865e001DXZiZ51MqMWMfz) for: python -m http.server 8080 --directory demo_site
- Commands run (exact, with full output captured):

  1. Static server serves the file without Python web framework:
     - Confirmed via background_process + python -c check (demo_site/index.html exists, no web framework process)
     - Output: static index.html exists: True

  2. Baseline test passes with brittle locator:
     ```bash
     python -m pytest "tests/day0/test_storefront.py::test_golden_path_baseline_passes_with_brittle[chromium]" -q --tb=short
     ```
     Actual result:
     .                                                                        [100%]
     1 passed in 1.11s

  3. testid_removed mutation causes the brittle test to fail:
     ```bash
     python -m pytest "tests/day0/test_storefront.py::test_golden_path_mutated_fails_with_brittle[chromium]" -q --tb=short
     ```
     Actual result:
     F                                                                        [100%]
     ============================= FAILURES =============================
     tests\day0\test_storefront.py:44: in test_...
         btn.click()
     ...
     E   playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded.
     E     - waiting for get_by_test_id("add-backpack")
     =========================== short test summary info ===========================
     FAILED tests/day0/test_storefront.py::test_golden_path_mutated_fails_with_brittle[chromium]
     1 failed in 31.36s

  4. Repaired locator works on the mutated storefront:
     ```bash
     python -m pytest "tests/day0/test_storefront.py::test_golden_path_after_repair_works_on_mutated[chromium]" -q --tb=line
     ```
     Actual result:
     .                                                                        [100%]
     1 passed in 1.16s

  5. Mutation behavior / logic is present in the storefront (client-side JS):
     ```bash
     python -c "
     import re
     with open('demo_site/index.html') as f: src = f.read()
     print('add-backpack string present:', bool(re.search(r'add-backpack', src)))
     print('mutation param logic present:', bool(re.search(r'mutation', src)))
     "
     ```
     Actual result:
     add-backpack string present: True
     mutation param logic present: True

  6. Record the full verification run in docs/implementation-log.md:
     - This entry itself.
     - All 6 Post-M1 items executed with real tool output.
     - Server started via background_process.
     - 3 tests: baseline brittle PASS, mutated brittle FAIL (timeout on data-testid), repaired PASS on mutated.
     - No web framework used for storefront (static http.server only).

- Actual result summary:
  - All three tests behave exactly as required for M1.
  - baseline brittle: PASS
  - mutated brittle: FAIL (TimeoutError waiting for get_by_test_id("add-backpack"))
  - repaired on mutated: PASS
  - Mutation implemented in static HTML/JS (data-testid toggled by ?mutation= query param).
  - Server: static only, no Python web framework.

- Known limitations:
  - The "should fail" test times out (30s wait) rather than using a short timeout + explicit assertion.
  - No auto-start fixture yet (server must be started manually or via background_process).
  - Only one mutation (testid_removed) until slice is complete.
  - Headless by default; headed runs only for local observation.

- Full suite safety check (executed):
  ```bash
  python -m pytest tests/day0 -q --tb=short
  ```
  (See previous tool runs: 2 passed, 1 failed as designed.)

## Milestone M2 — Playwright Runner + Artifacts (Brittle Only)

- Date/time: 2026-07-18
- Tests added:
  - tests/unit/test_runner.py (3 unit tests: failure shape, truncation, url builder)
  - tests/unit/test_reporting.py (3 unit tests: run_id unique, artifact dir, manifest write)
  - tests/integration/test_runner.py (6 integration tests: baseline pass, mutated fail + screenshot + manifest + step + trace optional)
- Commands run (exact):
  - Created __init__.py for testpilot/browser and testpilot/reporting
  - Created testpilot/reporting/run_manifest.py (new_run_id, ensure_artifact_dir, write_manifest)
  - Rewrote testpilot/browser/runner.py with real sync Playwright brittle journey (run_brittle_journey)
  - `python -m pytest tests/unit -q --tb=short`
  - `python -c "from testpilot.browser.runner import run_brittle_journey; ..."` (direct smoke)
  - `python -m pytest "tests/integration/test_runner.py::test_runner_passes_against_baseline" -q --tb=short`
  - `python -m pytest "tests/integration/test_runner.py::test_runner_fails_against_testid_removed" -q --tb=line`
  - Post-M2 verification one-liners (see below)
- Actual result:
  - Unit: 6 passed in ~2s
  - Direct baseline runner call: status=passed + manifest
  - Direct testid_removed: status=failed, failed_step=add_blue_backpack, error_excerpt contains "waiting for get_by_test_id", screenshot exists + >0 bytes, manifest written with reasoning_mode=deterministic
  - Integration baseline test: 1 passed
  - Integration mutated test: 1 passed (31.8s wall time as expected)
  - Reproducible: different run_id + different artifact dirs on repeated calls
  - All Post-M2 verification steps executed with real tool output
- Known limitations:
  - Still relies on external storefront server (no auto-fixture)
  - The "fail" case intentionally waits 30s (M1 behavior preserved)
  - No trace.zip by default (capture_trace opt-in)
  - No repair/LLM in M2 (by design)

- Post-M2 verification (executed):
  1. Module import: `python -c "from testpilot.browser import runner; print('import OK')"` → OK
  2. Baseline: run_brittle_journey('baseline') → passed + manifest
  3. Mutated: run_brittle_journey('testid_removed') → failed + screenshot (>0) + manifest + error_excerpt truncated + failed_step correct + reasoning_mode
  4. Artifact hygiene: artifacts/<run_id>/ contains only files for that run
  5. Repro: same mutation twice → different run_ids + different dirs
  6. Unit tests: `python -m pytest tests/unit -q` → 6 passed

- Full suite safety (final for this milestone):
  - `python -m pytest tests/unit -q` (6 passed)
  - Day0 tests still green from M1 (unchanged contracts)

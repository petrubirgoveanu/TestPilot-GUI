# How to Test M8 — Evaluation Suite

This guide explains what the evaluation suite is, why it exists, and how to run it.

The M8 evaluation suite is a product-level harness that validates the healed workflow using a small set of grounded cases. It is intentionally separate from pytest because it measures the actual user-facing metrics that matter for this project:

- Does a supported UI mutation fail the brittle original journey?
- Does the system propose a repair for the same intent?
- Does the human approval gate enforce the strategy policy?
- Does the repaired journey pass after validation?
- Are metrics computed and reported clearly?

The current implementation is deterministic: it uses the same controlled storefront, the deterministic healing path, and the locked mutation `testid_removed`. This makes M8 a strong audit check for the complete self-healing flow.

---

## 1. What evals are and why they help

An evaluation is not a unit test. It is a scenario-based verification harness that exercises the full healing workflow and reports results in terms of success rate and approval compliance.

`evals/run_evals.py` is the runner.
`evals/repair_cases.json` is the source of truth for the supported scenarios.

Evals help this project because they:

- enforce a stable case definition format
- validate the actual failure mode (`expected_category`, `expected_failed_step`)
- ensure the repair strategy matches the policy (`allowed_strategies`)
- check that the full approved healing loop ends in the expected final state
- provide a reusable audit report for independent verification

This is especially important when multiple milestones are involved: M3 builds the healing flow, M4 surfaces it in the UI, M5 adds narrow LLM specialists, and M8 confirms the product still behaves as expected.

---

## 2. Required files

- `evals/repair_cases.json`
- `evals/run_evals.py`

If either file is missing, M8 is not implemented.

---

## 3. Prerequisites

From the project root:

```cmd
python -m pip install -r requirements.txt
python -m pip install ruff
python -m playwright install chromium
python -m ruff check . --select E,W,F,C90 --line-length 120 --no-cache
```

Set the environment for deterministic evaluation:

```cmd
set DEMO_MODE=true
set LANGSMITH_TRACING=false
```

Then start the controlled storefront on port 8080:

```cmd
python -m http.server 8080 --directory demo_site
```

Verify the storefront loads:

```cmd
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/index.html?mutation=testid_removed', timeout=3).status)"
```

Expected output: `200`

---

## 4. How to run the evaluation suite

From the project root:

```cmd
DEMO_MODE=true python evals/run_evals.py
```

If your shell does not support `DEMO_MODE=true` prefixing, use this equivalent command:

```cmd
python -c "import os, sys; os.environ['DEMO_MODE'] = 'true'; from evals.run_evals import main; sys.exit(main())"
```

This is not a pytest command.

If the harness returns exit code `0`, all evaluation cases passed and the metrics were fully satisfied.

---

## 5. What the output means

Example output:

```text
Cases executed: 1
Cases healed: 1
Healing success rate: 1/1 (100%)
Approval-gate compliance: 1/1 (100%)
- testid_removed: status=healed, healed=True, approval_compliant=True
```

- `Cases executed` = number of scenarios in `evals/repair_cases.json`
- `Cases healed` = number of scenarios that reached the expected final state
- `Healing success rate` = healed / executed
- `Approval-gate compliance` = number of cases where the proposed repair strategy was permitted by the case definition

Each case line includes:

- `status`: the final workflow status returned by `execute_deterministic_healing`
- `healed`: whether the final status matched the expected final status
- `approval_compliant`: whether the proposed repair strategy was allowed for that case

If a case does not pass, the harness reports a `message` explaining the mismatch.

---

## 6. Schema requirements for `repair_cases.json`

Each case is a JSON object with these required fields:

- `id` — unique case identifier
- `user_intent` — natural-language intent description
- `mutation_id` — storefront mutation to run
- `expected_category` — expected failure category, e.g. `locator_not_found`
- `expected_failed_step` — the exact failed step target, e.g. `add_blue_backpack`
- `allowed_strategies` — list of permitted repair strategies, e.g. `["repaired"]`
- `expected_final_status` — the final workflow status expected after approval, e.g. `healed`

The current minimum case is:

```json
[
  {
    "id": "testid_removed",
    "user_intent": "Add the blue backpack to cart and confirm the cart count is 1.",
    "mutation_id": "testid_removed",
    "expected_category": "locator_not_found",
    "expected_failed_step": "add_blue_backpack",
    "allowed_strategies": ["repaired"],
    "expected_final_status": "healed"
  }
]
```

If the file is malformed or missing required fields, the harness fails fast with a nonzero exit code.

---

## 7. Why this is not a pytest test

The evaluation harness is a product acceptance runner, not a unit or integration test.

Use pytest for code-level correctness. Use the M8 harness to verify the supported story-level outcome metrics.

This means:

- M8 should be run explicitly, not as part of `python -m pytest`
- M8 verifies metrics, not implementation details
- M8 outputs a human-readable summary report
- The same code can still be covered by pytest, but the harness is the product audit gate

---

## 8. Common failure modes

- `DEMO_MODE` not set or overwritten
  - Set `DEMO_MODE=true` before running the harness.
- Port 8080 not serving the storefront
  - Restart the server with `python -m http.server 8080 --directory demo_site`
  - Confirm `http://localhost:8080/index.html?mutation=testid_removed` loads
- The brittle run unexpectedly passes
  - This means the mutation is not causing the failure the case expects. Check that the mutation query param is `testid_removed` and that the storefront has the expected brittle locator removed.
- `approval_compliant=False`
  - Confirm `evals/repair_cases.json` allows the actual proposed strategy.
  - The current deterministic repair strategy is `role` for `testid_removed`.
- `healed=False`
  - Inspect the per-case message.
  - Run the same mutation manually through `execute_deterministic_healing(..., approve=True)` to debug.

---

## 9. Best practices for future cases

- Keep cases narrow and realistic.
- Use the exact target name from `testpilot/models.py` for `expected_failed_step`.
- Keep `allowed_strategies` as small as possible.
- Add only one new mutation at a time.
- If you add a new mutation, update deterministic diagnosis and repair helpers before adding the case.

---

## 10. Verification checklist

1. Start the storefront:
   ```cmd
   python -m http.server 8080 --directory demo_site
   ```
2. Run the harness:
   ```cmd
   DEMO_MODE=true python evals/run_evals.py
   ```
3. Confirm the summary shows:
   - `Healing success rate: 1/1 (100%)`
   - `Approval-gate compliance: 1/1 (100%)`
4. Confirm the case line shows `status=healed`, `healed=True`, and `approval_compliant=True`.
5. Log the exact command and full output in `docs/implementation-log.md`.

---

## 11. Related files

- `evals/repair_cases.json` — evaluation case definitions
- `evals/run_evals.py` — evaluation harness runner
- `docs/milestone-checklist.md` — M8 acceptance criteria
- `docs/implementation-log.md` — record of M8 run commands and results
- `testpilot/workflow/healing.py` — deterministic healing path used by the harness

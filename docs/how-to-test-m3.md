# How to Test M3 — Deterministic Repair + Human Approval + Validation

This guide shows you how to manually verify the M3 implementation **with the browser visible**.

M3 proves the complete deterministic healing loop:

1. Baseline run passes (no repair needed).
2. `testid_removed` mutation + brittle locator → fails.
3. System produces deterministic diagnosis + repair proposal.
4. **Explicit human approval** is required (hard gate).
5. Validator checks: unique, visible, enabled, click succeeds, cart count becomes "1".
6. Full journey reruns using the repaired locator.
7. Final status is `HEALED` **only** after the repaired rerun passes.

---

## 1. Prerequisites

```powershell
# From the project root
python -m pip install -r requirements.txt
python -m pip install ruff
playwright install chromium
python -m ruff check . --select E,W,F,C90 --line-length 120 --no-cache

# Quick sanity check
python -c "from testpilot.workflow.healing import execute_deterministic_healing; print('M3 code ready')"
```

---

## 2. Start the Controlled Storefront (MANDATORY)

Open a **separate terminal** and run:

```powershell
python -m http.server 8080 --directory demo_site
```

Leave this running for the entire test session.

> **Important**: All M3 tests and healing flows require this static server on port 8080. `background_process` or manual terminal both work.

---

## 3. Watch the Original Golden Tests with Visible Browser (M1 behavior)

```powershell
# Baseline — should succeed
python -m pytest "tests/day0/test_storefront.py::test_golden_path_baseline_passes_with_brittle[chromium]" `
  --headed --slowmo=700 -q --tb=short

# Mutated + brittle — deliberately fails (watch the 30s timeout)
python -m pytest "tests/day0/test_storefront.py::test_golden_path_mutated_fails_with_brittle[chromium]" `
  --headed --slowmo=500 -q --tb=short

# Mutated + repaired — succeeds
python -m pytest "tests/day0/test_storefront.py::test_golden_path_after_repair_works_on_mutated[chromium]" `
  --headed --slowmo=700 -q --tb=short
```

**Tips**:
- Use `--slowmo=1000` or `1200` for easier observation.
- `--headed` opens a real Chromium window.
- The middle test is *supposed* to fail (it waits the full 30s).

---

## 4. Direct Runner Calls (Fastest Way to See Brittle vs Repaired)

```powershell
# 1. Brittle on baseline → quick pass
python -c "
from testpilot.browser.runner import run_journey
res = run_journey('baseline', strategy='brittle', headless=False, timeout_ms=10000)
print('Status:', res['status'])
print('Locator:', res.get('locator'))
"

# 2. Brittle on mutated → visible timeout (30s)
python -c "
from testpilot.browser.runner import run_journey
res = run_journey('testid_removed', strategy='brittle', headless=False, timeout_ms=10000)
print('Status:', res['status'])
print('Error excerpt:', res.get('error_excerpt', '')[:150])
"

# 3. Repaired on mutated → succeeds visibly
python -c "
from testpilot.browser.runner import run_journey
res = run_journey('testid_removed', strategy='repaired', headless=False, timeout_ms=10000)
print('Status:', res['status'])
print('Locator:', res.get('locator'))
"
```

---

## 5. Full M3 Healing Flow — The Complete Experience (Recommended)

This single command executes the entire M3 loop with a visible browser:

```powershell
python -c "
from testpilot.workflow.healing import execute_deterministic_healing
print('=== M3 Full Deterministic Healing Loop ===')
result = execute_deterministic_healing(
    'testid_removed',
    headless=False,   # browser is visible
    approve=True,     # explicit human approval (the hard gate)
    attempt=1
)
print()
print('Final status      :', result['status'])
print('Approved          :', result.get('approved'))
print('Validation passed :', result.get('validation', {}).get('passed'))
print('Validation checks :', result.get('validation', {}).get('checks'))
print('Run ID            :', result['run_id'])
print('Manifest path     :', result.get('manifest_path'))
"
```

**What you should observe**:
1. First browser action: tries `get_by_test_id("add-backpack")` → fails with timeout.
2. Validator phase: opens browser, finds button by role + "Add Blue Backpack", clicks it, cart count becomes 1.
3. Final repaired journey: full three-step run succeeds.
4. Only after the repaired rerun passes does it report `status: "healed"`.

---

## 6. Inspect the Run Manifest (Proof of M3 State Machine)

After any healing run:

```powershell
# Show the most recent healing manifest
Get-ChildItem artifacts -Directory | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 | 
    ForEach-Object {
        $m = Join-Path $_.FullName 'run_manifest.json'
        if (Test-Path $m) {
            Get-Content $m | ConvertFrom-Json | ConvertTo-Json -Depth 6
        }
    }
```

**Expected fields in a healed run manifest**:
- `diagnosis`
- `proposal` (with `new_locator` using `get_by_role`)
- `approved: true`
- `validation.checks` containing: `["unique", "visible", "enabled", "click_success", "cart_count==1"]`
- `repaired_result` with `status: "passed"`
- Final `status: "healed"`

---

## 7. Mandatory: Execute 3 Full Deterministic Loops

You must personally run the complete flow at least **three times**:

1. **Loop 1 (baseline)**:
   ```powershell
   python -c "
   from testpilot.workflow.healing import execute_deterministic_healing
   r = execute_deterministic_healing('baseline', headless=False, approve=False, attempt=1)
   print('Loop 1 status:', r['status'], 'approved:', r.get('approved'))
   "
   ```

2. **Loop 2 (mutated + approve)** — expect `healed`:
   ```powershell
   python -c "
   from testpilot.workflow.healing import execute_deterministic_healing
   r = execute_deterministic_healing('testid_removed', headless=False, approve=True, attempt=1)
   print('Loop 2 status:', r['status'])
   "
   ```

3. **Loop 3 (independent mutated + approve)** — different `run_id`, also `healed`.

Record the three `run_id`s and the final status for each.

---

## 8. Quick Verification Checklist

Run these and confirm:

- [ ] `python -m pytest tests/unit -q` → all green (12+ tests)
- [ ] Headed baseline test passes visibly
- [ ] Headed mutated brittle test visibly fails (timeout on `data-testid`)
- [ ] `execute_deterministic_healing(..., approve=True, headless=False)` returns `status: "healed"`
- [ ] Manifest for the healed run contains `diagnosis`, `proposal`, `approved`, `validation`, and `repaired_result`
- [ ] Three full loops executed and recorded (as above)
- [ ] No real LLM / OpenRouter calls were made (`DEMO_MODE` + deterministic only)

---

## 9. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Port 8080 already in use | Previous http.server still running | Kill the process or use a different port (update `BASE_URL` if you change it) |
| Browser never appears | `headless=True` (default in many calls) | Explicitly pass `headless=False` |
| Tests hang | Storefront not running | Start `python -m http.server 8080 --directory demo_site` first |
| 30-second wait on failure | By design for the "should fail" case | Use `--slowmo=300` or accept it; use `python -c` for faster healing verification |
| Manifest not found | Run failed before writing | Check the `artifacts/<run_id>/` folder was created |
| Import errors after changes | Missing `__init__.py` | Ensure `testpilot/workflow/__init__.py` exists |

---

## Related Files

- `docs/milestone-checklist.md` — full M3 specification and Post-M3 verification steps
- `docs/implementation-log.md` — actual commands + real output from the original M3 implementation
- `testpilot/workflow/healing.py` — the main coordinator (`execute_deterministic_healing`)
- `testpilot/browser/runner.py` — supports `strategy="brittle" | "repaired"`

Run the steps in this file exactly as written to independently verify M3.

## M9 Carry-Forward Note

When running these commands in CI/automation, follow the deterministic and artifact rules in `docs/how-to-test-m9.md`.

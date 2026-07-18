# How to Test M4 — Gradio UI Wired to Real Runner + Deterministic Repair

This guide lets you manually verify the M4 implementation **with the browser visible where possible**.

M4 delivers the product surface:
- Graphical “UI Change Lab” mutation selector (`gr.Radio`)
- Before/after preview that matches the actual storefront mutation
- “Generate & Run Original Regression” button that calls the **real** M2 runner
- Timeline, error, screenshot, diagnosis, repair diff
- **Explicit** Approve / Reject buttons (hard human gate from M3)
- Final `HEALED` only after validated repaired rerun
- Downloadable JSON manifest

**Important**: M4 uses the real runner + deterministic M3 services. No LLM calls.

---

## 1. Prerequisites

```powershell
python -m pip install -r requirements.txt
playwright install chromium

# Confirm M4 code
python -c "from testpilot.ui.layout import build_ui; from testpilot.ui import services; print('M4 ready')"
```

---

## 2. Start the Controlled Storefront (MANDATORY)

In a **separate terminal**:

```powershell
python -m http.server 8080 --directory demo_site
```

Leave it running.

---

## 3. Start the M4 Gradio App (use background_process in agents)

```powershell
python app.py
```

App should be reachable at:

```
http://127.0.0.1:7860
```

Verify quickly:

```powershell
python -c "
import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:7860', timeout=3).status)
"
```

---

## 4. Manual UI Acceptance (the 9 required steps)

Perform these **with the live UI** (or via `services` for fast simulation + headed observation).

### Step-by-step with the browser UI

1. Open http://127.0.0.1:7860
2. **Select Baseline**
   - Preview panels should be identical
   - Description says “No UI change”
   - Target URL contains `?mutation=baseline`
3. **Select “Remove test ID”**
   - Preview shows `data-testid` struck or removed on the right
   - Retained `aria-label="Add Blue Backpack"` is highlighted
   - Target URL now contains `?mutation=testid_removed`
4. Confirm the accessible name is still visible in the preview text.
5. Click **Generate & Run Original Regression**
   - For `testid_removed` you should see:
     - Status becomes “failed”
     - Error excerpt (timeout waiting for `get_by_test_id`)
     - Screenshot (if failure.png was captured)
     - Diagnosis text (deterministic M3 string)
     - Repair diff showing `get_by_test_id` → `get_by_role("button", name="Add Blue Backpack")`
6. **Approval controls**:
   - “Approve & Validate Repair” and “Reject Repair” must be **hidden or disabled** before any proposal.
   - After a `testid_removed` failure they become visible **only** when a proposal is pending.
7. Click **Approve & Validate Repair**
   - Validator runs (unique, visible, enabled, click, cart count == 1)
   - Repaired journey reruns
   - Final status becomes `HEALED` (only if the full repaired run passes)
8. Timeline updates through:
   `Planned → Running → Failed → Diagnosed → Repair proposed → Approved → Validated → Healed`
9. Download the manifest JSON and open it.
   - Must contain: `diagnosis`, `proposal`, `approved: true`, `validation.checks`, `repaired_result.status`

---

## 5. Fast Simulation via Services (recommended during development)

You can exercise the exact same logic the UI uses without clicking:

```powershell
python -c "
from testpilot.ui import services

print('=== Baseline ===')
print(services.get_mutation_description('baseline'))
print(services.build_target_url('baseline'))

print('\n=== Remove test ID ===')
print(services.get_mutation_description('testid_removed'))
print(services.build_target_url('testid_removed'))

print('\n=== Run on testid_removed (real brittle runner) ===')
run = services.run_original_regression('testid_removed', headless=True)
print('status:', run['status'])
print('proposal present:', run.get('proposal') is not None)
print('diagnosis snippet:', (run.get('diagnosis') or {}).get('reason','')[:80])

if run.get('proposal'):
    print('\n=== Approve & Validate (real validator + repaired run) ===')
    approved = services.approve_and_validate(run, headless=True)
    print('approved:', approved.get('approved'))
    print('final_status:', approved.get('final_status'))
    print('validation checks:', (approved.get('validation') or {}).get('checks'))
    print('manifest:', approved.get('manifest_path'))
"
```

For **visible browser** during simulation, pass `headless=False` in the calls above (or modify temporarily).

---

## 6. Inspect Manifests

```powershell
Get-ChildItem artifacts -Directory | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 | 
    ForEach-Object {
        $m = Join-Path $_.FullName 'run_manifest.json'
        if (Test-Path $m) { Get-Content $m | ConvertFrom-Json | ConvertTo-Json -Depth 5 }
    }
```

Look for the M4 healing-style fields after an approved run.

---

## 7. Quick Verification Checklist (must all pass)

- [ ] `python -m pytest tests/unit -q` → 20+ passed (including 8 new UI unit tests)
- [ ] `python -m pytest tests/integration/test_ui_handlers.py -q` (targeted nodes)
- [ ] App starts cleanly via `python app.py` and returns 200 on port 7860
- [ ] Selecting Baseline → no change preview + correct URL
- [ ] Selecting Remove test ID → preview shows removal + correct URL
- [ ] Run on `testid_removed` produces real failure + diagnosis + proposal (real runner)
- [ ] Approve button only appears when proposal is pending
- [ ] Approve leads to validation pass + final `HEALED`
- [ ] Manifest downloadable and contains full state (diagnosis, proposal, approved, validation, repaired_result)
- [ ] No real LLM / OpenRouter calls (DEMO_MODE + deterministic)

---

## 8. Headed Observation Tips

- For visual debugging you can temporarily edit services calls to use `headless=False`.
- The brittle failure will still take ~30s — this is by design.
- Use two browser windows: one for the Gradio UI, one to watch Playwright (if you patch `headless=False`).

---

## 9. Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Port 8080 busy | Storefront already running from previous session | Kill previous http.server |
| App fails to start | Old `concurrency_count` in queue() call | Use `demo.queue(default_concurrency_limit=1)` |
| Approval buttons never appear | Run was on `baseline` or no proposal was generated | Must run on `testid_removed` brittle failure |
| Screenshot missing | Run passed or Playwright screenshot failed silently | Normal for baseline passes |
| Full integration test times out | 30s brittle failure + multiple tests | Run specific nodes or use `python -c` on services |

---

## Related Files

- `docs/milestone-checklist.md` — M4 spec + Post-M4 verification steps
- `docs/implementation-log.md` — real commands + output from the M4 implementation
- `testpilot/ui/services.py` — the business logic the UI calls
- `testpilot/ui/layout.py` — the Gradio definition
- `app.py` — entry point

Run the steps in this file (or the 9 manual acceptance steps in the live UI) to independently verify M4.

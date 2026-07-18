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

### Clean up previous http.server (port 8080) on Windows

The controlled storefront runs on port 8080. If a previous `python -m http.server` is still running, you will get a "port already in use" error when trying to start it again.

**Command Prompt (cmd.exe) – concrete steps:**

1. **Find the PID** of the process using port 8080:
   ```
   netstat -ano | findstr :8080
   ```
   Look at the **last column** — that is the PID (for example: `12345`).

2. **Kill the old http.server process** (replace `12345` with the PID you found):
   ```
   taskkill /PID 12345 /F
   ```

**One-liner to kill (copy and paste directly into cmd):**
```
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8080') do @taskkill /PID %a /F
```

3. After killing, start a fresh storefront in a new terminal:
   ```
   python -m http.server 8080 --directory demo_site
   ```

**Prevention tip:**  
Always stop the storefront cleanly by pressing **Ctrl + C** in its terminal before closing it.  
Before starting a new one, quickly check if the port is free:
```
netstat -ano | findstr :8080
```

---

## 2. Start the Controlled Storefront (MANDATORY)

In a **separate terminal**, run from the **project root** (the directory containing `demo_site/`):

```cmd
python -m http.server 8080 --directory "D:\My-AI-Journey\Outskill-Engineering-Accelerator-14Days-Course\HackathonProject\demo_site"
```

> **Critical:** Always use the **full absolute path** to `demo_site`. If you run the command from the wrong working directory (e.g. `C:\Users\petru`), Python will look for `demo_site` there, not find `index.html`, and serve 404s for every Playwright request — causing a misleading failure screenshot.

Verify it works by opening in your browser:
```
http://localhost:8080/index.html?mutation=testid_removed
```
You should see "Demo Storefront — Version: testid_removed" with the "Add Blue Backpack" button.

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

Verify quickly — open this URL in your browser, you should see the Gradio UI load:

```
http://127.0.0.1:7860
```

Or from cmd (one-liner — no multi-line issues on Windows):

```cmd
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:7860', timeout=3).status)"
```

Expected output: `200`  
This just confirms the Gradio server responded — it does **not** test any app logic.


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
   - **Where to find it:** The exact path is shown in the "Run Manifest Path" field at the bottom of the UI after every run. Example:
     ```
     D:\...\HackathonProject\artifacts\20260718T141716241398Z\run_manifest.json
     ```
   - Each run creates its own timestamped subfolder under `artifacts/`. The folder name is the `run_id`.
   - **Important:** Only the manifest written **after Approve & Validate Repair** will contain the full healing chain. A pre-approval manifest only has `status` and `strategy`.
   - Open it in Windows Explorer by pasting the path from the UI, or in cmd:
     ```cmd
     notepad "D:\...\HackathonProject\artifacts\<run_id>\run_manifest.json"
     ```
   - Must contain: `diagnosis`, `proposal`, `approved: true`, `validation.checks`, `repaired_result.status`


---

## 5. Fast Simulation via Services (recommended during development)

You can exercise the exact same logic the UI uses without clicking.

> **Windows cmd note:** Multi-line `python -c "..."` does not work in cmd.exe. Use the provided script instead.

**Run from the project root:**

```cmd
python scripts\simulate_m4_services.py
```

The script [`scripts/simulate_m4_services.py`](../scripts/simulate_m4_services.py) runs the full sequence:
1. Prints mutation descriptions + target URLs (no browser needed)
2. Runs the brittle regression on `testid_removed` (needs port 8080 up)
3. If a proposal is generated, runs Approve & Validate automatically

**Expected output:**
```
=== Baseline ===
Baseline — No UI change. Original technical locator remains valid.
http://localhost:8080/index.html?mutation=baseline

=== Remove test ID ===
Remove test ID — UI refactor removes data-testid. ...
http://localhost:8080/index.html?mutation=testid_removed

=== Run on testid_removed (real brittle runner) ===
status: failed
proposal present: True
diagnosis snippet: The test failed because the UI refactor removed data-testid="add-backpack"...

=== Approve & Validate (real validator + repaired run) ===
approved: True
final_status: healed
validation checks: [...]
manifest: D:\...\artifacts\<run_id>\run_manifest.json
```

For a **visible browser** during simulation, open `scripts/simulate_m4_services.py` and change `headless=True` to `headless=False` on the two service calls.


---

## 6. Inspect Manifests

Each run writes a manifest to `artifacts/<run_id>/run_manifest.json`. The full path is shown in the "Run Manifest Path" field in the Gradio UI.

### Option A — Open manually (simplest, works everywhere)

Copy the path from the UI and open it in Notepad or VS Code:
```cmd
notepad "D:\My-AI-Journey\Outskill-Engineering-Accelerator-14Days-Course\HackathonProject\artifacts\<run_id>\run_manifest.json"
```

### Option B — Python one-liner in cmd (finds the latest manifest automatically)

```cmd
python -c "import os, json; root='artifacts'; runs=sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root,d))], reverse=True); f=os.path.join(root,runs[0],'run_manifest.json'); print(json.dumps(json.load(open(f)),indent=2)) if runs and os.path.exists(f) else print('No manifest found')"
```

### Option C — PowerShell (if you have PowerShell available)

Open **PowerShell** (not cmd) in the project root:
```powershell
Get-ChildItem artifacts -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { $m = Join-Path $_.FullName 'run_manifest.json'; if (Test-Path $m) { Get-Content $m | ConvertFrom-Json | ConvertTo-Json -Depth 5 } }
```


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
| Port 8080 busy | Storefront already running from previous session | Kill previous http.server: `for /f "tokens=5" %a in ('netstat -ano ^| findstr :8080') do @taskkill /PID %a /F` |
| App fails to start | Old `concurrency_count` in queue() call | Use `demo.queue(default_concurrency_limit=1)` |
| Approval buttons never appear | Run was on `baseline` or no proposal was generated | Must run on `testid_removed` brittle failure |
| Screenshot missing | Run passed or Playwright screenshot failed silently | Normal for baseline passes |
| Full integration test times out | 30s brittle failure + multiple tests | Run specific nodes or use `python -c` on services |
| Port 7860 already in use (WinError 10048 / "only one usage of each socket address") | Previous `python app.py` (or `background_process`) instance is still running and holding the port | **One-liner to kill (cmd):**<br>`for /f "tokens=5" %a in ('netstat -ano ^| findstr :7860') do @taskkill /PID %a /F`<br>Then restart: `python app.py`<br>**Alternative:** use a different port: `set GRADIO_SERVER_PORT=7861 && python app.py` |
| **Failure screenshot shows "Error response — 404 File not found"** (even though http.server IS running) | `python -m http.server` was started from the **wrong working directory** (e.g. `C:\Users\petru` instead of the project root), so `demo_site/` cannot be found | Stop the server (Ctrl+C), then restart using the **full absolute path**:<br>`python -m http.server 8080 --directory "D:\My-AI-Journey\Outskill-Engineering-Accelerator-14Days-Course\HackathonProject\demo_site"`<br>Verify: open `http://localhost:8080/index.html?mutation=testid_removed` in browser — should show the Demo Storefront, not a 404. |
| **Repair Proposal (code diff) panel appears blank / empty** | The diff HTML used a light grey background (`#f8f8f8`) which is invisible against Gradio's dark theme | Fixed in `testpilot/ui/services.py` — `get_repair_diff_html()` now uses a dark background (`#1e1e2e`) with coloured diff lines (red for removed, green for added). Restart `app.py` to pick up the fix. |

---

## Related Files

- `docs/milestone-checklist.md` — M4 spec + Post-M4 verification steps
- `docs/implementation-log.md` — real commands + output from the M4 implementation
- `testpilot/ui/services.py` — the business logic the UI calls
- `testpilot/ui/layout.py` — the Gradio definition
- `app.py` — entry point

Run the steps in this file (or the 9 manual acceptance steps in the live UI) to independently verify M4.

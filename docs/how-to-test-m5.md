# How to Test M5 — Pydantic Contracts + Narrow LLM Specialists

This guide shows how to verify M5: structured LLM specialists (Planner, Diagnosis, Repair)
with mandatory system prompts, Pydantic validation, targeted context, and **deterministic fallback**.

**Critical rule:** The automated test suite **must never make a real OpenRouter call**.  
All automated tests run with `DEMO_MODE=true` or with mocks. Real LLM calls are manual-only.

---

## 1. Prerequisites

From the project root in **cmd**:

```cmd
python -m pip install -r requirements.txt
playwright install chromium
```

Sanity check (one-liner, works in cmd):

```cmd
python -c "from testpilot.llm.planner import plan_flow; from testpilot.llm.diagnosis import diagnose_failure; from testpilot.llm.repair import propose_repair; print('M5 specialists import OK')"
```

Expected output: `M5 specialists import OK`

---

## 2. Start the Controlled Storefront (only needed for end-to-end flows)

> Unit and contract tests (steps 3–7) do **not** need the storefront.  
> Only skip this if you are running end-to-end healing flows.

In a **separate cmd terminal**, use the full absolute path:

```cmd
python -m http.server 8080 --directory "D:\My-AI-Journey\Outskill-Engineering-Accelerator-14Days-Course\HackathonProject\demo_site"
```

Verify: open `http://localhost:8080/index.html?mutation=testid_removed` — should show "Demo Storefront".

> **If port 8080 is busy**, kill the old process first:
> ```cmd
> for /f "tokens=5" %a in ('netstat -ano ^| findstr :8080') do @taskkill /PID %a /F
> ```

---

## 3. Run the M5 Test Suite (guaranteed no real LLM calls)

```cmd
python -m pytest tests/unit/test_llm_contracts.py -q --tb=short
python -m pytest tests/integration/test_llm_services.py -q --tb=short
```

Full unit layer (run after any code change):

```cmd
python -m pytest tests/unit -q --tb=no
```

Expected: all pass, **zero network calls** to OpenRouter.

---

## 4. Verify DEMO_MODE and Missing Key → Always Fallback

```cmd
python scripts\verify_m5_fallback.py
```

Expected output:
```
=== DEMO_MODE=true ===
Planner mode  : fallback
Diagnosis mode: fallback
Repair mode   : fallback

=== Missing API key ===
_get_llm() returns None (fallback): True
```

All three specialists must return `reasoning_mode = "fallback"` — no network activity.

---

## 5. Inspect Context Building (targeted + truncated)

```cmd
python scripts\verify_m5_context.py
```

Expected output:
```
=== Checks ===
full_html excluded : True
trace excluded     : True
error_excerpt len  : 800 <= 800: True
```

- Only whitelisted keys appear in the context sent to the LLM.
- Long fields are truncated to 800 characters.
- `full_html`, raw traces, base64 screenshots are never included.

---

## 6. Verify System Prompts Load Correctly

```cmd
python scripts\verify_m5_prompts.py
```

Expected output:
```
planner    len=  NNN  contains 'JSON': True
diagnosis  len=  NNN  contains 'JSON': True
repair     len=  NNN  contains 'JSON': True
```

Prompts live in `prompts/<name>.md` and are loaded as the **system message** for each specialist.

---

## 7. Check reasoning_mode Is Recorded in Manifests

```cmd
python scripts\verify_m5_manifest.py
```

Expected output:
```
reasoning_mode recorded: llm
Check passed           : True
```

Uses a temporary directory — no files are left behind after the test.

---

## 8. Manual Real LLM Test (optional — requires API key + network)

> **Do not run in CI or automated suites.** This makes real network calls and consumes API credits.

### Setting environment variables in cmd

In cmd, `set VAR=value` sets a variable **for the current terminal session only** — it is not permanent and is not seen by other windows.

You must set the variables and run the script **in the same cmd window**, one after the other:

```cmd
set DEMO_MODE=false
set OPENROUTER_API_KEY=sk-or-...
set LLM_MODEL=openai/gpt-4o-mini
python scripts\test_m5_real_llm.py
```

> **Important:** There must be **no spaces** around the `=` sign in `set` commands.  
> `set KEY = value` will NOT work — it creates a variable named `KEY ` (with a trailing space).

To verify a variable was set correctly:
```cmd
echo %OPENROUTER_API_KEY%
```

To clear a variable:
```cmd
set OPENROUTER_API_KEY=
```

Then run:

```cmd
python scripts\test_m5_real_llm.py
```

Expected output when key is valid:
```
=== Planner (real LLM) ===
mode: llm  | name: add_blue_backpack_to_cart

=== Diagnosis (real LLM) ===
mode: llm  | category: locator_broken

=== Repair (real LLM) ===
mode: llm  | new_locator: page.get_by_role(...)
```

- All modes must be `"llm"` with a valid key.
- Bad JSON, timeouts, or schema errors must still fall back to `"fallback"` cleanly.

---

## 9. Watch Playwright in the Browser (visual debugging)

By default, Playwright runs **headless** (no visible window). To watch it step through the storefront:

### headless=False — opens a real browser window

Open [`scripts/simulate_m4_services.py`](../scripts/simulate_m4_services.py) and change the runner call:

```python
# Default — no browser window, fastest:
run = services.run_original_regression("testid_removed", headless=True)

# headless=False — opens a real Chromium window so you can watch every action:
run = services.run_original_regression("testid_removed", headless=False)
```

### slow_mo_ms — adds delay between each action

The runner supports a `slow_mo_ms` parameter (milliseconds of pause between every Playwright action). Edit [`scripts/simulate_m4_services.py`](../scripts/simulate_m4_services.py):

```python
from testpilot.browser.runner import run_journey

# slow_mo_ms=500 → Playwright pauses 500ms before every action (click, goto, assert).
# Use with headless=False so you can see each step in the browser window.
# Use strategy="repaired" for a fast passing run; "brittle" will still take ~30s (timeout).
result = run_journey("testid_removed", strategy="repaired", headless=False, slow_mo_ms=500)
```

Recommended combination for visual debugging:
```python
run_journey("testid_removed", strategy="brittle", headless=False, slow_mo_ms=500)
```

> **Note:** The brittle run takes ~30s even in headed mode because the `get_by_test_id` locator genuinely times out waiting for a missing element. Use `strategy="repaired"` to watch a fast, successful run.

---

## 10. Quick Verification Checklist

- [ ] `python -m pytest tests/unit/test_llm_contracts.py -q` → all pass
- [ ] `python -m pytest tests/integration/test_llm_services.py -q` → all pass (mocks only)
- [ ] `scripts\verify_m5_fallback.py` → all modes = `fallback`, `_get_llm()` = `None`
- [ ] `scripts\verify_m5_context.py` → `full_html` excluded, long fields truncated
- [ ] `scripts\verify_m5_prompts.py` → all 3 prompts load, contain `JSON`
- [ ] `scripts\verify_m5_manifest.py` → `reasoning_mode` persisted correctly
- [ ] No real OpenRouter calls during any automated step
- [ ] Full unit layer green: `python -m pytest tests/unit -q`

---

## 11. Common Issues & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Tests call real API | `DEMO_MODE` not set or `_get_llm` not patched | Always `set DEMO_MODE=true` or use `monkeypatch.setenv("DEMO_MODE","true")` in tests |
| Mode stays `"fallback"` even with key | `_get_llm` returns `None` (wrong env or exception) | Check key is set **before** importing modules; reload config if needed |
| Mock not applied | Patching wrong path | Use `patch.object(llm_client.ChatOpenAI, "invoke", ...)` or a full `MagicMock` |
| Context contains huge data | Forgot whitelist | Only pass allowed keys to the context dict; `_build_context` filters the rest |
| Prompt not found | Wrong working directory | Run scripts from the project root; `load_system_prompt` resolves relative to it |
| Port 7860 busy (WinError 10048) | Old `app.py` still running | Kill it: `for /f "tokens=5" %a in ('netstat -ano ^| findstr :7860') do @taskkill /PID %a /F` |
| Port 8080 returns 404 | `http.server` started from wrong directory | Use the full absolute path to `demo_site` (see Step 2) |
| `ModuleNotFoundError: testpilot` | Running script from wrong dir or missing path fix | All `scripts\verify_m5_*.py` files add the project root to `sys.path` automatically |

---

## 12. Related Files

| File | Purpose |
|------|---------|
| `testpilot/llm/` | All M5 specialist implementations |
| `prompts/planner.md`, `diagnosis.md`, `repair.md` | Fixed system prompts |
| `testpilot/config.py` | `DEMO_MODE`, `OPENROUTER_API_KEY`, `LLM_MODEL` |
| `scripts/verify_m5_fallback.py` | Verifies fallback for DEMO_MODE + missing key |
| `scripts/verify_m5_context.py` | Verifies context whitelist + truncation |
| `scripts/verify_m5_prompts.py` | Verifies system prompts load correctly |
| `scripts/verify_m5_manifest.py` | Verifies `reasoning_mode` persisted in manifest |
| `scripts/test_m5_real_llm.py` | Manual real LLM test (optional, needs key) |
| `docs/milestone-checklist.md` | Full M5 spec + post-M5 checks |

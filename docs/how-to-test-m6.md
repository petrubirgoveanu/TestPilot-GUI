# How to Test M6 (LangGraph Workflow)

This document provides exact commands to verify the M6 LangGraph integration locally on Windows.

M6 replaces the manual orchestration with a formal `StateGraph` from LangGraph. It uses `MemorySaver` to pause the graph at the validation step, allowing for the human-in-the-loop approval gate.

## 1. Prerequisites

Ensure dependencies are installed and `demo_site` is served. From the project root:
```cmd
python -m pip install -r requirements.txt
python -m pip install ruff
python -m pip install playwright
python -m playwright install chromium
python -m ruff check . --select E,W,F,C90 --line-length 120 --no-cache
```
Open a new terminal and run:
```cmd
python -m http.server 8080 --directory demo_site
```

## 2. Graph Unit Tests (No Browser)

Test the graph edges and mocked nodes without launching Playwright.

```cmd
python -m pytest tests/unit/test_graph.py -q
```
**Expected Output:** `3 passed` (baseline pass, interrupt on failure, resume on approval).

## 3. Workflow Integration Tests (Real Browser)

Test the graph hitting the real storefront using `DEMO_MODE=true` to ensure the deterministic fallback works correctly through the graph.

```cmd
python -m pytest tests/integration/test_workflow.py -q
```
**Expected Output:** `2 passed` (baseline, and mutated run with approval).

## 4. Full Suite Verification

Make sure the UI layer tests still pass since `services.py` now uses the graph.

```cmd
python -m pytest -q
```
**Expected:** All tests pass cleanly.

## 4.1 Lessons Learned

- LangGraph integration is only valuable after the deterministic healing flow is stable. Do not introduce graph orchestration before M3/M4 are green.
- The approval gate remains the most fragile area: ensure the graph pauses cleanly and resumes only after explicit approval.
- If the graph tests fail, isolate the issue by validating the underlying `execute_deterministic_healing()` path first.

## 5. Manual UI Acceptance

1. Start the Gradio app:
   ```cmd
   python app.py
   ```
2. Navigate to `http://127.0.0.1:7860`.
3. Select **Remove test ID** and click **Run Healing Workflow**.
4. Observe the timeline advancing through `Planned -> Running -> Failed -> Diagnosed -> Repair proposed`.
5. The graph is now interrupted. Click **Approve & Validate Repair**.
6. Observe the graph resuming and advancing to `Approved -> Validated -> Healed`.
7. Download the Manifest and inspect `run_manifest.json` to verify the state transitions are recorded.

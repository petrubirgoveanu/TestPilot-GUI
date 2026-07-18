# How to Test M7 (LangSmith Observability)

This document provides instructions on how to verify Milestone 7 (Optional LangSmith Observability) and details the separation of concerns between our tracing, runner, UI, and audit layers.

## 1. Tracing vs. Artifact Separation of Concerns

Our project enforces a strict boundary between observability, browser testing, user interface, and the audit logs:

```text
LangSmith: LLM/LangGraph decision traces
Playwright: browser evidence, screenshots, traces, assertions
Gradio: product-facing workflow and repair timeline
JSON run manifest: per-run hackathon audit record
```

- **LangSmith** only holds high-level LLM and LangGraph decision traces. It is never used to store browser evidence or logs.
- **Playwright** manages all low-level browser operations (clicks, assertions, screenshot generation on failure, etc.).
- **Gradio** provides the web layout for driving mutations and showcasing the repair timeline to humans.
- **JSON run manifests** are the ultimate audit logs of each test run, stored under `artifacts/<run_id>/run_manifest.json`.

## 2. Running Automated Tests

Milestone 7 is covered by the LangSmith optionality tests in the unit suite. The key tests in this area are:

- `tests/unit/test_langsmith.py::test_app_runs_when_langsmith_env_vars_are_absent`
- `tests/unit/test_langsmith.py::test_app_runs_when_langsmith_tracing_is_false`
- `tests/unit/test_langsmith.py::test_langsmith_configuration_is_optional`
- `tests/unit/test_langsmith.py::test_browser_artifacts_do_not_depend_on_langsmith`

### Run LangSmith Optionality Tests
Ensure these run and pass without needing any active LangSmith accounts or API calls:
```cmd
python -m pytest tests/unit/test_langsmith.py -q
```
**Expected Output:** `4 passed`

### Run Full Unit Test Layer
Run the entire suite of unit tests to verify no regressions. This layer includes tests such as:

- `tests/unit/test_llm_contracts.py::test_flow_spec_validates_supported_intent`
- `tests/unit/test_llm_contracts.py::test_missing_api_key_uses_fallback`
- `tests/unit/test_graph.py::test_graph_pass_baseline`
- `tests/unit/test_runner.py::test_failure_result_serializes_required_fields`
- `tests/unit/test_ui_services.py::test_mutation_selection_updates_gradio_state`
- `tests/unit/test_langsmith.py::test_app_runs_when_langsmith_env_vars_are_absent`

```cmd
python -m pytest tests/unit -q
```

### Run Full Test Suite
Run all tests (unit and integration) to confirm full safety:
```cmd
python -m pytest -q
```

## 3. Manual Tracing Verification (Optional)

Use this section only if you want to confirm that tracing is working in your own LangSmith account. The goal is to verify that the app can emit LLM/LangGraph trace events without depending on browser artifacts or manifest files.

### Step 1: Prepare the environment
Open a terminal in the project root and configure the tracing variables:

```cmd
set LANGSMITH_TRACING=true
set LANGSMITH_API_KEY=your_langsmith_api_key
set LANGSMITH_PROJECT=testpilot-hackathon
```

If you are using PowerShell instead of Command Prompt, use:

```powershell
$env:LANGSMITH_TRACING="true"
$env:LANGSMITH_API_KEY="your_langsmith_api_key"
$env:LANGSMITH_PROJECT="testpilot-hackathon"
```

### Step 2: Start the storefront
In Terminal 1, serve the demo storefront so the browser app is available:

```cmd
python -m http.server 8080 --directory demo_site
```

Leave this terminal running.

### Step 3: Start the Gradio app
In Terminal 2, launch the main application:

```cmd
python app.py
```

When the app starts successfully, you should see the Gradio interface URL in the terminal output. Open the page at `http://127.0.0.1:7860` or `http://localhost:7860` in your browser. If the page is already visible, you can proceed directly to the next step.

### Step 4: Use the app and run a healing workflow
Once the page is open, interact with the interface as follows:

1. Select the baseline or mutated scenario from the available options.
2. Choose the mutation you want to test.
3. Click the button that starts the regression or repair workflow.
4. Wait for the run to complete and review the timeline or status updates shown in the UI.

The app should run through the planner, diagnosis, and repair stages during this workflow.

What to watch for:
- The workflow should complete without requiring any LangSmith-specific setup beyond the environment variables above.
- The browser UI should still function normally.
- A run manifest should be produced under `artifacts/<run_id>/run_manifest.json` for the run.

### Step 5: Verify traces in LangSmith
After the workflow completes, open your LangSmith dashboard and check the project named `testpilot-hackathon`.

You should see trace entries for the major steps such as:
- planner
- diagnosis
- repair

If no traces appear, confirm that:
- the `LANGSMITH_API_KEY` is valid,
- the project name matches the one configured,
- the app process is still running,
- the workflow actually reached the LLM/LangGraph stages.

### Step 6: Disable tracing when finished
To stop sending traces, either clear the environment variables or switch tracing off:

```cmd
set LANGSMITH_TRACING=false
```

Or in PowerShell:

```powershell
$env:LANGSMITH_TRACING="false"
```

# How to Test M9 — Docker + CI + Render Attempt

This runbook explains how to verify Milestone M9 in a reproducible, deterministic way.

M9 scope:
- Docker build and local container smoke run
- GitHub Actions CI workflow (unit + integration + e2e + evals)
- Failure artifact upload on CI failures
- Render deployment attempt and fallback documentation

The project must remain deterministic in CI:
- `DEMO_MODE=true`
- `LANGSMITH_TRACING=false`
- no real OpenRouter key usage in CI

Browser mode policy:
- Automated tests (local commands in this guide and GitHub Actions) run in headless mode by default.
- Headed mode is for local debugging only.

---

## 1. Prerequisites

From repository root:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Start the controlled storefront in a separate terminal:

```powershell
python -m http.server 8080 --directory demo_site
```

Quick readiness check:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/index.html?mutation=testid_removed', timeout=5).status)"
```

Expected output: `200`

---

## 2. Local Deterministic Verification

In a second terminal (same repo):

```powershell
$env:DEMO_MODE = "true"
$env:LANGSMITH_TRACING = "false"
$env:OPENROUTER_API_KEY = ""
$env:BASE_URL = "http://localhost:8080"
```

Run tests and evals:

```powershell
python -m pytest tests/unit -q --tb=no
python -m pytest tests/integration -q --tb=no
python -m pytest tests/e2e -q --tb=no
python evals/run_evals.py
```

Notes:
- `tests/e2e` may be empty for the current slice.
- If pytest returns exit code `5` for e2e (`no tests collected`), treat that as acceptable for now.
- The test flows above run headless unless you explicitly change test/service calls to `headless=False` for local observation.

---

## 3. Docker Verification (Local)

Build image:

```powershell
docker build -t testpilot-slice .
```

Run container smoke test:

```powershell
docker run --rm -p 7860:7860 --env DEMO_MODE=true --env LANGSMITH_TRACING=false testpilot-slice
```

Then open:
- `http://localhost:7860`

Expected:
- Gradio UI is reachable.
- App starts without stack traces.

If using `.env` locally instead:

```powershell
docker run --rm -p 7860:7860 --env-file .env testpilot-slice
```

---

## 4. CI Verification (GitHub Actions)

Workflow file:
- `.github/workflows/ci.yml`

Expected CI behavior:
- checks out code
- sets up Python 3.11
- installs dependencies and Chromium
- starts static storefront (`python -m http.server 8080 --directory demo_site`)
- runs unit, integration, e2e, and eval suite
- builds Docker image
- uploads artifacts on failure

After pushing branch:
1. Open GitHub Actions tab.
2. Confirm at least one run is green.
3. If failed, confirm artifact upload exists and is downloadable.

Artifacts expected on failure:
- `artifacts/**`
- `storefront.log`
- `.pytest_cache/**`

---

## 5. Render Attempt Verification

Attempt public Docker Web Service deployment on Render.

Minimum evidence to record in `docs/implementation-log.md`:
- exact deployment attempt commands/settings
- final Render status
- public URL (if created)
- incognito reachability check result

If Render deployment is blocked:
- document exact blocker
- document fallback status (local Docker verification)
- keep retry notes concise and factual

---

## 6. Common M9 Failure Modes

- CI silently passes despite failing tests:
  - remove `|| echo ...` failure masking on required test steps.
- Storefront not started before integration/evals:
  - ensure startup + readiness probe happen before test steps.
- e2e step fails with no tests collected:
  - handle only pytest exit code `5` as a temporary pass condition.
- PowerShell cannot run venv interpreter path:
  - use call operator syntax:
  - `& ".venv\\Scripts\\python.exe" -m pytest tests/unit -q`
- `rg` command missing in shell:
  - use `git ls-files` for file inventory fallback.

---

## 7. Required Log Entry

After M9 verification, append a real-results entry to `docs/implementation-log.md` with:
- command list
- exact outcomes
- CI run link/status
- Docker build/run status
- Render attempt outcome

Do not mark M9 complete until Post-M9 verification checks in `docs/milestone-checklist.md` are independently confirmed.

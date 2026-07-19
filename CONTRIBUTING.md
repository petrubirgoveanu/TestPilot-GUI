# Contributing to TestPilot

Thanks for helping improve TestPilot. This repository is intentionally small and opinionated, so contributions are easiest when they stay focused on the controlled browser-testing workflow.

## What this project is optimizing for

TestPilot is a public MVP for a very specific problem: a supported browser journey should stay stable even when a UI refactor breaks brittle locators. The codebase is designed to keep that loop auditable, deterministic, and easy to verify.

That means contributors should optimize for:

- clarity over cleverness
- deterministic behavior over hidden automation
- explicit evidence over implied success
- small changes that are easy to review and reproduce

## Development setup

From the repository root:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Run the storefront and app in separate terminals:

```powershell
python -m http.server 8080 --directory demo_site
python app.py
```

Recommended local environment variables:

```powershell
$env:DEMO_MODE = "true"
$env:LANGSMITH_TRACING = "false"
$env:OPENROUTER_API_KEY = ""
$env:BASE_URL = "http://localhost:8080"
```

## What to test

Use the smallest test scope that proves the change.

Common commands:

```powershell
python -m pytest tests/unit -q --tb=no
python -m pytest tests/integration -q --tb=no
python -m pytest tests/e2e -q --tb=no
python -m evals.run_evals
python -m ruff check . --select E,W,F,C90 --line-length 120 --no-cache
```

If you change the browser runner or services layer, re-run the unit tests that exercise those paths immediately. If you change deployment behavior, check the relevant runbook in `docs/` as well.

## Code style

- Keep UI callbacks thin; move actual logic into service modules.
- Keep business intent in `testpilot/models.py` and do not hard-code selectors into flow contracts.
- Preserve the approval gate. Repairs must never auto-apply.
- Prefer small helper functions over long branching functions when code starts to get complex.
- Add comments only when the reason is not obvious from the code.

## Documentation expectations

If you change user-visible behavior, update the documentation that describes it.

Good places to update are:

- [README.md](README.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- the relevant runbook in `docs/`

Do not leave readers guessing about:

- how to run the app
- which environment variables matter
- where artifacts are written
- what behavior is deterministic versus optional

## Pull request checklist

Before opening a PR:

- [ ] Code is focused and reviewed locally
- [ ] Tests relevant to the change pass
- [ ] Ruff passes for touched Python files
- [ ] Documentation matches the new behavior
- [ ] No secrets or generated artifacts are committed
- [ ] The branch is ready for CI

## Repository hygiene

Please avoid committing:

- `.env` files with real secrets
- generated Playwright artifacts
- local cache directories
- large screenshots unless they are intentionally part of a doc or test fixture

The repo already contains milestone and runbook documentation. Keep those files intact unless you are deliberately improving the guidance they provide.

## Questions or follow-up work

If a change affects the public app surface, deployment, or test strategy, document the impact in the repository before merging. That keeps the project easier to use for both judges and outside contributors.

# TestPilot — Submission Checklist (Reference)

## Product
- [ ] Deployed URL works in incognito.
- [ ] Known-good v1 baseline is tested.
- [ ] Known-good v2 repair scenario is tested at least five times.
- [ ] Run queue prevents concurrent Chromium jobs.
- [ ] Error state is readable if LLM call fails.

## Repository
- [ ] README begins with product summary, live URL, Loom link, and architecture.
- [ ] `.env.example` exists; real `.env` is ignored.
- [ ] No keys, build outputs, browser binaries, traces, or giant videos committed.
- [ ] No unused Node/package files if project is Python-only.
- [ ] Every dependency and module is used by the deployed flow.
- [ ] Setup instructions work from a clean clone.
- [ ] **M2+**: Storefront server start instructions are explicit (background_process or two terminals). Port 8080 + demo_site.
- [ ] **M3+**: Runner supports "brittle" + "repaired" strategies; healing flow + validator + explicit approval gate implemented and verified with 3 full deterministic loops recorded.
- [ ] **M4+**: Gradio UI ("UI Change Lab") with real runner integration, mutation-driven previews/URLs, explicit Approve/Reject gate, timeline, evidence panels, and manifest download. 9 manual acceptance steps verified. No LLM calls. See docs/how-to-test-m4.md.
- [ ] **M5+**: Narrow LLM specialists (Planner/Diagnosis/Repair) implemented with dedicated system prompts, Pydantic validation, targeted context only. All automated tests use DEMO_MODE or mocks (zero real OpenRouter calls). reasoning_mode recorded. See docs/how-to-test-m5.md.
- [ ] **M8+**: Evaluation suite in `evals/repair_cases.json` + `run_evals.py` implemented. Run `python -m evals.run_evals` and verify healing success and approval compliance.
- [ ] **M9+**: CI workflow starts storefront, runs unit/integration/e2e/evals in deterministic mode, builds Docker, and uploads failure artifacts. See docs/how-to-test-m9.md.

## Evidence
- [ ] Screenshot and trace are produced for a failure.
- [ ] Repair diff and validation result are visible.
- [ ] Final healed outcome is visible.
- [ ] Backup short video and final Loom are available.

## Presentation
- [ ] Loom is under five minutes.
- [ ] Demo is rehearsed twice from the deployed URL.
- [ ] A specific scenario—not random—is used for main pitch.
- [ ] Each speaker knows their segment.
- [ ] Submission links have been opened by a second team member.

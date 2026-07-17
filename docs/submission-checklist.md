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

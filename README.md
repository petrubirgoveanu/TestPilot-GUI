# TestPilot — AI-Assisted Self-Healing Browser Tests

> **Status:** Planning / implementation starts Saturday 14:00. Empty project.
>
> **Our only goal until the first checkpoint:**
> A controlled UI mutation breaks a browser test → TestPilot captures evidence
> → user approves a repair → deterministic validation reruns the complete journey successfully.

**Hackathon window:** Saturday 14:00 to Sunday 14:00  
**Team:** 7 people  
**Primary stack (slice):** Python, Gradio, Playwright (sync), OpenRouter GPT-4o Mini, Docker

---

## Current Status & Day 0 (Do This First)

- [ ] Project is still empty — only this README exists.
- [ ] Immediate next 60–90 minutes (Saturday kickoff):
  1. Agree on the **Minimum Demoable Slice** (see below).
  2. Clone repo, create `.venv`, `pip install -r requirements.txt`, `playwright install chromium`.
  3. Create the tiniest possible demo storefront (single HTML page driven by golden mutation).
  4. Write one baseline Playwright test that passes on baseline and fails on testid_removed (one intentional locator break).
  5. Run it locally and capture screenshot + error.
  6. Show the failure in a minimal Gradio UI (hard-coded `FlowSpec`, template test, run button, show screenshot).
  7. Add a manual "Apply known-good repair" button that swaps the locator and re-runs.
  8. Validate + full rerun must pass and show green result.

**Critical path first (Pair 2 owns this until green):**
- Golden storefront + mutation
- Baseline + mutated Playwright tests using brittle locator
- Hard-coded execution + screenshot on failure
- Manual approve gate + repaired locator validation + full rerun

**Parallel work allowed (as long as it does not block the slice):**
- Pair 1: Define Pydantic models, OpenRouter adapter skeleton, prompt templates, and deterministic stubs against the agreed `FlowSpec` / `GOLDEN_INTENT`.
- Pair 3: Build Gradio shell, timeline, and approval UX using fake/hard-coded run data.
- Integrator: Prepare Docker skeleton and Render config (can deploy the skeleton early).

Do not let unfinished parallel work become a dependency on the golden vertical slice.

---

## Minimum Demoable Slice (The Only Thing That Matters Until Green)

This is the **only** scope for the first vertical slice. Everything else is reference material.

### Golden path supported request (THE single source of truth for the slice)

```
Add the blue backpack to cart and confirm the cart count is 1.
```

Defined in `testpilot/models.py` as `GOLDEN_INTENT`.

The `FlowSpec` (`GOLDEN_FLOWSPEC`) expresses **only business intent** (logical steps: goto storefront, click add_blue_backpack, assert cart_count == 1). 

Locators are resolved at execution time using `resolve_locator(page, target, strategy)`:
- "brittle" → original fragile locator that will break on mutation
- "repaired" → stable semantic locator (role + accessible name)

This separation is deliberate: the journey never changes; only the technical locator does.

### Supported journey (short)
1. Open storefront
2. Add Blue Backpack to cart
3. Assert cart count is 1

### Controlled mutation (one only)
- baseline (or `?v=1`): button has `data-testid="add-backpack"`
- `testid_removed` (mutated): `data-testid` removed; button is still findable by role + accessible name

### What "working" means
- User enters (or we hard-code) exactly `GOLDEN_INTENT`.
- Baseline test passes on the non-mutated storefront.
- Run on the mutated storefront fails → screenshot + error shown.
- UI shows simple diagnosis (can be deterministic string first).
- One proposed repair (hard-coded or from LLM) that switches the locator strategy for the same intent step from "brittle" to "repaired".
- User must click **Approve**.
- Validation: exactly 1 matching element, visible, enabled, click succeeds, assertion passes.
- Full journey re-runs and passes.
- Timeline/audit shows the steps taken.

**Success metric for slice:** 3+ independent full runs (baseline pass + mutated fail + repair + validated rerun) with no manual intervention after approve.

See [docs/mvp-full.md](docs/mvp-full.md) for the old ambitious list — ignore until this slice is solid.

---

## Table of Contents

- [Problem](#problem)
- [Product](#product)
- [Scope Principles](#scope-principles)
- [Minimum Demoable Slice](#minimum-demoable-slice-the-only-thing-that-matters-until-green) (above)
- [Demo Storefront + Mutation](#demo-storefront--mutation)
- [Architecture (High Level)](#architecture-high-level)
- [Safety Rules for the Slice](#safety-rules-for-the-slice)
- [Concrete Evidence & Validation](#concrete-evidence--validation)
- [Known Sharp Edges (First Slice)](#known-sharp-edges-first-slice)
- [Day 1 Schedule & Milestones](#day-1-schedule--milestones)
- [Quick Start (Local)](#quick-start-local)
- [Reference Material](#reference-material)

---

## Problem

Browser end-to-end tests are expensive to maintain. A small UI refactor—such as a renamed button, removed `data-testid`, changed accessible label, or an action moving from a link to a button—can break an otherwise valid customer journey. QA engineers then need to inspect failures, understand what changed, update selectors, rerun the test, and verify the business flow still works.

Current AI code generation alone is insufficient. A trustworthy solution must show:

1. What failed and where.
2. Evidence from the browser run.
3. Why the failure occurred.
4. The exact repair proposed.
5. A human approval decision.
6. Independent validation that the repaired locator works and the full business assertion passes.

---

## Product

### Name

**TestPilot** — AI-Assisted Self-Healing Browser Tests

### One-line pitch

> TestPilot turns a supported user journey into a Playwright test, detects when a UI change breaks it, explains the failure from browser evidence, proposes a safe repair, and validates the repaired journey after human approval.

### What makes it different

TestPilot is **not** a generic chatbot that writes browser automation code, and it is **not** an unrestricted agent that can browse arbitrary public websites. It is a controlled, auditable QA workflow:

```text
Natural-language intent
        ↓
Typed flow specification
        ↓
Safe Playwright test generation
        ↓
Browser execution with artifacts
        ↓
Failure diagnosis from evidence
        ↓
Repair proposal with confidence
        ↓
Human approval
        ↓
Deterministic validation and full rerun
```

---

## Scope Principles

### Build deeply, not broadly

A polished end-to-end vertical slice is worth more than a large collection of unfinished agents. Every module must be exercised by the deployed demo.

### Controlled target only

The MVP tests a small, team-owned demo storefront. We do not accept arbitrary URLs or execute arbitrary LLM-generated Python. This makes runs safe, repeatable, and judge-friendly.

### One repair category first

The first supported repair is a broken locator caused by an intentional UI change. We add more mutation scenarios only after the primary pass → fail → repair → pass loop is reliable.

### Evidence before claims

A repair is only considered successful after the system captures evidence, validates the candidate against the live page, performs the intended action, and reruns the complete journey successfully.

### Honest terminology

We use **supported mutation coverage** rather than claiming universal self-healing. The system can heal defined categories of UI-change regressions in the controlled mutation lab.

---

## Demo Storefront + Mutation (Must Be First Thing Built)

**Implementation for the slice (keep it dead simple):**

- Single small HTML page served locally (FastAPI or even `python -m http.server` to start).
- Mutation controlled by `mutation` query param (see `testpilot/models.py` for the golden path):
  - `?mutation=baseline` → original fragile locator present (`data-testid="add-backpack"`)
  - `?mutation=testid_removed` → mutated: `data-testid` removed, button still visible by role + name
- Cart is fake (in-memory or simple JS state). The "add to cart" action just increments a visible counter.
- No auth, no real backend, no external calls.

This guarantees:
- Business flow still works after mutation.
- Original `get_by_test_id` locator breaks on the mutated version.
- Repair target is stable: `get_by_role("button", name="Add Blue Backpack")` (resolved via `resolve_locator(..., "repaired")`).

Put the storefront code under `demo_site/` or even inline in `app.py` at first. Do not over-engineer.

See the Minimum Demoable Slice rules above — this is the **only** mutation until the loop is green 3+ times.

---

## Architecture (High Level — Slice Only)

```
Gradio UI (intent or hard-coded, run button, approve button, screenshot, timeline)
        ↓
LangGraph (or simple sequential functions first)
  plan (stub or real) → generate (template) → execute (Playwright)
  → diagnose (stub or LLM) → propose_repair → await_approval (human)
  → validate (deterministic checks + rerun) → show result
        ↓
Playwright (Chromium, headless) + controlled demo storefront (local)
```

**For the first slice you can replace the full graph with plain functions.** Add LangGraph only after the happy path works.

Key data (keep minimal):
- `flow_spec` (Pydantic)
- `run_result`: status, error, screenshot_path, mutation_id
- `repair_proposal`
- `approved: bool`
- `validation_result`

---

## Safety Rules for the Slice

- Browser only talks to the local controlled storefront. No URL input field.
- LLM (if used) may only return structured objects we validate with Pydantic.
- Never auto-apply a repair. Human must click Approve.
- One active browser run at a time (use Gradio queue or a simple lock).
- All artifacts go under `artifacts/<run_id>/`.
- No secrets in code or screenshots.

---

## Concrete Evidence & Validation (For the Slice)

### What to capture on every run
- Screenshot on failure (Playwright `screenshot(path=...)`).
- Error text / stack excerpt.
- The exact step that failed.

### Evidence for repair context (collect deterministically before calling LLM)
Use a **targeted** extractor — never the whole page body.

```python
# Example of good, narrow evidence collection
buttons = page.get_by_role("button").all()
relevant = []
for b in buttons:
    relevant.append({
        "role": "button",
        "name": b.get_attribute("aria-label") or b.inner_text(),
        "testid": b.get_attribute("data-testid"),
    })
# Also grab the failed step, original locator, error, and a small
# sanitized DOM fragment around the control if needed.
```

Keep it small, relevant, and explainable. This supports the evidence-grounded repair idea without dumping the entire DOM.

### Required validation checks (must pass before declaring healed)
Use the runtime resolver with "repaired" strategy (sync Playwright):

```python
from testpilot.models import resolve_locator

candidate = resolve_locator(page, "add_blue_backpack", "repaired")
assert candidate.count() == 1
assert candidate.is_visible()
assert candidate.is_enabled()

candidate.click()
expect(resolve_locator(page, "cart_count", "brittle")).to_have_text("1")
```

Only then re-run the full supported journey (the golden 3 steps) and require it to pass.

---

## Known Sharp Edges (First Slice)

- Gradio + async browser runs + "resume after approve" is tricky. Start with storing proposal in session state or a temp JSON file and a "Continue after approve" button.
- Playwright on Windows + paths with spaces.
- OpenRouter structured output can still return bad JSON — always wrap in try/except + Pydantic.
- Headless Chromium memory on free hosting (Render) is unreliable. Prioritize local Docker + recorded backup Loom.
- Flaky timing: use semantic locators + explicit waits; keep the journey to 3 steps.
- Token limits: never send full trace or huge DOM.

---

## Day 1 Schedule & Milestones (Tight)

| Time | Objective | Exit condition |
|---|---|---|
| Sat 14:00–14:30 | Kickoff + lock slice | Agree on 3-step journey + one testid mutation. Roles assigned. |
| Sat 14:30–15:30 | Environment + storefront | `python app.py` serves golden storefront; baseline passes, testid_removed fails with screenshot. |
| Sat 15:30–17:00 | Minimal UI + run | Gradio shows run button, failure screenshot, and a manual repair-apply button. Full loop works once (hard-coded). |
| Sat 17:00 | **Checkpoint** | 3 clean end-to-end runs (pass → fail → approve → validated rerun). |
| Sat 17:00–19:30 | Add real LLM pieces | Planner stub → real small prompt, diagnosis, repair proposal (still 1 mutation). |
| Sat 19:30–22:00 | Polish & artifacts | Timeline visible, run manifest JSON, artifacts stored, error states handled. |
| Sat 22:00 | **Deployment checkpoint** | Local Docker works. Attempt Render deployment and record a backup video immediately. If Render is constrained, retain local replay mode and the Loom as fallback — but do not stop attempting the deployed URL (explicit judging bonus). |
| After 22:00 | Only if core is rock solid | Second mutation, better prompts, CI. Otherwise stop and rehearse. |
| Sun morning | Reliability | 5+ full runs, fix flakes, rehearse Loom twice. |
| Sun 10:30 | Feature freeze | Only docs, cleanup, final video. |

**Rule:** After 17:00 on Saturday, do not add any feature that can break the existing green loop.

---

## Quick Start (Local — Day 0)

```bash
# 1. Setup
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# 2. Copy env
cp .env.example .env
# put your OPENROUTER_API_KEY in .env (or use DEMO_MODE=true with stubs first)

# 3. Run (will evolve)
python app.py
# open http://127.0.0.1:7860
```

See the Minimum Demoable Slice section. Get the 8 steps working before touching anything else.

---

## Reference Material

The following live in `docs/` and are only relevant **after** the Minimum Demoable Slice is solid:

- [Full original MVP list](docs/mvp-full.md) (ignore for now)
- [Demo & Pitch script](docs/demo-pitch.md)
- [Submission checklist](docs/submission-checklist.md)

Other heavy original sections (detailed team structure, full schedule, Git layout, CI yaml, reports, risk register, etc.) have been trimmed from this README so the file stays usable as a Day 0 guide. Restore from git history or recreate only when the core loop works.



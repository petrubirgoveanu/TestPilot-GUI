# TestPilot — AI-Assisted Self-Healing Browser Tests

> **Status:** Skeleton in place. Ready to implement the Minimum Demoable Slice.
>
> **Our only goal until the first checkpoint:**
> A controlled UI mutation breaks a browser test → TestPilot captures evidence
> → user approves a repair → deterministic validation reruns the complete journey successfully.

**Hackathon window:** Saturday 14:00 to Sunday 14:00  

---

## Target Technology Stack & Deployment (LOCKED for the Slice)

**Use exactly this. Do not add or depend on anything else until the Minimum Demoable Slice is green and stable.**

### Technology stack
- **Python** 3.11
- **Gradio** (Blocks)
- **Playwright** (Python + Chromium, **synchronous** API only)
- **LLM**: OpenRouter `openai/gpt-4o-mini`
- **Packaging**: Docker (official Playwright Python image)
- **Contracts**: Pydantic v2

**Workflow for the slice**: Start with plain sequential Python functions. Introduce LangGraph only after the core loop works.

**Out of scope until the slice is stable**:
- Multiple LLMs, routing, RAG, embeddings
- Databases, queues, Redis, auth, RBAC
- Multi-browser, visual regression, Allure, etc.

### Deployment
- **Required**: Public **Render** URL (Docker Web Service).
- The URL must be reachable in incognito and must be demonstrated in the final Loom + submission.
- **Rule**: Attempt Render deployment by the Sat 22:00 checkpoint.
- Local Docker + recorded Loom is fallback only (you must keep trying for the public URL).

See "Known Sharp Edges" and the implementation artifacts (`implementation-prompt`, `AGENT_BRIEF.md`, `docs/milestone-checklist.md`) for current guidance.

---

## Current Status

- Core contracts and golden path are defined in `testpilot/models.py`.
- Controlled demo storefront exists at `demo_site/index.html`.
- Playwright runner (brittle + repaired strategies) + M2 artifacts in place.
- M3 deterministic repair complete: diagnosis + proposal + explicit approval gate + validator + full rerun healed. 3+ manual loops recorded.
- M4 Gradio UI complete: "UI Change Lab" radio, live previews, real runner integration, timeline, error/screenshot, diagnosis, repair diff, explicit Approve/Reject, final HEALED only after validation. 12 new tests + app launches + manual acceptance flows verified.
- M5 narrow LLM specialists complete: Planner / Diagnosis / Repair with dedicated system prompts from `prompts/`, Pydantic validation, targeted context only, strict DEMO_MODE + error fallbacks, `reasoning_mode` recorded. All automated tests use mocks or DEMO_MODE (zero real OpenRouter calls). 14 new M5 tests.
- UI services layer: `testpilot/ui/services.py` (thin, testable, calls real M2 + M3).
- Workflow package: `testpilot/workflow/` (deterministic only).
- LLM package: `testpilot/llm/` (narrow specialists only).
- System prompts for the narrow LLM specialists are in `prompts/`.
- The project uses a flat `testpilot/` layout.

**For implementers (agents or humans):**  
The single source of truth for building the slice is `implementation-prompt`.  
Quick discipline rules and scope lock are in `AGENT_BRIEF.md`.  
A practical milestone-by-milestone checklist (with mandatory verification steps) is in `docs/milestone-checklist.md`.

**Mandatory verification gate:**  
After finishing the implementation work and "Run & Verify" commands for a milestone, **a human (or a separate verification agent) must** independently run the documented post-milestone checks listed in `docs/milestone-checklist.md`. The person/agent who did the implementation work cannot self-approve the milestone. All verification commands + real output must be recorded in `docs/implementation-log.md`.

Do the work in the order described in those files. Do not expand scope until the Minimum Demoable Slice is green and stable.

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

```mermaid
flowchart TD
    subgraph UI["Gradio UI (product surface)"]
        U1[Golden Intent<br/>hard-coded or input]
        U2[Mutation Selector<br/>baseline / testid_removed]
        U3[Run / Approve buttons]
        U4[Timeline + Screenshot + Repair Diff]
    end

    subgraph Specialists["Narrow LLM Specialists (not general agents)"]
        P[Planner<br/>system: prompts/planner.md<br/>intent → FlowSpec]
        D[Diagnosis<br/>system: prompts/diagnosis.md<br/>evidence → Diagnosis]
        R[Repair<br/>system: prompts/repair.md<br/>evidence + Diagnosis → RepairProposal]
    end

    subgraph Exec["Deterministic Execution"]
        E1[Playwright Executor<br/>(brittle locators first)]
        V[Validator<br/>(repaired locators + checks)]
        FB[Fallback<br/>DEMO_MODE / error → deterministic]
    end

    subgraph Human["Human in the Loop (mandatory)"]
        H{Await Approval?}
    end

    subgraph Out["Artifacts & State"]
        M[Run Manifest<br/>(JSON, every transition)]
        S[Screenshot + Trace]
        Res[Final Result<br/>HEALED / NEEDS_REVIEW]
    end

    U1 & U2 --> E1
    E1 -->|pass| Res
    E1 -->|fail + evidence| D
    D --> R
    R --> H
    H -->|Approve| V
    H -->|Reject| Res
    V -->|valid| E2[Re-execute full journey<br/>with repaired locator]
    E2 --> Res
    V -->|invalid / 2nd failure| Res

    P --> E1
    D -.->|on LLM error| FB
    R -.->|on LLM error| FB

    style Specialists fill:#f0f8ff
    style Human fill:#fff4e6
    style FB fill:#ffe4e1
```

### Agentic Architecture (Slice Only)

- **Narrow specialists only**: Planner, Diagnosis, Repair.
- Each specialist loads a dedicated **system prompt** from `prompts/` (`planner.md`, `diagnosis.md`, `repair.md`).
  - The file content is used as the fixed system message.
  - Dynamic user context (intent + targeted evidence + mutation) is appended as a small user message.
- No general-purpose agents, no autonomous web browsing, no unrestricted code execution.
- Human approval is a **hard gate** — repairs are never applied automatically.
- LangGraph (or plain sequential functions for the first slice) orchestrates the flow.
- Deterministic fallback is first-class: when `DEMO_MODE=true`, key missing, or LLM fails, the system uses built-in deterministic behavior and records `reasoning_mode: "fallback"`.

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

## M2 Lessons (real implementation friction)
- Controlled storefront server (`python -m http.server 8080 --directory demo_site`) must be running **before** any runner call or integration test. Agents must use `background_process start` first; port conflicts are common.
- The deliberate "fail" test waits 30s. Full `pytest tests/integration` often exceeds agent tool timeouts. Run single nodes or use direct `python -c` calls for verification.
- New `testpilot/` subpackages require `__init__.py`.
- Prefer the exact Post-M* verification one-liners in `docs/milestone-checklist.md` (they are faster and more reliable than full suite runs during implementation).

---

## Implementation Guidance

The detailed, up-to-date milestones, sequencing, and exit criteria live in the implementation artifacts:

- `implementation-prompt` — full step-by-step spec for the slice (the document an implementing agent should follow).
- `AGENT_BRIEF.md` — strict rules for tool usage, scope lock, and discipline.
- `docs/milestone-checklist.md` — concise milestone-by-milestone quick reference, **including the mandatory human / independent-agent verification steps that must be performed and logged after each milestone before the project may move to the next one**.

The historical schedule table has been removed from this README. All current execution guidance is in the files above.

**Hard rule that remains:** Do not add features that can break the existing green loop once the Minimum Demoable Slice reaches a stable pass → fail → approve → validated rerun state.

---

## Quick Start (Current Skeleton)

```bash
# 1. Setup
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# 2. Copy env
cp .env.example .env
# put your OPENROUTER_API_KEY in .env (or use DEMO_MODE=true with stubs first)

# 3. Verify core contracts
python -c "from testpilot.models import GOLDEN_INTENT, resolve_locator; print('OK')"

# 4. Run the early storefront tests (example)
# Preferred: use background_process in agent context, or two terminals.
# Human quick start:
python -m http.server 8080 --directory demo_site
# In another terminal / same shell context:
python -m pytest tests/day0 -q --tb=short
# -q            → quiet: only show summary (dots + final counts), less noise
# --tb=short    → short tracebacks: just the failing assertion + compact stack
```

The actual implementation order, commands, and post-milestone human verification requirements are defined in `implementation-prompt` and `docs/milestone-checklist.md`.

---

## Reference Material

The following live in `docs/`:

- [How to Test M3 (with visible browser)](docs/how-to-test-m3.md) — step-by-step guide to run the full deterministic healing loop yourself
- [How to Test M4 — Gradio UI](docs/how-to-test-m4.md) — mutation selector, real runner integration, approval gate, 9 manual acceptance steps, simulation commands
- [How to Test M5 — LLM Specialists](docs/how-to-test-m5.md) — DEMO_MODE verification, mocked integration tests, context rules, system prompt loading, optional real-key manual testing (recommended after M5)
- [Milestone Quick Reference](docs/milestone-checklist.md) — concise checklist for implementers (includes mandatory human verification checks after each milestone)
- [Full original MVP list](docs/mvp-full.md) — ignore until the Minimum Demoable Slice is green
- [Demo & Pitch script](docs/demo-pitch.md)
- [Submission checklist](docs/submission-checklist.md)
- `docs/implementation-log.md` — real results log (updated during implementation)

The authoritative documents for building the slice are at the project root:
- `implementation-prompt`
- `AGENT_BRIEF.md`



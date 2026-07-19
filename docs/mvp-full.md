# TestPilot — Full MVP Definition (Reference)

This is the original ambitious must-ship list. Do **not** work on these until the Minimum Demoable Slice is working end-to-end and reliable.

## Must-ship capabilities (full list)

| Capability | Definition of success |
|---|---|
| Natural-language intent | User enters a supported request, for example: “Add the blue backpack to cart and confirm the cart contains one item.” |
| Intent Planner | OpenRouter model returns a Pydantic-validated `FlowSpec` JSON object |
| Script Generator | A safe template turns `FlowSpec` into readable Playwright Python code or deterministic executable steps |
| Playwright Executor | Chromium run produces pass/fail status, error information, screenshot on failure, and trace when available |
| Controlled mutation | A selected Shop v2 UI change causes the baseline test to fail predictably |
| Diagnosis | LLM returns structured plain-English cause, failed step, repairability, and preferred repair strategy |
| Repair proposal | LLM proposes one concrete replacement locator/action with rationale |
| Human approval | User explicitly clicks **Approve & Validate Repair**; the system never silently edits and deploys a test |
| Repair validation | Candidate must match exactly one visible/enabled element, action must succeed, and business assertion must pass |
| Full rerun | Repaired journey passes and result is displayed in the UI |
| Audit timeline | UI shows `Planned → Generated → Running → Failed → Diagnosed → Repair proposed → Approved → Validated → Passed` |
| Live deployment | Public Render URL works in incognito |

## MVP non-goals

Do **not** build these unless the Minimum Demoable Slice is complete and stable:

- Arbitrary website crawling or discovery.
- CAPTCHA, authentication bypass, or scraping arbitrary websites.
- Multi-browser execution; use Chromium only.
- Full visual regression history platform.
- Real database, user accounts, RBAC, Redis, queues, Kafka, Kubernetes, or RAG.
- Multiple LLM providers or model-routing logic.
- Autonomous source-code commits.
- Full CI/CD deployment automation.
- Allure integration.

## M2 Lesson (added after real implementation)
For M2 and later, the controlled storefront server must be explicitly started before any runner code or integration tests (`python -m http.server 8080 --directory demo_site`). This is a hard prerequisite that has caused repeated "port in use" or hanging failures when forgotten. All future docs and demos must call this out.

## M3 Lessons (added after real implementation)
- Runner must support both "brittle" and "repaired" strategies (generalize before/while doing M3).
- Healing flow must perform the exact validator checks: count==1, visible, enabled, click, cart==1.
- Human approval is a hard explicit gate (boolean approve param; never auto-apply).
- After code, execute and record exactly 3 full deterministic loops (baseline pass + 2x mutated+approve→HEALED) and inspect the healing manifest.
- 30s brittle timeout and external storefront prerequisite remain. Use targeted python -c or specific nodes.
- New subpackages require __init__.py. Re-run unit tests immediately after runner edits.
- Everything in M3 must be deterministic (DEMO_MODE, no network, no real LLM calls).

## M4 Lessons (added after real implementation)
- Keep Gradio callbacks thin — real logic belongs in `testpilot/ui/services.py` (runner + M3 deterministic calls). Layout only wires UI.
- Gradio queue: use `demo.queue(default_concurrency_limit=1)`. Old `concurrency_count` kwarg can break on newer versions.
- Mutation radio must drive the actual Playwright URL (`?mutation=...`). Previews must match the real storefront JS behavior.
- Approval controls visibility: only show Approve/Reject when a proposal is pending and not yet approved.
- Fast simulation: use `python -c "from testpilot.ui import services; ..."` (with `headless=False` when watching).
- Still requires external storefront on 8080. Brittle failures are slow by design.
- Start the app with `background_process`. Verify reachability.
- After approve, healing-style manifests must contain diagnosis/proposal/approved/validation/repaired_result.
- New subpackage needs `__init__.py`. Re-run full unit tests after runner/services changes.
- M4 is 100% deterministic — no LLM calls allowed yet.
- See `docs/how-to-test-m4.md` for the 9 manual UI acceptance steps and simulation commands.

## M5 Lessons (added after real implementation)
- Automated tests must **never** call the real LLM (spec requirement). Use `DEMO_MODE=true` or mocks in `tests/integration/test_llm_services.py`.
- Always return `(result, reasoning_mode)` from specialists. Record `"llm"` or `"fallback"` in manifests / RunResult.
- Context is strictly whitelisted + truncated. Never pass full HTML, traces, raw screenshots, etc.
- Load system prompts from `prompts/<specialist>.md` as the fixed system message (user intent is never the system prompt).
- Pydantic validation on every LLM response. Any failure (bad JSON, timeout, schema error, no key, DEMO_MODE) → deterministic fallback.
- Fallbacks reuse M3 deterministic logic (GOLDEN_FLOWSPEC for planner, existing diagnosis/repair for the others).
- Patch the correct object in tests (`llm_client.ChatOpenAI` or provide MagicMock).
- Re-run full unit layer after adding the `testpilot/llm/` package.
- M5 is still narrow specialists only. No sub-agents, no raw execution. Human approval remains a hard gate.
- See `docs/how-to-test-m5.md` for DEMO_MODE verification, mocked tests, context inspection, and optional real-key manual steps.
- M4 must be complete and verified before introducing LLM specialists. Deterministic path must stay fully functional.

## M9 Lessons (added after implementation)
- CI must fail loudly; do not mask integration/e2e failures with `|| echo ...` in workflow steps.
- Start the controlled storefront inside CI before integration/evals and probe `BASE_URL` explicitly.
- Always force deterministic CI env (`DEMO_MODE=true`, `LANGSMITH_TRACING=false`, empty OpenRouter key).
- Treat pytest exit code 5 (no tests collected) intentionally in the e2e step; pass only for that specific code path.
- Upload artifacts on CI failure (`artifacts/**`, storefront logs, pytest cache) so debugging can happen without rerunning blindly.
- Keep Docker verification split: build in CI; run smoke locally and in deployment target.

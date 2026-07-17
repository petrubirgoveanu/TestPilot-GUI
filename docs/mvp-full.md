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

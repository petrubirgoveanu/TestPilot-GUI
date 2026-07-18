# TestPilot — Demo & Pitch Script (Reference)

Use the 5-minute structure only after the Minimum Demoable Slice is solid.

## Five-minute Loom structure

| Time | Visual | Message |
|---:|---|---|
| 0:00–0:25 | Public deployed URL | Problem: brittle browser tests after UI changes |
| 0:25–0:55 | Architecture diagram | Mermaid diagram + narrow LLM specialists (Planner/Diagnosis/Repair) with dedicated system prompts. Human approval is a hard gate. Deterministic fallback is first-class. |
| 0:55–1:25 | Intent input and FlowSpec/test | LLM output is constrained; no unrestricted code execution |
| 1:25–1:50 | Shop v1 success | Baseline journey passes |
| 1:50–2:35 | Select Shop v2 mutation, run fails | UI change breaks the original locator; screenshot/trace captured |
| 2:35–3:20 | Diagnosis and repair diff | System explains the cause and proposes a semantic locator repair |
| 3:20–4:00 | Approve and validate | Human approval, unique/visible/action/assertion checks, full rerun |
| 4:00–4:30 | Green final result and run evidence | Repaired journey passed; report/artifacts are available |
| 4:30–5:00 | README + v2 roadmap | Future: multi-flow coverage, visual regression, CI integrations |

## Live demo rule

Use one specific mutation known to pass reliably. Do not gamble on random selection during the main pitch.

## Agentic Architecture (for the pitch)

- Only **narrow specialists** (Planner, Diagnosis, Repair), each with its own system prompt file in `prompts/`.
- No general agents, no autonomous browsing, no raw code execution.
- Human must click **Approve & Validate Repair** — repairs are never auto-applied.
- On any LLM failure the system falls back to deterministic behavior and records `reasoning_mode: "fallback"`.
- LangGraph (or plain sequential functions for the slice) orchestrates the flow.

## Backup plan

- Record a 60–90 second backup video as soon as the deployed flow first works.
- Record the final five-minute Loom after feature freeze.
- Keep screenshots and an example run manifest in the repository/docs.
- If Render or LLM connectivity fails live, demonstrate the deployed UI in replay mode and show the backup recording.

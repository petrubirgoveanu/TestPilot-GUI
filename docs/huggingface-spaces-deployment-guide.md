# Hugging Face Spaces Deployment Guide (Docker)

This guide is tailored to this repository and mirrors the practical style used in the Render guide.

## Goal

Deploy TestPilot to a public Hugging Face Docker Space with stable startup and clear environment setup.

## Expected Deployed App URL

Hugging Face Spaces URL pattern:

- https://huggingface.co/spaces/<username-or-org>/<space-name>

App URL pattern:

- https://<space-name>.hf.space

Example:

- Space page: https://huggingface.co/spaces/your-user/testpilot-gui
- Public app URL: https://testpilot-gui.hf.space

Important distinction:

- App URL is where Gradio UI is hosted.
- BASE_URL is the storefront URL used by Playwright for mutation pages.
- BASE_URL can be the same domain only if that domain serves /index.html for the mutation lab.

## Prerequisites

- Hugging Face account
- Public repository access for this codebase
- Dockerfile in repo root (already present)

## Configuration Profiles

Use these profile templates from the repo:

- Local run profile: .env.local.example
- Production profile reference: .env.production.example

For Hugging Face Spaces, set values in Space Settings (Variables and Secrets), not in git files.

## Create the Space

1. Go to https://huggingface.co/new-space.
2. Owner: choose your account or org.
3. Space name: testpilot-gui (or your preferred name).
4. SDK: Docker.
5. Visibility: Public (recommended for demo).
6. Hardware: CPU Basic (free tier).
7. Create Space.

## Connect Your Code

Use one of these methods.

### Method A: Push repository to Space git remote

1. Open the new Space page.
2. Copy the Space git URL (shown in Space page instructions).
3. Add remote locally:
   - git remote add hf https://huggingface.co/spaces/<owner>/<space-name>
4. Push:
   - git push hf main

### Method B: Import from GitHub (if available in your UI)

1. In Space settings or creation flow, choose GitHub import.
2. Select repository petrubirgoveanu/TestPilot-GUI.
3. Confirm branch main.

## Environment Variables and Secrets

Open Space -> Settings -> Variables and secrets.

Add these keys:

- OPENROUTER_API_KEY (Secret)
- LLM_MODEL (Variable)
- DEMO_MODE (Variable)
- BASE_URL (Variable)
- LANGSMITH_TRACING (Variable)
- LANGSMITH_API_KEY (Secret)
- LANGSMITH_PROJECT (Variable)
- LANGSMITH_ENDPOINT (Variable)

Recommended demo values:

- LLM_MODEL = openai/gpt-4o-mini
- DEMO_MODE = true
- LANGSMITH_TRACING = false
- LANGSMITH_PROJECT = testpilot-hackathon

BASE_URL guidance:

- Do not set BASE_URL to localhost in Spaces.
- If your Space does not serve /index.html, use a separate hosted storefront domain.

Path examples:

- App URL example: https://testpilot-gui.hf.space
- BASE_URL example (same-domain): https://testpilot-gui.hf.space
- BASE_URL example (separate-domain): https://demo-storefront.example.com
- Baseline mutation example: https://demo-storefront.example.com/index.html?mutation=baseline
- testid_removed mutation example: https://demo-storefront.example.com/index.html?mutation=testid_removed

## Docker and Runtime Notes

- Keep Dockerfile in repo root.
- Keep app startup command from Dockerfile CMD.
- This app reads PORT dynamically and defaults to 7860, which is compatible with Spaces Docker hosting.

## First Deployment Validation Checklist

After first build is green:

1. Open app URL in normal browser.
2. Open app URL in incognito.
3. Confirm UI loads.
4. Confirm no runtime crash in Space logs.
5. Confirm BASE_URL mutation pages load.

## Detailed Manual Testing (Post-Deployment)

For compact execution use:

- docs/huggingface-post-deploy-qa-checklist.md

### A. Service Smoke

1. Open app URL.
   - Example: https://testpilot-gui.hf.space
2. Open in incognito.
3. Confirm Gradio UI renders.

### B. Validate BASE_URL Directly

1. Copy BASE_URL from Space settings.
2. Open BASE_URL/index.html?mutation=baseline.
3. Open BASE_URL/index.html?mutation=testid_removed.

Expected:

- Both URLs load.
- Mutated page still has Add Blue Backpack button.

### C. Baseline Run

1. In UI, choose mutation baseline.
2. Click Generate & Run Original Regression.
3. Wait for completion.

Expected:

- Final status indicates successful completion.
- Approval controls are not required for baseline pass.

### D. Mutation Failure and Proposal

1. Choose mutation testid_removed from UI Change Lab.
2. Confirm Target URL includes ?mutation=testid_removed.
3. Click Generate & Run Original Regression.

Expected:

- Initial status is failed.
- Error excerpt and screenshot appear.
- Diagnosis and repair proposal appear.
- Approve and Reject buttons appear.

### E. Approval Path

1. Click Approve & Validate Repair.
2. Wait for completion.

Expected:

- Final status becomes healed.
- Timeline includes Approved, Validated, Healed.

### F. Rejection Path

1. Re-run mutation failure path.
2. Click Reject Repair.

Expected:

- Final status becomes rejected.

## Troubleshooting

### Build fails before app start

Check:

- Space type is Docker.
- Dockerfile exists at repo root.
- Latest commit reached the Space.

### App loads but run action fails

Likely BASE_URL problem.

Fix:

- Set BASE_URL to a real storefront host serving mutation paths.

### Secret/key issues

Fix:

- Put API keys in Secrets, not Variables.
- Keep DEMO_MODE=true if you want deterministic mode without external API calls.

## Recommended Free-Tier Baseline

- Hardware: CPU Basic (free)
- DEMO_MODE: true
- LANGSMITH_TRACING: false
- Dockerfile: repo root
- BASE_URL: real storefront URL (not localhost)

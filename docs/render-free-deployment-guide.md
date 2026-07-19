# Render Free Deployment Guide (Docker Web Service)

This guide matches the Render onboarding screens you shared and is tailored to this repository.

## Goal

Deploy TestPilot on Render Free tier with stable startup and clear settings for every field.

## Expected Deployed App URL

Render creates the public app URL from your service name.

Expected pattern:

- https://<service-name>.onrender.com

For this guide (service name testpilot-gui), expected app URL is:

- https://testpilot-gui.onrender.com

Important distinction:

- App URL is where the Gradio UI is hosted.
- BASE_URL is the storefront URL used by Playwright for index.html mutation pages.
- BASE_URL can be the same domain only if that domain actually serves /index.html for the mutation lab.

Should App URL and BASE_URL be the same?

- They can be the same, but only if your deployed app domain serves the mutation storefront at /index.html.
- They can be different when storefront is hosted separately.

Two valid patterns:

1. Same-domain pattern:
  - App URL: https://testpilot-gui.onrender.com
  - BASE_URL: https://testpilot-gui.onrender.com
  - Baseline: https://testpilot-gui.onrender.com/index.html?mutation=baseline
  - Mutation: https://testpilot-gui.onrender.com/index.html?mutation=testid_removed

2. Separate-domain pattern:
  - App URL: https://testpilot-gui.onrender.com
  - BASE_URL: https://demo-storefront.onrender.com
  - Baseline: https://demo-storefront.onrender.com/index.html?mutation=baseline
  - Mutation: https://demo-storefront.onrender.com/index.html?mutation=testid_removed

Path examples:

- App URL example: https://testpilot-gui.onrender.com
- BASE_URL example (same-domain): https://testpilot-gui.onrender.com
- BASE_URL example (separate-domain): https://demo-storefront.onrender.com
- Baseline mutation example (same-domain): https://testpilot-gui.onrender.com/index.html?mutation=baseline
- Baseline mutation example (separate-domain): https://demo-storefront.onrender.com/index.html?mutation=baseline
- testid_removed example (same-domain): https://testpilot-gui.onrender.com/index.html?mutation=testid_removed
- testid_removed example (separate-domain): https://demo-storefront.onrender.com/index.html?mutation=testid_removed

## Important Notes Before You Click Deploy

- The app now honors Render dynamic PORT at startup (updated in app.py).
- Keep Docker Command empty unless you are debugging.
- For free tier reliability, start with DEMO_MODE=true.

## Configuration Profiles

Use these profile templates as quick references:

- Local run profile: .env.local.example
- Production (Render) profile: .env.production.example

How to use:

1. Keep .env.example as the neutral placeholder template.
2. For local runs, copy values from .env.local.example into .env.
3. For Render, copy values from .env.production.example into Render Environment Variables (not into git).

Optional helper script (PowerShell):

1. Switch to local template:
  - .\scripts\switch-env-profile.ps1 -Profile local -Force
2. Switch to production template:
  - .\scripts\switch-env-profile.ps1 -Profile production -Force

Notes:

- Without -Force, the script will refuse to overwrite an existing .env.
- After switching, fill placeholders in .env before running locally.

## Screen 1: Configure Service

### Source Code

- Repository: petrubirgoveanu/TestPilot-GUI
- Action: keep selected repository.

Comment:
- Render auto-detected Docker because this repo contains a Dockerfile.

### Name

Recommended value:
- testpilot-gui

Comment:
- Use lowercase and hyphens. The name is part of your public URL.

### Language

Value:
- Docker

Comment:
- Correct for this repo. Do not switch to Python runtime mode.

### Branch

Value:
- main

Comment:
- Deploys your merged main branch.

### Region

Value:
- Frankfurt (EU Central) or the closest region to your users.

Comment:
- Choose same region for related services to reduce latency.

### Root Directory (Optional)

Value:
- leave empty

Comment:
- This repo root already contains Dockerfile and app.py.

## Screen 2: Instance Type

### Instance Type

Value:
- Free

Comment:
- Good for demos and hackathon submission.
- Free instances sleep after inactivity and can have cold starts.

## Screen 3: Environment Variables

Add these variables exactly:

- OPENROUTER_API_KEY = your key (optional if DEMO_MODE=true)
- LLM_MODEL = openai/gpt-4o-mini
- DEMO_MODE = true
- BASE_URL = your storefront URL (see note below)
- LANGSMITH_ENDPOINT = (optional, empty if unused)
- LANGSMITH_TRACING = false
- LANGSMITH_API_KEY = (optional, empty if unused)
- LANGSMITH_PROJECT = testpilot-hackathon

Comments per variable:

- OPENROUTER_API_KEY
  - Needed only when DEMO_MODE=false and you want real LLM calls.

- LLM_MODEL
  - Default model used by the app when LLM mode is enabled.

- DEMO_MODE
  - true is safest for deterministic demo behavior and no API spend.

- BASE_URL
  - Must point to a URL that serves index.html for the mutation lab.
  - The app builds URLs like: BASE_URL/index.html?mutation=baseline
  - Same-domain example: https://testpilot-gui.onrender.com/index.html?mutation=baseline
  - Same-domain example: https://testpilot-gui.onrender.com/index.html?mutation=testid_removed
  - Separate-domain example: https://demo-storefront.onrender.com/index.html?mutation=baseline
  - Separate-domain example: https://demo-storefront.onrender.com/index.html?mutation=testid_removed
  - If your app does not host demo_site at that path, use a separate hosted demo storefront URL.

CRITICAL BASE_URL REQUIREMENT:

- BASE_URL is not optional for end-to-end run behavior.
- Do not leave BASE_URL as localhost in Render.
- Do not keep a placeholder value in production.
- If BASE_URL is wrong, UI loads but Playwright runs fail.

- LANGSMITH_* variables
  - Keep tracing off unless you explicitly need observability.

## Screen 4: Advanced

### Secret Files

Value:
- none

Comment:
- Not needed for this setup.

### Health Check Path

Recommended value:
- /

Comment:
- Use root path for Gradio service health checks.
- Avoid /healthz unless you have implemented that route.

### Registry Credential

Value:
- No credential

Comment:
- Correct for public Docker build from repo.

### Docker Build Context Directory

Value:
- .

Comment:
- Build context is repository root.

### Dockerfile Path

Recommended value:
- Dockerfile

Comment:
- Do not set this to .
- If left blank, Render usually defaults to ./Dockerfile.

### Docker Command

Value:
- leave empty

Comment:
- Render uses Dockerfile CMD: python app.py.
- This is preferred because app.py now reads PORT automatically.

### Pre-Deploy Command

Value:
- leave empty

Comment:
- No migration step required.

### Auto-Deploy

Recommended value:
- On Commit

Comment:
- Useful while iterating quickly.

### Build Filters (Included Paths / Ignored Paths)

Value:
- leave empty initially

Comment:
- Empty means any commit in repo can trigger deploy.
- Add filters later only if you need to reduce rebuilds.

## Final Action

Click Deploy Web Service.

## Blueprint Option (Recommended for Repeatable Deploys)

This repository now includes a Render Blueprint file:

- render.yaml

What this gives you:

- Same settings every redeploy (plan, region, Docker config, health path)
- Less manual form filling
- Safer secret handling (`OPENROUTER_API_KEY` and `LANGSMITH_API_KEY` are marked `sync: false`)

How to use it:

1. Push the latest commit (with `render.yaml`) to `main`.
2. In Render, click New, then Blueprint.
3. Select this repository.
4. Render reads `render.yaml` and preconfigures the service.
5. Fill only required secrets and adjust `BASE_URL` to your real storefront host.
6. Deploy.

Important blueprint note:

- `BASE_URL` in `render.yaml` is a placeholder.
- Replace it with the real URL that serves `index.html` and accepts `?mutation=...`.
- Example replacement (same-domain): https://testpilot-gui.onrender.com
- Example replacement (separate-domain): https://demo-storefront.onrender.com

Hard rule:

- Never deploy with the default placeholder BASE_URL.
- Always replace it before first deploy or before promoting any redeploy.

## Detailed Manual Testing (Post-Deployment)

Run this exact checklist after Render reports Deploy successful.

For a compact execution version, use:

- docs/render-post-deploy-qa-checklist.md

### A. Service Smoke and Availability

1. Open your Render service URL in a normal browser profile.
  - Example: https://testpilot-gui.onrender.com
2. Confirm the page title and main UI render.
3. Open the same URL in incognito/private mode.
  - Example: https://testpilot-gui.onrender.com
4. Confirm it still loads without login/session dependency.

Pass criteria:

- UI is reachable in both normal and incognito modes.
- No Render 502/503 page.

### B. Validate BASE_URL Directly

1. In Render service Settings, copy the current BASE_URL env value.
2. Open this URL in the browser:
  - BASE_URL/index.html?mutation=baseline
  - Same-domain example: https://testpilot-gui.onrender.com/index.html?mutation=baseline
  - Separate-domain example: https://demo-storefront.onrender.com/index.html?mutation=baseline
3. Open this URL in the browser:
  - BASE_URL/index.html?mutation=testid_removed
  - Same-domain example: https://testpilot-gui.onrender.com/index.html?mutation=testid_removed
  - Separate-domain example: https://demo-storefront.onrender.com/index.html?mutation=testid_removed

Pass criteria:

- Both URLs return a valid HTML page.
- The testid_removed page still shows the Add Blue Backpack button.

If this fails:

- Fix BASE_URL first.
- Redeploy.
- Repeat section B before running app-level tests.

### C. Baseline Journey Test in the App

1. In the deployed app, set UI Change Lab to baseline.
2. Click Generate & Run Original Regression.
3. Wait for execution to finish.

Expected outcome:

- Final Status shows a passing terminal state (commonly healed for baseline fast path).
- Approve & Validate Repair button is not shown.
- Timeline indicates planned/run/pass sequence.

### D. Mutation Failure and Repair Proposal

How to set UI Change Lab to `testid_removed` in Gradio:

1. Open your deployed app URL.
  - Example: https://testpilot-gui.onrender.com
2. At the top area of the page, find the radio section labeled UI Change Lab — Select Mutation.
3. Click the option text that starts with: Remove test ID — UI refactor removes data-testid.
4. Verify Target URL used by Playwright now ends with: ?mutation=testid_removed.

If you do not see the radio control:

1. Refresh the page once.
2. Scroll to the top controls area.
3. Confirm the app loaded fully (no Render loading spinner or error banner).

1. Click Generate & Run Original Regression.
2. Wait for failure state.

Expected outcome:

- Final Status shows failed before approval.
- Error excerpt is populated.
- Failure screenshot is shown.
- Diagnosis text appears.
- Repair proposal/code diff appears.
- Approve & Validate Repair and Reject Repair buttons are visible.

### E. Approval Path (Heal Verification)

1. Click Approve & Validate Repair.
2. Wait for validation + repaired rerun to complete.

Expected outcome:

- Final Status becomes healed.
- Timeline includes Approved, Validated, then Healed.
- Manifest path is populated.

### F. Rejection Path (Human Gate Verification)

1. Re-run step D (testid_removed) to get a fresh proposal.
2. Click Reject Repair.

Expected outcome:

- Final Status becomes rejected.
- Timeline appends Rejected.
- No healed status is shown.

### G. Artifact and Manifest Spot Check

1. In the app, copy Run Manifest Path from the latest run.
2. Open Render logs and verify there are no unhandled exceptions.
3. Confirm run evidence appeared in the UI during failed and healed runs.

Pass criteria:

- Failure run shows evidence (error + screenshot).
- Approval run shows healed state only after validation.
- Rejection run does not auto-heal.

### H. Final Manual Sign-Off Criteria

Mark deployment as validated only if all are true:

1. Service URL opens in normal and incognito.
  - Example: https://testpilot-gui.onrender.com
2. BASE_URL baseline and mutation URLs both load.
  - Same-domain baseline: https://testpilot-gui.onrender.com/index.html?mutation=baseline
  - Same-domain mutation: https://testpilot-gui.onrender.com/index.html?mutation=testid_removed
  - Separate-domain baseline: https://demo-storefront.onrender.com/index.html?mutation=baseline
  - Separate-domain mutation: https://demo-storefront.onrender.com/index.html?mutation=testid_removed
3. Baseline run completes successfully.
4. Mutation run fails first, then heals only after approval.
5. Rejection path results in rejected status.

## First Deployment Validation Checklist

After deployment completes:

1. Open the Render public URL in normal browser and incognito.
  - Example: https://testpilot-gui.onrender.com
2. Confirm app UI loads.
3. Check Render logs for server startup line and port binding.
4. If you use mutation runs, confirm BASE_URL serves index.html.
  - Same-domain baseline: https://testpilot-gui.onrender.com/index.html?mutation=baseline
  - Same-domain mutation: https://testpilot-gui.onrender.com/index.html?mutation=testid_removed
  - Separate-domain baseline: https://demo-storefront.onrender.com/index.html?mutation=baseline
  - Separate-domain mutation: https://demo-storefront.onrender.com/index.html?mutation=testid_removed

## Troubleshooting

### Deploy succeeds but service stays unhealthy

Check these first:
- Health Check Path is set to /
- Dockerfile Path is Dockerfile (not .)
- Render logs show app listening on assigned PORT

### UI loads but run action fails

Likely BASE_URL issue.

Fix:
- Set BASE_URL to a real hosted storefront URL that serves index.html and mutation query params.
- Same-domain example: https://testpilot-gui.onrender.com
- Separate-domain example: https://demo-storefront.onrender.com

### LLM calls fail

Fix options:
- Keep DEMO_MODE=true for deterministic mode, or
- Set DEMO_MODE=false and provide valid OPENROUTER_API_KEY

## Recommended Free-Tier Baseline

Use this profile for reliable hackathon demo:

- Instance: Free
- DEMO_MODE: true
- LANGSMITH_TRACING: false
- Health Check Path: /
- Docker Command: empty
- Auto-Deploy: On Commit

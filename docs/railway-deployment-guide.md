# Railway Deployment Guide (Docker Web Service)

This guide is tailored to this repository and mirrors the practical style used in the Render docs.

## Goal

Deploy TestPilot on Railway with a Docker service, stable startup, and the right environment variables for the app and Playwright runner.

## What Railway Should Run

This repo already supports Railway-style runtime startup:

- app.py reads the dynamic PORT environment variable.
- Dockerfile starts the app with python app.py.
- The service exposes the Gradio UI, not the storefront used by Playwright.

That means the Railway setup should focus on Docker, env vars, and the public service URL.

## Expected Public URL

Railway creates a public service URL for the app, or you can attach a custom domain.

Use that Railway service URL for the Gradio app.

Important distinction:

- App URL is where the Gradio UI is hosted.
- BASE_URL is the storefront URL used by Playwright for index.html mutation pages.
- BASE_URL can be the same domain only if that domain actually serves /index.html for the mutation lab.

## Recommended Railway Setup

Use the options in the Railway service settings screen as follows.

### Networking

- Public networking: enabled through Railway's generated public domain or your custom domain.
- Private networking: leave as-is unless you have a second private service.
- Outbound IPv6: leave off unless you specifically need it.

Comment:

- You only need the public app URL for the demo. The app itself does not need a custom networking setup.

### Scale

- Replicas: 1
- Resource limits: leave at the default free-tier values.

Comment:

- A single replica is the right starting point for this app.
- Do not increase scale unless you have a specific reason and a paid plan.

### Build

- Builder: Dockerfile detection
- Dockerfile path: Dockerfile
- Build context: repository root
- Watch paths: optional, leave empty initially

Comment:

- This repo already has a root Dockerfile, so Railway should auto-detect Docker.
- Do not switch to a Python runtime template unless you are intentionally changing the deployment model.

### Deploy

- Start command: leave empty if Railway uses the Dockerfile CMD
- Pre-deploy command: leave empty
- Teardown: leave off
- Health check path: /health
- Auto deploy: on for main

Comment:

- python app.py already binds to Railway's assigned port.
- Health checks should hit /health for a lightweight 200 response.

### Config-as-code

- Leave empty unless you add a Railway config file later.

Comment:

- The repo currently uses Docker plus environment variables, which is enough for a clean Railway setup.

### Feature Flags

- Leave defaults off.

Comment:

- None of the Railway preview flags are required for this app.

## Environment Variables

Add these in Railway's Variables section.

- OPENROUTER_API_KEY = your key, required only when DEMO_MODE=false
- LLM_MODEL = openai/gpt-4o-mini
- DEMO_MODE = true
- BASE_URL = your storefront URL that serves index.html
- LANGSMITH_ENDPOINT = empty unless you use LangSmith
- LANGSMITH_TRACING = false
- LANGSMITH_API_KEY = empty unless you use LangSmith
- LANGSMITH_PROJECT = testpilot-hackathon

## Minimum Setup To Test the App

If you only want to confirm that Railway starts the container and shows the Gradio UI, you can keep it very simple:

- DEMO_MODE = true
- leave OPENROUTER_API_KEY empty
- leave the LangSmith variables empty

In that case, the app should still boot because the runtime defaults are already safe.

## Minimum Setup To Test the Full Regression Flow

To run the actual baseline and mutation tests from the UI, you need one extra thing:

- BASE_URL must point to a real public storefront that serves index.html

Without that, the app may load but the Playwright journey will fail when it tries to open the mutation pages.

Comments per variable:

- OPENROUTER_API_KEY
  - Needed only when you want real LLM calls.

- LLM_MODEL
  - Default model used by the narrow LLM helpers.

- DEMO_MODE
  - Set to true for the safest hackathon demo path.

- BASE_URL
  - Must point to a real hosted storefront URL that serves index.html.
  - The app builds URLs like BASE_URL/index.html?mutation=baseline.
  - If your Railway app does not serve the storefront itself, use a separate hosted storefront URL.

- LANGSMITH_*
  - Keep tracing off unless you explicitly need observability.

### Critical BASE_URL Rule

- Do not leave BASE_URL pointing at localhost in Railway.
- Do not keep a placeholder value in production.
- If BASE_URL is wrong, the app UI can still load but Playwright runs will fail.
- If you have not deployed the storefront yet, you can still smoke-test the app URL first and add BASE_URL later.

## Practical Recommendation

For this repository, the safest default is:

- Railway hosts the Gradio app.
- A separate storefront host serves the mutation pages.
- BASE_URL points to that storefront host, not to the Railway app itself.

If you later make Railway serve the storefront too, you can switch to a same-domain BASE_URL.

## Same-Service Storefront (Now Supported)

This app can now serve both:

- Gradio UI at `/`
- Demo storefront at `/shop`

So on Railway you can use a single service with:

- App URL: `https://<your-service>.up.railway.app/`
- BASE_URL: `https://<your-service>.up.railway.app/shop`

Mutation URL examples in this mode:

- `https://<your-service>.up.railway.app/shop/index.html?mutation=baseline`
- `https://<your-service>.up.railway.app/shop/index.html?mutation=testid_removed`

## Suggested Values From the Screens You Have

If the Railway screen asks for these options, use:

- Region: closest to your users
- Service name: testpilot-gui
- Environment/runtime: Docker
- Replica count: 1
- Health check path: /
- Health check path: /health
- Dockerfile path: Dockerfile
- Docker/Start command: leave empty
- Auto deploy from main: on

## Deployment Steps

1. Push the latest code to main.
2. Create or open the Railway service.
3. Choose Docker deployment.
4. Confirm the Dockerfile is detected from the repository root.
5. Set the environment variables listed above.
6. Keep the start command empty.
7. Deploy the service.

## First Validation Checklist

After the service is live:

1. Open the Railway public app URL in a normal browser.
2. Open the same URL in incognito/private mode.
3. Confirm the Gradio UI loads.
4. Check Railway logs for a clean startup and the assigned port binding.
5. Open BASE_URL/index.html?mutation=baseline.
6. Open BASE_URL/index.html?mutation=testid_removed.

Expected:

- The app is reachable in both normal and incognito modes.
- Both mutation URLs return HTML.
- The mutated page still shows the Add Blue Backpack button.

## Quick Demo Checklist

1. Run the baseline journey and confirm it passes.
2. Run the testid_removed mutation and confirm it fails first.
3. Approve the repair and confirm the validated rerun heals.
4. Run the rejection path and confirm it stays rejected.

## Troubleshooting

### The Railway service starts but the UI is unhealthy

Check these first:

- Dockerfile is at the repository root.
- Health check path is /
- Railway logs show the app listening on the assigned PORT.

### The UI loads but Playwright runs fail

This is usually a BASE_URL issue.

Fix:

- Point BASE_URL to a real storefront host that serves index.html.
- Avoid localhost values in Railway.

### The app tries to use the LLM and fails

Fix options:

- Keep DEMO_MODE=true.
- Or set DEMO_MODE=false and provide a valid OPENROUTER_API_KEY.

## Recommended Free-Tier Baseline

Use this profile for the most reliable Railway demo:

- Docker deployment
- One replica
- Health check path /
- Health check path /health
- DEMO_MODE=true
- LANGSMITH_TRACING=false
- BASE_URL points to a real storefront host

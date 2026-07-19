# Render Post-Deploy QA Checklist

Use this checklist right after a Render deployment finishes.

## Scope

Validate that:
- service is reachable,
- BASE_URL is correct,
- baseline run passes,
- mutation run fails first then heals only after approval,
- rejection path remains rejected.

## Inputs You Need

- Render service URL
- Current BASE_URL environment value from Render settings

Examples:

- Render service URL example: https://testpilot-gui.onrender.com
- BASE_URL example (same-domain): https://testpilot-gui.onrender.com
- BASE_URL example (separate-domain): https://demo-storefront.onrender.com
- Baseline mutation example (same-domain): https://testpilot-gui.onrender.com/index.html?mutation=baseline
- Baseline mutation example (separate-domain): https://demo-storefront.onrender.com/index.html?mutation=baseline
- testid_removed example (same-domain): https://testpilot-gui.onrender.com/index.html?mutation=testid_removed
- testid_removed example (separate-domain): https://demo-storefront.onrender.com/index.html?mutation=testid_removed

## Quick Pass/Fail Board

- [ ] Service reachable (normal browser)
- [ ] Service reachable (incognito)
- [ ] BASE_URL baseline URL loads
- [ ] BASE_URL mutation URL loads
- [ ] Baseline journey run succeeds
- [ ] Mutation journey initially fails
- [ ] Approve path heals
- [ ] Reject path stays rejected
- [ ] Logs show no unhandled exceptions

## Step-by-Step Execution

### 1. Smoke Test the Service

1. Open the Render service URL in a normal browser tab.
	- Example: https://testpilot-gui.onrender.com
2. Open the same URL in incognito/private mode.
	- Example: https://testpilot-gui.onrender.com
3. Confirm UI loads in both places.

Expected:
- App UI visible in both sessions.
- No 502/503 from Render.

### 2. Validate BASE_URL Target

1. Copy BASE_URL from Render environment variables.
2. Open BASE_URL/index.html?mutation=baseline.
	- Example: https://demo-storefront.onrender.com/index.html?mutation=baseline
3. Open BASE_URL/index.html?mutation=testid_removed.
	- Example: https://demo-storefront.onrender.com/index.html?mutation=testid_removed

Expected:
- Both pages load HTML.
- Mutated page still contains Add Blue Backpack button.

If failed:
- Fix BASE_URL.
- Redeploy.
- Restart checklist from step 1.

### 3. Baseline Run

1. In app UI, select mutation baseline.
2. Click Generate & Run Original Regression.
3. Wait for completion.

Expected:
- Final Status indicates successful completion.
- Approval buttons are not required for baseline pass.

### 4. Mutation Failure and Proposal

1. In the top controls area, find UI Change Lab — Select Mutation.
2. Click the radio option: Remove test ID — UI refactor removes data-testid.
3. Confirm Target URL used by Playwright ends with ?mutation=testid_removed.
	- Example target URL: https://demo-storefront.onrender.com/index.html?mutation=testid_removed
4. Click Generate & Run Original Regression.
5. Wait for completion.

Expected:
- Initial result is failed before any approval.
- Error excerpt appears.
- Screenshot appears.
- Diagnosis and repair proposal appear.
- Approve & Validate Repair and Reject Repair buttons are visible.

### 5. Approval Path

1. Click Approve & Validate Repair.
2. Wait for full validation + repaired rerun.

Expected:
- Final Status becomes healed.
- Timeline includes Approved, Validated, Healed.

### 6. Rejection Path

1. Re-run step 4 to regenerate proposal.
2. Click Reject Repair.

Expected:
- Final Status becomes rejected.
- No healed state is shown for this run.

### 7. Evidence and Logs

1. Check the run evidence in UI (error + screenshot on failure path).
2. Copy Run Manifest Path if shown.
3. Check Render logs for unhandled exceptions during test runs.

Expected:
- Failure evidence appears when expected.
- No critical runtime exceptions in logs.

## Sign-Off Rule

Deployment is QA-approved only when every checkbox in Quick Pass/Fail Board is checked.

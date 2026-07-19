# Hugging Face Spaces Post-Deploy QA Checklist

Use this checklist immediately after a Space build completes.

## Scope

Validate that:

- app URL is reachable,
- BASE_URL is correct,
- baseline run passes,
- mutation run fails first then heals only after approval,
- rejection path remains rejected.

## Inputs You Need

- Hugging Face app URL
- Current BASE_URL value from Space settings

Examples:

- App URL example: https://testpilot-gui.hf.space
- BASE_URL example (same-domain): https://testpilot-gui.hf.space
- BASE_URL example (separate-domain): https://demo-storefront.example.com
- Baseline mutation example: https://demo-storefront.example.com/index.html?mutation=baseline
- testid_removed mutation example: https://demo-storefront.example.com/index.html?mutation=testid_removed

## Quick Pass/Fail Board

- [ ] Service reachable (normal browser)
- [ ] Service reachable (incognito)
- [ ] BASE_URL baseline URL loads
- [ ] BASE_URL mutation URL loads
- [ ] Baseline journey run succeeds
- [ ] Mutation journey initially fails
- [ ] Approve path heals
- [ ] Reject path stays rejected
- [ ] Space logs show no unhandled exceptions

## Step-by-Step Execution

### 1. Smoke Test the Service

1. Open app URL in normal browser.
   - Example: https://testpilot-gui.hf.space
2. Open app URL in incognito.
   - Example: https://testpilot-gui.hf.space
3. Confirm UI loads.

Expected:

- Gradio UI visible in both sessions.

### 2. Validate BASE_URL Target

1. Copy BASE_URL from Space settings.
2. Open BASE_URL/index.html?mutation=baseline.
3. Open BASE_URL/index.html?mutation=testid_removed.

Expected:

- Both pages load.
- Mutated page still contains Add Blue Backpack button.

If failed:

- Fix BASE_URL.
- Restart Space or trigger rebuild.
- Restart checklist from step 1.

### 3. Baseline Run

1. Select mutation baseline.
2. Click Generate & Run Original Regression.
3. Wait for completion.

Expected:

- Final status indicates successful completion.

### 4. Mutation Failure and Proposal

1. In UI Change Lab, select Remove test ID option.
2. Confirm Target URL includes ?mutation=testid_removed.
3. Click Generate & Run Original Regression.
4. Wait for completion.

Expected:

- Initial status is failed.
- Error excerpt appears.
- Screenshot appears.
- Diagnosis and repair proposal appear.
- Approve and Reject controls appear.

### 5. Approval Path

1. Click Approve & Validate Repair.
2. Wait for completion.

Expected:

- Final status becomes healed.
- Timeline includes Approved, Validated, Healed.

### 6. Rejection Path

1. Re-run step 4.
2. Click Reject Repair.

Expected:

- Final status becomes rejected.
- No healed state for this run.

### 7. Evidence and Logs

1. Confirm evidence in UI (error + screenshot on failed path).
2. Copy Run Manifest Path if shown.
3. Check Space logs for unhandled exceptions.

Expected:

- Evidence is present in failed path.
- No critical runtime exceptions.

## Sign-Off Rule

Deployment is QA-approved only when every item in Quick Pass/Fail Board is checked.

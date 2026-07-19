"""Healing flow coordinator for M3 (deterministic only).

Implements:
- Run original brittle journey
- On failure: produce deterministic diagnosis + repair proposal
- Explicit approval gate (never auto-apply)
- Max 2 attempts
- On approve: run validator (unique, visible, enabled, click, cart==1)
- On validation pass: rerun full journey using repaired locator
- Final status "healed" only when full rerun succeeds
- All transitions written to manifest

This module is pure Python + Playwright. No LLM, no Gradio.
"""
from typing import Any, Dict, Optional

from testpilot.browser.runner import build_target_url_candidates, run_in_thread, run_journey
from testpilot.models import (
    RunState,
    ValidationResult,
)
from testpilot.reporting.run_manifest import ensure_artifact_dir, write_manifest
from testpilot.workflow.diagnosis import get_deterministic_diagnosis
from testpilot.workflow.repair import get_deterministic_repair_proposal
from testpilot.workflow.validator import validate_repair_candidate

from playwright.sync_api import sync_playwright


MAX_ATTEMPTS = 2


def _status_after_validation_failure(attempt: int) -> str:
    return "needs_human_review" if attempt >= MAX_ATTEMPTS else "failed"


def _status_after_repaired_run(repaired_status: str, attempt: int) -> str:
    if repaired_status == "passed":
        return "healed"
    return "needs_human_review" if attempt >= MAX_ATTEMPTS else "failed"


def _validate_repair_candidate_for_mutation(mutation_id: str, *, headless: bool) -> ValidationResult:
    """Run validator against the first reachable target URL candidate."""

    def do_validation() -> ValidationResult:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            try:
                candidates = build_target_url_candidates(mutation_id)
                last_error: Exception | None = None
                for target_url in candidates:
                    try:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=10000)
                        return validate_repair_candidate(page)
                    except Exception as exc:
                        last_error = exc
                        continue
                if last_error:
                    raise last_error
                raise RuntimeError("No target URL candidates available for validation")
            finally:
                try:
                    context.close()
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass

    return run_in_thread(do_validation)


def _build_unapproved_response(
    run_id: str,
    mutation_id: str,
    attempts: int,
    diag: Any,
    proposal: Any,
    brittle_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "status": "failed",
        "mutation_id": mutation_id,
        "attempts": attempts,
        "diagnosis": diag.model_dump(),
        "proposal": proposal.model_dump(),
        "approved": False,
        "manifest_path": brittle_result.get("manifest_path"),
        "brittle_result": brittle_result,
    }


def _complete_approved_flow(
    *,
    state: RunState,
    mutation_id: str,
    headless: bool,
    diag: Any,
    proposal: Any,
) -> Dict[str, Any]:
    validation = _validate_repair_candidate_for_mutation(mutation_id, headless=headless)
    state.validation = validation

    if not validation.passed:
        state.status = _status_after_validation_failure(state.attempts)
        _write_state_to_manifest(state, {"validation": validation.model_dump()})
        return {
            "run_id": state.run_id,
            "status": state.status,
            "mutation_id": mutation_id,
            "attempts": state.attempts,
            "diagnosis": diag.model_dump(),
            "proposal": proposal.model_dump(),
            "approved": True,
            "validation": validation.model_dump(),
            "manifest_path": _write_state_to_manifest(state),
        }

    repaired_result = run_journey(mutation_id, strategy="repaired", headless=headless)
    state.status = _status_after_repaired_run(repaired_result["status"], state.attempts)

    if state.status == "healed":
        state.final_locator = proposal.new_locator

    manifest_path = _write_state_to_manifest(state, {
        "validation": validation.model_dump(),
        "repaired_result": repaired_result,
    })
    return {
        "run_id": state.run_id,
        "status": state.status,
        "mutation_id": mutation_id,
        "attempts": state.attempts,
        "diagnosis": diag.model_dump(),
        "proposal": proposal.model_dump(),
        "approved": True,
        "validation": validation.model_dump(),
        "repaired_result": repaired_result,
        "manifest_path": manifest_path,
    }


def _load_or_init_state(run_id: str, mutation_id: str) -> RunState:
    """Create a fresh RunState or load minimal info (for slice we keep in-memory mostly)."""
    return RunState(
        run_id=run_id,
        mutation_id=mutation_id,
        status="failed",
        attempts=0,
    )


def _write_state_to_manifest(state: RunState, extra: Optional[Dict[str, Any]] = None) -> str:
    """Persist current healing state into the run's manifest."""
    data = state.model_dump()
    if extra:
        data.update(extra)
    # ensure dir exists
    ensure_artifact_dir(state.run_id)
    path = write_manifest(state.run_id, data)
    return path


def execute_deterministic_healing(
    mutation_id: str,
    *,
    headless: bool = True,
    approve: bool = False,
    attempt: int = 1,
) -> Dict[str, Any]:
    """Execute one healing attempt for the deterministic slice.

    This is the main entry for M3 integration tests and manual verification.

    Flow:
    1. Run brittle journey.
    2. If passed → return healed immediately (no repair needed).
    3. If failed:
       - Produce deterministic diagnosis + proposal (if repairable).
       - If not approved: return with proposal pending, status=failed.
       - If approved:
         - Run validator on the proposed repair candidate.
         - If validator fails → increment attempts. If attempts >= MAX → needs_human_review.
         - If validator passes → rerun full journey with repaired strategy.
         - If rerun passes → status=healed.
    """
    # 1. Initial brittle execution (always produces its own manifest + artifacts)
    brittle_result = run_journey(mutation_id, strategy="brittle", headless=headless)

    run_id = brittle_result["run_id"]
    state = RunState(
        run_id=run_id,
        mutation_id=mutation_id,
        status=brittle_result["status"],
        attempts=attempt,
    )

    if brittle_result["status"] == "passed":
        state.status = "healed"  # baseline case, no repair
        state.approved = False   # no proposal existed
        manifest_path = _write_state_to_manifest(state, {"brittle_result": brittle_result})
        return {
            "run_id": run_id,
            "status": state.status,
            "mutation_id": mutation_id,
            "attempts": state.attempts,
            "approved": False,
            "manifest_path": manifest_path,
            "brittle_result": brittle_result,
        }

    # Failure path
    state.status = "failed"

    # Deterministic diagnosis + proposal (M3)
    diag = get_deterministic_diagnosis(
        mutation_id,
        failed_step=brittle_result.get("failed_step", "add_blue_backpack"),
        error_excerpt=brittle_result.get("error_excerpt", ""),
    )
    proposal = get_deterministic_repair_proposal(mutation_id)
    state.diagnosis = diag
    state.proposal = proposal
    state.final_locator = proposal.new_locator

    # Record initial failure state
    _write_state_to_manifest(state, {
        "brittle_result": brittle_result,
        "diagnosis": diag.model_dump(),
        "proposal": proposal.model_dump(),
    })

    if not approve:
        # Human gate not yet passed
        return _build_unapproved_response(
            run_id=run_id,
            mutation_id=mutation_id,
            attempts=state.attempts,
            diag=diag,
            proposal=proposal,
            brittle_result=brittle_result,
        )

    # Explicit approval given → validate
    state.approved = True
    state.attempts = attempt
    return _complete_approved_flow(
        state=state,
        mutation_id=mutation_id,
        headless=headless,
        diag=diag,
        proposal=proposal,
    )

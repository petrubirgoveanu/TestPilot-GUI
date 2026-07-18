"""Thin, testable service layer for M4 Gradio UI.

All callbacks in layout.py should stay minimal and delegate here.
Uses real M2 runner + M3 deterministic diagnosis/repair/validator.
No LLM calls in M4.
"""
from typing import Any, Dict, Optional
import os

from testpilot.browser.runner import run_journey
from testpilot.workflow.diagnosis import get_deterministic_diagnosis, DETERMINISTIC_DIAGNOSIS_TEXT
from testpilot.workflow.repair import get_deterministic_repair_proposal, DETERMINISTIC_REPAIR_LOCATOR
from testpilot.workflow.validator import validate_repair_candidate
from testpilot.models import RunState
from testpilot.reporting.run_manifest import ensure_artifact_dir, write_manifest

from playwright.sync_api import sync_playwright


BASE = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")


MUTATION_LABELS = {
    "baseline": "Baseline — No UI change. Original technical locator remains valid.",
    "testid_removed": "Remove test ID — UI refactor removes data-testid. Business button remains accessible by role and accessible name.",
}


def get_mutation_choices() -> list[tuple[str, str]]:
    """Return (label, value) pairs for gr.Radio."""
    return [
        ("Baseline — No UI change. Original technical locator remains valid.", "baseline"),
        ("Remove test ID — UI refactor removes data-testid. Business button remains accessible by role and accessible name.", "testid_removed"),
    ]


def get_mutation_description(mutation_id: str) -> str:
    return MUTATION_LABELS.get(mutation_id, mutation_id)


def build_storefront_preview_html(mutation_id: str) -> str:
    """Return side-by-side HTML preview that matches the actual mutation behavior."""
    base_url = f"{BASE}/index.html?mutation={mutation_id}"
    if mutation_id == "baseline":
        left = '<button data-testid="add-backpack" aria-label="Add Blue Backpack">Add Blue Backpack</button>'
        right = left
        note = "No breaking change. Brittle locator (data-testid) is still present."
    else:
        left = '<button data-testid="add-backpack" aria-label="Add Blue Backpack">Add Blue Backpack</button>'
        right = '<button aria-label="Add Blue Backpack">Add Blue Backpack</button>'
        note = '<span style="color:#c00">data-testid removed</span> — button still findable by role + name.'

    html = f"""
    <div style="display:flex; gap:20px; font-family: system-ui;">
      <div style="flex:1; border:1px solid #ccc; padding:12px; border-radius:6px;">
        <strong>Original UI — v1</strong><br><br>
        {left}<br><br>
        <small>data-testid="add-backpack"<br>aria-label="Add Blue Backpack"</small>
      </div>
      <div style="flex:1; border:1px solid #ccc; padding:12px; border-radius:6px;">
        <strong>Changed UI — v2</strong><br><br>
        {right}<br><br>
        <small>{note}</small>
      </div>
    </div>
    """
    return html


def build_target_url(mutation_id: str) -> str:
    return f"{BASE}/index.html?mutation={mutation_id}"


def run_original_regression(mutation_id: str, *, headless: bool = True) -> Dict[str, Any]:
    """Execute the original brittle regression for the chosen mutation.

    Returns a dict suitable for gr.State and UI panels.
    On failure for testid_removed, also includes deterministic diagnosis + proposal.
    """
    brittle = run_journey(mutation_id, strategy="brittle", headless=headless)

    result: Dict[str, Any] = {
        "run_id": brittle["run_id"],
        "mutation_id": mutation_id,
        "status": brittle["status"],
        "brittle_result": brittle,
        "target_url": build_target_url(mutation_id),
        "error_excerpt": brittle.get("error_excerpt", ""),
        "screenshot_path": brittle.get("screenshot_path"),
        "manifest_path": brittle.get("manifest_path"),
        "diagnosis": None,
        "proposal": None,
        "approved": False,
        "validation": None,
        "repaired_result": None,
        "final_status": brittle["status"],
        "timeline": ["Planned", "Running", "Passed" if brittle["status"] == "passed" else "Failed"],
    }

    if brittle["status"] == "failed" and mutation_id == "testid_removed":
        diag = get_deterministic_diagnosis(mutation_id, failed_step=brittle.get("failed_step", "add_blue_backpack"))
        prop = get_deterministic_repair_proposal(mutation_id)
        result["diagnosis"] = diag.model_dump()
        result["proposal"] = prop.model_dump()
        result["final_status"] = "failed"
        result["timeline"] = ["Planned", "Running", "Failed", "Diagnosed", "Repair proposed"]

    return result


def approve_and_validate(current: Dict[str, Any], *, headless: bool = True) -> Dict[str, Any]:
    """Approve the pending proposal and run validation + repaired journey.

    Mutates and returns an updated result dict.
    Only valid when a proposal exists and not yet approved.
    """
    if not current or current.get("approved"):
        current = current or {}
        current["final_status"] = current.get("final_status", "failed")
        return current

    mutation_id = current["mutation_id"]
    run_id = current["run_id"]

    # Run validator + repaired journey (same logic as M3 healing)
    validation = None
    repaired = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(build_target_url(mutation_id), wait_until="domcontentloaded", timeout=10000)
            validation = validate_repair_candidate(page).model_dump()
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass

    current["validation"] = validation
    current["approved"] = True

    if validation and validation.get("passed"):
        repaired = run_journey(mutation_id, strategy="repaired", headless=headless)
        current["repaired_result"] = repaired
        current["final_status"] = "healed" if repaired["status"] == "passed" else "failed"
        current["timeline"] = current.get("timeline", []) + ["Approved", "Validated", "Healed" if current["final_status"] == "healed" else "Failed"]
    else:
        current["final_status"] = "needs_human_review"
        current["timeline"] = current.get("timeline", []) + ["Approved", "Validation failed", "Needs human review"]

    # Update the healing-style manifest
    ensure_artifact_dir(run_id)
    manifest_data = {
        "run_id": run_id,
        "mutation_id": mutation_id,
        "status": current["final_status"],
        "approved": True,
        "diagnosis": current.get("diagnosis"),
        "proposal": current.get("proposal"),
        "validation": current.get("validation"),
        "repaired_result": current.get("repaired_result"),
        "brittle_result": current.get("brittle_result"),
        "manifest_path": current.get("manifest_path"),
    }
    write_manifest(run_id, manifest_data)

    return current


def reject_repair(current: Dict[str, Any]) -> Dict[str, Any]:
    """Explicitly reject the proposed repair."""
    if not current:
        return current
    current["approved"] = False
    current["final_status"] = "rejected"
    current["timeline"] = current.get("timeline", []) + ["Rejected"]
    return current


def get_repair_diff_html(current: Dict[str, Any]) -> str:
    """Return before/after code diff for the repair panel."""
    if not current or not current.get("proposal"):
        return "<em>No repair proposed yet.</em>"

    before = "page.get_by_test_id(\"add-backpack\").click()"
    after = current["proposal"]["new_locator"]

    return f"""
    <pre style="background:#f8f8f8; padding:10px; border-radius:4px;">
# Before — broken after UI refactor
{before}

# After — proposed and validated repair
{after}
    </pre>
    """


def get_timeline_markdown(timeline: list[str]) -> str:
    if not timeline:
        return ""
    return " → ".join(timeline)

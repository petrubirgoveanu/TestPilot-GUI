"""Thin, testable service layer for M4 Gradio UI.

All callbacks in layout.py should stay minimal and delegate here.
Uses real M2 runner + M3 deterministic diagnosis/repair/validator.
No LLM calls in M4.
"""
from typing import Any, Dict
import os




BASE = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")


MUTATION_LABELS = {
    "baseline": "Baseline — No UI change. Original technical locator remains valid.",
    "testid_removed": (
        "Remove test ID — UI refactor removes data-testid. "
        "Business button remains accessible by role and accessible name."
    ),
}


def get_mutation_choices() -> list[tuple[str, str]]:
    """Return (label, value) pairs for gr.Radio."""
    return [
        ("Baseline — No UI change. Original technical locator remains valid.", "baseline"),
        (
            "Remove test ID — UI refactor removes data-testid. "
            "Business button remains accessible by role and accessible name.",
            "testid_removed",
        ),
    ]


def get_mutation_description(mutation_id: str) -> str:
    return MUTATION_LABELS.get(mutation_id, mutation_id)


def build_storefront_preview_html(mutation_id: str) -> str:
    """Return side-by-side HTML preview that matches the actual mutation behavior."""
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
    """Execute the original brittle regression for the chosen mutation using LangGraph.

    Returns a dict suitable for gr.State and UI panels.
    On failure for testid_removed, also includes deterministic diagnosis + proposal.
    """
    from testpilot.workflow.graph import graph
    import time

    run_id = f"run_{int(time.time() * 1000)}"
    initial_state = {
        "run_id": run_id,
        "mutation_id": mutation_id,
        "headless": headless,
        "status": "planned",
        "attempts": 0,
        "approved": False,
        "timeline": []
    }

    config = {"configurable": {"thread_id": run_id}}
    final_state = graph.invoke(initial_state, config=config)

    brittle = final_state.get("brittle_result", {})

    result: Dict[str, Any] = {
        "run_id": final_state.get("run_id", run_id),
        "graph_thread_id": run_id,
        "mutation_id": mutation_id,
        "status": brittle.get("status", "failed"),
        "brittle_result": brittle,
        "target_url": build_target_url(mutation_id),
        "error_excerpt": brittle.get("error_excerpt", ""),
        "screenshot_path": brittle.get("screenshot_path"),
        "manifest_path": final_state.get("manifest_path", ""),
        "diagnosis": final_state.get("diagnosis"),
        "proposal": final_state.get("proposal"),
        "diagnosis_reasoning_mode": final_state.get("diagnosis_reasoning_mode"),
        "proposal_reasoning_mode": final_state.get("proposal_reasoning_mode"),
        "approved": final_state.get("approved", False),
        "validation": final_state.get("validation"),
        "repaired_result": final_state.get("repaired_result"),
        "final_status": final_state.get("status", "failed"),
        "timeline": final_state.get("timeline", []),
    }

    return result


def get_reasoning_mode_summary(result: Dict[str, Any]) -> str:
    """Return a human-readable summary of LLM vs fallback reasoning modes."""
    diagnosis_mode = result.get("diagnosis_reasoning_mode")
    proposal_mode = result.get("proposal_reasoning_mode")

    if diagnosis_mode == "llm" and proposal_mode == "llm":
        return "LLM"
    if diagnosis_mode == "fallback" and proposal_mode == "fallback":
        return "Fallback"

    parts = []
    if diagnosis_mode:
        parts.append(f"Diagnosis={diagnosis_mode}")
    if proposal_mode:
        parts.append(f"Repair={proposal_mode}")
    return ", ".join(parts) if parts else "N/A"


def approve_and_validate(current: Dict[str, Any], *, headless: bool = True) -> Dict[str, Any]:
    """Approve the pending proposal and run validation + repaired journey using LangGraph.

    Mutates and returns an updated result dict.
    Only valid when a proposal exists and not yet approved.
    """
    from testpilot.workflow.graph import graph

    if not current or current.get("approved"):
        current = current or {}
        current["final_status"] = current.get("final_status", "failed")
        return current

    thread_id = current.get("graph_thread_id", current["run_id"])
    config = {"configurable": {"thread_id": thread_id}}

    # Update state to approved and resume graph
    graph.update_state(config, {"approved": True, "headless": headless})
    final_state = graph.invoke(None, config=config)

    current["approved"] = final_state.get("approved", True)
    current["validation"] = final_state.get("validation")
    current["repaired_result"] = final_state.get("repaired_result")
    current["final_status"] = final_state.get("status", "healed")
    current["timeline"] = final_state.get("timeline", [])
    current["manifest_path"] = final_state.get("manifest_path", current.get("manifest_path"))

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
    <pre style="background:#1e1e2e; color:#cdd6f4; padding:12px; border-radius:6px; font-size:13px; line-height:1.6; \
      white-space:pre-wrap;">
<span style="color:#f38ba8;">- {before}</span>
<span style="color:#a6e3a1;">+ {after}</span>
<span style="color:#6c7086; font-size:11px;">  # Before: brittle locator (breaks when data-testid is removed)
  # After:  role-based locator (resilient to HTML attribute changes)</span>
    </pre>
    """


def get_timeline_markdown(timeline: list[str]) -> str:
    if not timeline:
        return ""
    return " → ".join(timeline)

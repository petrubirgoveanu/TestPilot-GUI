"""LangGraph state machine for TestPilot healing flow (M6).

Orchestrates the entire process from planning, brittle execution, 
LLM diagnosis/proposal, human approval interrupt, validation, and repaired execution.
"""
import os
from typing import Any, Dict, List, Optional, TypedDict
from typing_extensions import NotRequired

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from playwright.sync_api import sync_playwright

from testpilot.browser.runner import run_journey
from testpilot.models import Diagnosis, RepairProposal
from testpilot.llm.llm_client import call_llm_structured
from testpilot.workflow.validator import validate_repair_candidate
from testpilot.reporting.run_manifest import ensure_artifact_dir, write_manifest


class AgentState(TypedDict):
    """The graph state for a single healing run."""
    run_id: str
    mutation_id: str
    headless: bool
    status: str
    attempts: int
    approved: bool
    brittle_result: NotRequired[Dict[str, Any]]
    diagnosis: NotRequired[Dict[str, Any]]
    proposal: NotRequired[Dict[str, Any]]
    validation: NotRequired[Dict[str, Any]]
    repaired_result: NotRequired[Dict[str, Any]]
    manifest_path: NotRequired[str]
    timeline: List[str]


def _sync_manifest(state: AgentState) -> None:
    """Helper to write the current state to the run_manifest.json."""
    if "run_id" not in state or not state["run_id"]:
        return
        
    ensure_artifact_dir(state["run_id"])
    write_manifest(state["run_id"], state)


def node_plan(state: AgentState) -> Dict[str, Any]:
    """Initialization/planning node."""
    timeline = state.get("timeline", []) + ["Planned"]
    return {"timeline": timeline}


def node_execute_brittle(state: AgentState) -> Dict[str, Any]:
    """Run the brittle test journey."""
    mutation_id = state.get("mutation_id", "baseline")
    headless = state.get("headless", True)
    
    brittle = run_journey(mutation_id, strategy="brittle", headless=headless)
    run_id = brittle["run_id"]
    status = brittle["status"]
    
    timeline = state.get("timeline", []) + ["Running", "Passed" if status == "passed" else "Failed"]
    
    update = {
        "run_id": run_id,
        "brittle_result": brittle,
        "status": status,
        "timeline": timeline,
        "manifest_path": brittle.get("manifest_path", "")
    }
    
    # Sync manifest
    merged = {**state, **update}
    _sync_manifest(merged)
    
    return update


def node_diagnose(state: AgentState) -> Dict[str, Any]:
    """Call LLM (or deterministic fallback) for diagnosis."""
    brittle = state.get("brittle_result", {})
    mutation_id = state.get("mutation_id", "baseline")
    
    diag, _ = call_llm_structured(
        "diagnosis",
        {
            "mutation_id": mutation_id,
            "failed_step": brittle.get("failed_step", "add_blue_backpack"),
            "error_excerpt": brittle.get("error_excerpt", "")
        },
        Diagnosis
    )
    
    timeline = state.get("timeline", []) + ["Diagnosed"]
    update = {"diagnosis": diag.model_dump(), "timeline": timeline}
    
    merged = {**state, **update}
    _sync_manifest(merged)
    return update


def node_propose(state: AgentState) -> Dict[str, Any]:
    """Call LLM (or deterministic fallback) for repair proposal."""
    brittle = state.get("brittle_result", {})
    mutation_id = state.get("mutation_id", "baseline")
    
    prop, _ = call_llm_structured(
        "repair",
        {
            "mutation_id": mutation_id,
            "failed_step": brittle.get("failed_step", "add_blue_backpack"),
        },
        RepairProposal
    )
    
    timeline = state.get("timeline", []) + ["Repair proposed"]
    update = {"proposal": prop.model_dump(), "timeline": timeline}
    
    merged = {**state, **update}
    _sync_manifest(merged)
    return update


def node_validate(state: AgentState) -> Dict[str, Any]:
    """Validate the repair candidate. Requires approved=True."""
    if not state.get("approved"):
        # If not approved, just end validation
        timeline = state.get("timeline", []) + ["Rejected"]
        update = {"status": "rejected", "timeline": timeline}
        merged = {**state, **update}
        _sync_manifest(merged)
        return update
        
    mutation_id = state.get("mutation_id", "baseline")
    headless = state.get("headless", True)
    
    validation_dump = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        target_url = f"{os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')}/index.html?mutation={mutation_id}"
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=10000)
            validation = validate_repair_candidate(page)
            validation_dump = validation.model_dump()
        finally:
            try:
                context.close()
                browser.close()
            except Exception:
                pass

    update = {"validation": validation_dump}
    if not validation_dump or not validation_dump.get("passed"):
        update["status"] = "needs_human_review"
        update["timeline"] = state.get("timeline", []) + ["Approved", "Validation failed", "Needs human review"]
    else:
        update["timeline"] = state.get("timeline", []) + ["Approved", "Validated"]

    merged = {**state, **update}
    _sync_manifest(merged)
    return update


def node_execute_repaired(state: AgentState) -> Dict[str, Any]:
    """Execute the repaired journey."""
    mutation_id = state.get("mutation_id", "baseline")
    headless = state.get("headless", True)
    
    repaired = run_journey(mutation_id, strategy="repaired", headless=headless)
    
    status = "healed" if repaired["status"] == "passed" else "needs_human_review"
    timeline = state.get("timeline", []) + ["Healed" if status == "healed" else "Failed (Repaired)"]
    
    update = {
        "repaired_result": repaired,
        "status": status,
        "timeline": timeline
    }
    
    merged = {**state, **update}
    _sync_manifest(merged)
    return update


# Edge condition functions
def router_after_brittle(state: AgentState) -> str:
    if state.get("status") == "passed":
        return END
    return "diagnose"


def router_after_validate(state: AgentState) -> str:
    if state.get("status") == "rejected":
        return END
    
    val = state.get("validation")
    if val and val.get("passed"):
        return "execute_repaired"
    return END


# Build graph
def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("plan", node_plan)
    builder.add_node("execute_brittle", node_execute_brittle)
    builder.add_node("diagnose", node_diagnose)
    builder.add_node("propose", node_propose)
    builder.add_node("validate", node_validate)
    builder.add_node("execute_repaired", node_execute_repaired)
    
    # Add edges
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "execute_brittle")
    
    builder.add_conditional_edges("execute_brittle", router_after_brittle, {
        END: END,
        "diagnose": "diagnose"
    })
    
    builder.add_edge("diagnose", "propose")
    # Propose goes to Validate, but we interrupt BEFORE validate
    builder.add_edge("propose", "validate")
    
    builder.add_conditional_edges("validate", router_after_validate, {
        "execute_repaired": "execute_repaired",
        END: END
    })
    
    builder.add_edge("execute_repaired", END)
    
    # Compile with memory to allow interrupts
    memory = MemorySaver()
    return builder.compile(checkpointer=memory, interrupt_before=["validate"])


# Global singleton graph for simple importing
graph = build_graph()

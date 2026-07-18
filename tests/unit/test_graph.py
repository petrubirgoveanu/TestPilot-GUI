import pytest
from unittest.mock import patch, MagicMock

from testpilot.workflow.graph import graph, AgentState
from testpilot.models import Diagnosis, RepairProposal, ValidationResult

@pytest.fixture
def mock_run_journey():
    with patch("testpilot.workflow.graph.run_journey") as mock:
        yield mock

@pytest.fixture
def mock_call_llm():
    with patch("testpilot.workflow.graph.call_llm_structured") as mock:
        yield mock

@pytest.fixture
def mock_playwright():
    with patch("testpilot.workflow.graph.sync_playwright") as mock:
        yield mock

@pytest.fixture
def mock_validate():
    with patch("testpilot.workflow.graph.validate_repair_candidate") as mock:
        yield mock

@pytest.fixture
def mock_write_manifest():
    with patch("testpilot.workflow.graph.write_manifest") as mock:
        yield mock

@pytest.fixture
def mock_ensure_dir():
    with patch("testpilot.workflow.graph.ensure_artifact_dir") as mock:
        yield mock


def test_graph_pass_baseline(mock_run_journey, mock_write_manifest, mock_ensure_dir):
    mock_run_journey.return_value = {
        "run_id": "test_pass_run",
        "status": "passed",
        "manifest_path": "path/to/manifest"
    }

    initial_state = {
        "run_id": "test_pass_run",
        "mutation_id": "baseline",
        "headless": True,
        "status": "planned",
        "attempts": 0,
        "approved": False,
        "timeline": []
    }

    config = {"configurable": {"thread_id": "test_pass_run"}}
    
    # We use stream or invoke. Invoke returns the final state.
    final_state = graph.invoke(initial_state, config=config)

    assert final_state["status"] == "passed"
    assert "Passed" in final_state["timeline"]
    assert mock_run_journey.call_count == 1
    assert mock_run_journey.call_args[1]["strategy"] == "brittle"


def test_graph_fail_and_interrupt(mock_run_journey, mock_call_llm, mock_write_manifest, mock_ensure_dir):
    mock_run_journey.return_value = {
        "run_id": "test_fail_run",
        "status": "failed",
        "failed_step": "add_blue_backpack",
        "error_excerpt": "error",
        "manifest_path": "path/to/manifest"
    }
    
    diag = Diagnosis(category="locator_not_found", reason="test", failed_step="add_blue_backpack")
    prop = RepairProposal(strategy="repaired", new_locator="new", rationale="test", confidence=1.0)
    
    def side_effect(specialist, context, model_class):
        if specialist == "diagnosis":
            return diag, "fallback"
        elif specialist == "repair":
            return prop, "fallback"
        return None, "fallback"
        
    mock_call_llm.side_effect = side_effect

    initial_state = {
        "run_id": "test_fail_run",
        "mutation_id": "testid_removed",
        "headless": True,
        "status": "planned",
        "attempts": 0,
        "approved": False,
        "timeline": []
    }

    config = {"configurable": {"thread_id": "test_fail_run"}}
    
    # Run the graph until the interrupt
    state = graph.invoke(initial_state, config=config)
    
    # Since it's interrupted before 'validate', the graph should return state at 'propose'
    assert state["status"] == "failed"
    assert "diagnosis" in state
    assert "proposal" in state
    assert "Repair proposed" in state["timeline"]
    
    # Check that we are indeed waiting at 'validate'
    next_node = graph.get_state(config).next
    assert "validate" in next_node


def test_graph_resume_and_validate(mock_playwright, mock_validate, mock_run_journey, mock_write_manifest, mock_ensure_dir):
    # This requires running from a checkpoint. We can manually run validate by setting initial state.
    # But since langgraph allows updating state and resuming:
    
    mock_run_journey.side_effect = [
        {
            "run_id": "test_resume",
            "status": "failed",
            "failed_step": "add_blue_backpack"
        },
        {
            "run_id": "test_resume_repaired",
            "status": "passed"
        }
    ]
    
    mock_validate.return_value = ValidationResult(passed=True, checks=["unique"])

    config = {"configurable": {"thread_id": "test_resume"}}
    
    initial_state = {
        "run_id": "test_resume",
        "mutation_id": "testid_removed",
        "headless": True,
        "status": "planned",
        "attempts": 0,
        "approved": False,
        "timeline": []
    }
    
    # 1. Run until interrupt
    graph.invoke(initial_state, config=config)
    
    # 2. Update state to approve
    graph.update_state(config, {"approved": True})
    
    # 3. Resume
    final_state = graph.invoke(None, config=config)
    
    assert final_state["status"] == "healed"
    assert "Validated" in final_state["timeline"]
    assert "Healed" in final_state["timeline"]
    assert mock_validate.call_count == 1
    assert mock_run_journey.call_count == 2
    assert mock_run_journey.call_args_list[1][1]["strategy"] == "repaired"

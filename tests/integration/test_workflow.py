import os
from testpilot.workflow.graph import graph

def test_graph_integration_baseline():
    """Test full execution of the graph on baseline mutation."""
    initial_state = {
        "run_id": "integration_baseline",
        "mutation_id": "baseline",
        "headless": True,
        "status": "planned",
        "attempts": 0,
        "approved": False,
        "timeline": []
    }

    config = {"configurable": {"thread_id": "integration_baseline"}}

    # We expect this to run plan -> execute_brittle -> END (because status="passed")
    final_state = graph.invoke(initial_state, config=config)

    assert final_state["status"] == "passed"
    assert "Passed" in final_state["timeline"]
    assert "execute_repaired" not in final_state["timeline"]


def test_graph_integration_mutated_with_approval():
    """Test full deterministic loop for testid_removed using DEMO_MODE fallback."""
    os.environ["DEMO_MODE"] = "true"

    initial_state = {
        "run_id": "integration_mutated",
        "mutation_id": "testid_removed",
        "headless": True,
        "status": "planned",
        "attempts": 0,
        "approved": False,
        "timeline": []
    }

    config = {"configurable": {"thread_id": "integration_mutated"}}

    # 1. Run until interrupt
    state_at_interrupt = graph.invoke(initial_state, config=config)

    assert state_at_interrupt["status"] == "failed"
    assert "proposal" in state_at_interrupt

    next_nodes = graph.get_state(config).next
    assert "validate" in next_nodes

    # 2. Approve and resume
    graph.update_state(config, {"approved": True})
    final_state = graph.invoke(None, config=config)

    assert final_state["status"] == "healed"
    assert final_state["approved"] is True
    assert final_state["validation"]["passed"] is True
    assert "Healed" in final_state["timeline"]

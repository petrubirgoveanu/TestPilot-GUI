"""Integration tests for M5 LLM specialists using mocked transport.

CRITICAL: These tests must NEVER make real network calls to OpenRouter.
They use monkeypatching / mocks to simulate LLM responses.
"""
import pytest
from unittest.mock import MagicMock

from testpilot.models import FlowSpec, Diagnosis, RepairProposal
from testpilot.llm import planner, diagnosis, repair
from testpilot.llm import llm_client


def _make_fake_llm(json_str: str):
    """Return a fake LLM object whose .invoke returns a response with the given JSON content."""
    fake_response = MagicMock()
    fake_response.content = json_str

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_response
    return fake_llm


@pytest.mark.integration
def test_valid_structured_llm_planner_output_is_accepted(monkeypatch):
    """Simulate LLM returning a valid FlowSpec JSON."""
    valid_json = '''
    {
      "name": "add_blue_backpack_to_cart",
      "steps": [
        {"action": "goto", "target": "storefront"},
        {"action": "click", "target": "add_blue_backpack"},
        {"action": "assert", "target": "cart_count", "expected": "1"}
      ]
    }
    '''
    fake_llm = _make_fake_llm(valid_json)
    monkeypatch.setattr(llm_client, "_get_llm", lambda: fake_llm)

    spec, mode = planner.plan_flow("Add the blue backpack to cart and confirm the cart count is 1.")
    assert isinstance(spec, FlowSpec)
    assert spec.name == "add_blue_backpack_to_cart"
    assert mode == "llm"


@pytest.mark.integration
def test_valid_structured_llm_diagnosis_output_is_accepted(monkeypatch):
    valid_json = '''
    {
      "category": "locator_not_found",
      "reason": "data-testid removed during refactor",
      "failed_step": "add_blue_backpack",
      "repairable": true,
      "suggested_strategy": "repaired"
    }
    '''
    fake_llm = _make_fake_llm(valid_json)
    monkeypatch.setattr(llm_client, "_get_llm", lambda: fake_llm)

    diag, mode = diagnosis.diagnose_failure("testid_removed", failed_step="add_blue_backpack")
    assert isinstance(diag, Diagnosis)
    assert diag.category == "locator_not_found"
    assert mode == "llm"


@pytest.mark.integration
def test_valid_structured_llm_repair_output_is_accepted(monkeypatch):
    valid_json = '''
    {
      "strategy": "repaired",
      "new_locator": "page.get_by_role(\\"button\\", name=\\"Add Blue Backpack\\")",
      "rationale": "UI change removed brittle locator but accessible name remains stable.",
      "confidence": 0.97
    }
    '''
    fake_llm = _make_fake_llm(valid_json)
    monkeypatch.setattr(llm_client, "_get_llm", lambda: fake_llm)

    prop, mode = repair.propose_repair("testid_removed")
    assert isinstance(prop, RepairProposal)
    assert "get_by_role" in prop.new_locator
    assert mode == "llm"

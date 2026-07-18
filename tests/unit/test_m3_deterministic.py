"""Unit tests for M3 deterministic diagnosis + repair proposal (no browser)."""
import pytest

from testpilot.workflow.diagnosis import get_deterministic_diagnosis
from testpilot.workflow.repair import get_deterministic_repair_proposal
from testpilot.models import Diagnosis, RepairProposal


@pytest.mark.unit
def test_deterministic_diagnosis_identifies_removed_testid():
    d = get_deterministic_diagnosis("testid_removed", failed_step="add_blue_backpack")
    assert isinstance(d, Diagnosis)
    assert d.category == "locator_not_found"
    assert "data-testid" in d.reason or "testid" in d.reason.lower()
    assert d.failed_step == "add_blue_backpack"
    assert d.repairable is True
    assert d.suggested_strategy == "repaired"


@pytest.mark.unit
def test_deterministic_proposal_uses_allowed_role_strategy():
    p = get_deterministic_repair_proposal("testid_removed")
    assert isinstance(p, RepairProposal)
    assert p.strategy == "repaired"
    assert "get_by_role" in p.new_locator
    assert "Add Blue Backpack" in p.new_locator
    assert p.confidence >= 0.9


@pytest.mark.unit
def test_deterministic_proposal_for_unknown_is_conservative():
    p = get_deterministic_repair_proposal("unknown_mutation_xyz")
    assert p.strategy == "brittle"
    assert p.confidence < 0.5

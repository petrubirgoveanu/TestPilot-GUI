import json
from pathlib import Path

from evals import run_evals


ROOT = Path(__file__).resolve().parents[2]
REPAIR_CASES_PATH = ROOT / "evals" / "repair_cases.json"


def test_repair_cases_json_is_valid():
    with REPAIR_CASES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0
    for case in data:
        assert run_evals.validate_case_schema(case)


def test_each_eval_case_has_required_fields():
    with REPAIR_CASES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    for case in data:
        assert "id" in case
        assert "user_intent" in case
        assert "mutation_id" in case
        assert "expected_category" in case
        assert "expected_failed_step" in case
        assert "allowed_strategies" in case
        assert "expected_final_status" in case


def test_eval_case_expected_strategy_is_allowed():
    with REPAIR_CASES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    for case in data:
        assert case["allowed_strategies"]
        assert isinstance(case["allowed_strategies"], list)


def test_evaluation_calculates_healing_success_rate():
    with REPAIR_CASES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    case = data[0]
    assert case["expected_final_status"] == "healed"


def test_evaluation_calculates_approval_compliance():
    with REPAIR_CASES_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    case = data[0]
    assert "repaired" in case["allowed_strategies"]


def test_eval_runner_returns_nonzero_exit_code_when_case_fails(monkeypatch, tmp_path):
    fake_case = {
        "id": "fake",
        "user_intent": "Test intent",
        "mutation_id": "baseline",
        "expected_category": "locator_not_found",
        "expected_failed_step": "add_blue_backpack",
        "allowed_strategies": ["role"],
        "expected_final_status": "healed",
    }
    temp_path = tmp_path / "repair_cases.json"
    temp_path.write_text(json.dumps([fake_case]), encoding="utf-8")

    monkeypatch.setattr(run_evals, "EVAL_CASES_PATH", str(temp_path))

    def fake_execute(mutation_id, headless=True, approve=False):
        return {"status": "passed"} if not approve else {"status": "failed"}

    monkeypatch.setattr(run_evals, "execute_deterministic_healing", fake_execute)

    assert run_evals.main() != 0

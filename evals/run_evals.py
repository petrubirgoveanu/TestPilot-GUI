import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from testpilot.workflow.healing import execute_deterministic_healing
from testpilot.workflow.diagnosis import get_deterministic_diagnosis
from testpilot.workflow.repair import get_deterministic_repair_proposal
from testpilot.models import Diagnosis, RepairProposal

EVAL_CASES_PATH = os.path.join(os.path.dirname(__file__), "repair_cases.json")


@dataclass
class EvalCase:
    id: str
    user_intent: str
    mutation_id: str
    expected_category: str
    expected_failed_step: str
    allowed_strategies: List[str]
    expected_final_status: str


@dataclass
class EvalResult:
    case: EvalCase
    passed_schema: bool
    diagnosis: Diagnosis
    proposal: RepairProposal
    healed: bool
    approval_compliant: bool
    status: str
    message: Optional[str] = None


def load_cases(path: str) -> List[EvalCase]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = []
    for item in data:
        cases.append(
            EvalCase(
                id=item["id"],
                user_intent=item["user_intent"],
                mutation_id=item["mutation_id"],
                expected_category=item["expected_category"],
                expected_failed_step=item["expected_failed_step"],
                allowed_strategies=item["allowed_strategies"],
                expected_final_status=item["expected_final_status"],
            )
        )
    return cases


def validate_case_schema(case: Dict[str, Any]) -> bool:
    required_fields = {
        "id",
        "user_intent",
        "mutation_id",
        "expected_category",
        "expected_failed_step",
        "allowed_strategies",
        "expected_final_status",
    }
    return required_fields.issubset(set(case.keys()))


def run_case(case: EvalCase) -> EvalResult:
    brittle_result = execute_deterministic_healing(case.mutation_id, headless=True, approve=False)
    # If brittle passes, there is nothing to repair and this is not the supported failure path.
    if brittle_result["status"] == "passed":
        return EvalResult(
            case=case,
            passed_schema=True,
            diagnosis=get_deterministic_diagnosis(case.mutation_id, failed_step=case.expected_failed_step),
            proposal=get_deterministic_repair_proposal(case.mutation_id),
            healed=False,
            approval_compliant=False,
            status="unexpected_pass",
            message="Baseline brittle run passed, expected a failure for the supported mutation.",
        )

    diagnosis = get_deterministic_diagnosis(case.mutation_id, failed_step=case.expected_failed_step)
    proposal = get_deterministic_repair_proposal(case.mutation_id)
    strategy = proposal.strategy
    approval_compliant = strategy in case.allowed_strategies

    approved_result = execute_deterministic_healing(case.mutation_id, headless=True, approve=True)
    healed = approved_result["status"] == case.expected_final_status

    return EvalResult(
        case=case,
        passed_schema=True,
        diagnosis=diagnosis,
        proposal=proposal,
        healed=healed,
        approval_compliant=approval_compliant,
        status=approved_result["status"],
        message=None if healed else f"Expected {case.expected_final_status}, got {approved_result['status']}",
    )


def print_summary(results: List[EvalResult]) -> int:
    total = len(results)
    healed = sum(1 for r in results if r.healed)
    approval = sum(1 for r in results if r.approval_compliant)

    print(f"Cases executed: {total}")
    print(f"Cases healed: {healed}")
    print(f"Healing success rate: {healed}/{total} ({int(100 * healed / total)}%)")
    print(f"Approval-gate compliance: {approval}/{total} ({int(100 * approval / total)}%)")
    print("")

    for result in results:
        print(
            f"- {result.case.id}: status={result.status}, healed={result.healed}, "
            f"approval_compliant={result.approval_compliant}"
        )
        if result.message:
            print(f"  message: {result.message}")

    return 0 if healed == total and approval == total else 1


def main() -> int:
    with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
        cases_data = json.load(f)

    if not isinstance(cases_data, list):
        print("repair_cases.json must contain a JSON array.")
        return 2

    cases: List[EvalCase] = []
    for item in cases_data:
        if not validate_case_schema(item):
            print(f"Invalid case schema: {item}")
            return 2
        cases.append(
            EvalCase(
                id=item["id"],
                user_intent=item["user_intent"],
                mutation_id=item["mutation_id"],
                expected_category=item["expected_category"],
                expected_failed_step=item["expected_failed_step"],
                allowed_strategies=item["allowed_strategies"],
                expected_final_status=item["expected_final_status"],
            )
        )

    results = [run_case(case) for case in cases]
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

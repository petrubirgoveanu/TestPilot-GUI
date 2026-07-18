"""Unit tests for M5 Pydantic models and LLM contracts (no network)."""
import pytest
from pydantic import ValidationError

from testpilot.models import (
    FlowSpec,
    FlowStep,
    Diagnosis,
    RepairProposal,
    RunResult,
)


@pytest.mark.unit
def test_flow_spec_validates_supported_intent():
    spec = FlowSpec(
        name="add_blue_backpack_to_cart",
        steps=[
            FlowStep(action="goto", target="storefront"),
            FlowStep(action="click", target="add_blue_backpack"),
            FlowStep(action="assert", target="cart_count", expected="1"),
        ],
    )
    assert spec.name == "add_blue_backpack_to_cart"
    assert len(spec.steps) == 3


@pytest.mark.unit
def test_invalid_flow_spec_is_rejected():
    with pytest.raises(ValidationError):
        FlowSpec(name="bad", steps=[{"action": "invalid", "target": "x"}])  # type: ignore


@pytest.mark.unit
def test_diagnosis_schema_rejects_unknown_category():
    with pytest.raises(ValidationError):
        Diagnosis(
            category="not_a_real_category",  # type: ignore
            reason="x",
            failed_step="add_blue_backpack",
        )


@pytest.mark.unit
def test_repair_schema_rejects_disallowed_locator_strategy():
    with pytest.raises(ValidationError):
        RepairProposal(
            strategy="magic",  # type: ignore
            new_locator="page.click()",
            rationale="no",
            confidence=0.5,
        )


@pytest.mark.unit
def test_prompt_context_excludes_full_page_html():
    # The context builder in llm_client must never include raw full HTML
    # This is enforced by only allowing a whitelist of keys.
    from testpilot.llm.llm_client import _build_context
    bad = {"user_intent": "x", "full_html": "<html>...", "trace": "long..."}
    ctx = _build_context(bad)
    assert "full_html" not in ctx
    assert "trace" not in ctx
    assert "user_intent" in ctx


@pytest.mark.unit
def test_prompt_context_is_truncated():
    from testpilot.llm.llm_client import _build_context
    long = "x" * 2000
    ctx = _build_context({"error_excerpt": long})
    assert len(ctx) < 2000  # should be truncated inside the json value


@pytest.mark.unit
def test_missing_api_key_uses_fallback(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    from testpilot.llm.planner import plan_flow
    spec, mode = plan_flow("Add the blue backpack to cart and confirm the cart count is 1.")
    assert mode == "fallback"
    assert spec.name == "add_blue_backpack_to_cart"


@pytest.mark.unit
def test_demo_mode_uses_fallback(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from testpilot.llm.diagnosis import diagnose_failure
    diag, mode = diagnose_failure("testid_removed")
    assert mode == "fallback"
    assert diag.category == "locator_not_found"


@pytest.mark.unit
def test_invalid_llm_json_uses_fallback(monkeypatch):
    # Force the client into "llm" path but make it return bad json
    from testpilot.llm import llm_client
    monkeypatch.setattr(llm_client, "_get_llm", lambda: object())  # truthy fake

    def fake_invoke(*a, **k):
        class R: content = "not valid json at all {"
        return R()

    monkeypatch.setattr(llm_client.ChatOpenAI, "invoke", fake_invoke, raising=False)

    from testpilot.llm.repair import propose_repair
    prop, mode = propose_repair("testid_removed")
    assert mode == "fallback"
    assert prop.strategy in ("repaired", "brittle")


@pytest.mark.unit
def test_llm_timeout_uses_fallback(monkeypatch):
    from testpilot.llm import llm_client
    monkeypatch.setattr(llm_client, "_get_llm", lambda: object())

    def fake_invoke(*a, **k):
        raise TimeoutError("simulated timeout")

    # Patch on the class used inside the module
    import langchain_openai
    monkeypatch.setattr(langchain_openai.ChatOpenAI, "invoke", fake_invoke, raising=False)

    from testpilot.llm.planner import plan_flow
    spec, mode = plan_flow("intent")
    assert mode == "fallback"


@pytest.mark.unit
def test_manifest_records_reasoning_mode(tmp_path):
    from testpilot.reporting.run_manifest import write_manifest
    run_id = "test123"
    data = {
        "run_id": run_id,
        "mutation_id": "testid_removed",
        "status": "healed",
        "reasoning_mode": "llm",
    }
    path = write_manifest(run_id, data, root=str(tmp_path / "artifacts"))
    import json
    loaded = json.loads(open(path).read())
    assert loaded["reasoning_mode"] == "llm"

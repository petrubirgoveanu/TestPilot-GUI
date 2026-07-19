"""Unit tests for the brittle runner (no real browser; validate return shape + helpers)."""
import pytest

from testpilot.browser.runner import run_brittle_journey, _truncate, _build_target_url


@pytest.mark.unit
def test_failure_result_serializes_required_fields():
    # We don't run a real browser here; we test that the function is importable
    # and returns the documented keys (even on failure path via mutation).
    # Actual browser behavior is covered in integration/e2e.
    # Smoke: calling with an invalid mutation should still return a dict with keys.
    res = run_brittle_journey("baseline", headless=True, timeout_ms=100)
    assert isinstance(res, dict)
    for key in ("run_id", "mutation_id", "status", "manifest_path", "artifact_dir", "timestamp"):
        assert key in res


@pytest.mark.unit
def test_error_excerpt_is_truncated_to_safe_length():
    long = "x" * 2000
    out = _truncate(long, max_len=100)
    assert len(out) <= 100
    assert out.endswith("...")


@pytest.mark.unit
def test_build_target_url_contains_mutation():
    u = _build_target_url("testid_removed")
    assert "mutation=testid_removed" in u
    assert u.startswith("http")

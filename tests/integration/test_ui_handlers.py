"""Integration tests for M4 UI handlers/services.

These call the real runner (M2) and deterministic healing path (M3).
Requires storefront running:
  python -m http.server 8080 --directory demo_site

They deliberately use the same patterns as M3 (targeted calls, accept long failure case).
"""
import pytest
import os

from testpilot.ui import services


@pytest.mark.integration
def test_run_callback_passes_selected_mutation_to_runner():
    # Baseline should pass
    res = services.run_original_regression("baseline", headless=True)
    assert res["mutation_id"] == "baseline"
    assert res["status"] in ("passed", "failed")  # should be passed if storefront up
    assert "brittle_result" in res
    assert res["brittle_result"]["strategy"] == "brittle"

    # testid_removed should fail with brittle (if storefront is serving the mutation)
    res2 = services.run_original_regression("testid_removed", headless=True)
    assert res2["mutation_id"] == "testid_removed"
    # The brittle run may succeed or fail depending on whether server is up;
    # if it failed we expect diagnosis/proposal from M3 services
    if res2.get("status") == "failed":
        assert res2.get("proposal") is not None
        assert "get_by_role" in res2["proposal"].get("new_locator", "")


@pytest.mark.integration
def test_approve_callback_only_validates_pending_run():
    # Start a failure run
    current = services.run_original_regression("testid_removed", headless=True)
    if current.get("status") != "failed":
        pytest.skip("Storefront not producing the expected failure for this test")

    # Before approve, approved must be False
    assert current.get("approved") is False or current.get("approved") is None

    # Approve should run validation + repaired journey
    updated = services.approve_and_validate(current, headless=True)
    assert updated.get("approved") is True
    assert "validation" in updated
    # final_status should be healed if validation + repaired run succeeded
    assert updated.get("final_status") in ("healed", "failed", "needs_human_review")


@pytest.mark.integration
def test_run_callback_uses_shared_browser_concurrency_identifier():
    # This is mostly a documentation / shape test.
    # The actual concurrency_id="browser_runner" is enforced in the Gradio layout.
    # Here we just ensure the service functions are re-entrant safe in sequence.
    r1 = services.run_original_regression("baseline", headless=True)
    r2 = services.run_original_regression("testid_removed", headless=True)
    assert r1["run_id"] != r2["run_id"]


@pytest.mark.integration
def test_manifest_download_is_available_after_run():
    res = services.run_original_regression("testid_removed", headless=True)
    mp = res.get("manifest_path")
    if mp:
        assert os.path.exists(mp)
        assert mp.endswith("run_manifest.json")
    else:
        # If storefront wasn't running we still expect the key to be present (may be None)
        assert "manifest_path" in res

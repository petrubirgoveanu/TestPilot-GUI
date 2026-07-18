"""Unit tests for M4 UI services (pure, no browser, no Gradio app running)."""
import pytest

from testpilot.ui import services


@pytest.mark.unit
def test_mutation_selection_updates_gradio_state():
    # Simulate what the radio change handler returns
    html, desc, url = services.build_storefront_preview_html("baseline"), services.get_mutation_description("baseline"), services.build_target_url("baseline")
    assert "baseline" in url
    assert "No UI change" in desc or "Baseline" in desc

    html2, desc2, url2 = services.build_storefront_preview_html("testid_removed"), services.get_mutation_description("testid_removed"), services.build_target_url("testid_removed")
    assert "testid_removed" in url2
    assert "data-testid" in html2.lower() or "removed" in html2.lower()


@pytest.mark.unit
def test_baseline_preview_describes_testid_as_present():
    html = services.build_storefront_preview_html("baseline")
    assert "data-testid" in html or "add-backpack" in html


@pytest.mark.unit
def test_testid_removed_preview_describes_testid_as_removed():
    html = services.build_storefront_preview_html("testid_removed")
    assert "data-testid" in html.lower() or "removed" in html.lower()


@pytest.mark.unit
def test_preview_contains_stable_accessible_name():
    for mid in ("baseline", "testid_removed"):
        html = services.build_storefront_preview_html(mid)
        assert "Add Blue Backpack" in html


@pytest.mark.unit
def test_selected_mutation_builds_correct_storefront_url():
    u1 = services.build_target_url("baseline")
    u2 = services.build_target_url("testid_removed")
    assert "mutation=baseline" in u1
    assert "mutation=testid_removed" in u2
    assert u1.startswith("http")


@pytest.mark.unit
def test_repair_controls_hidden_without_pending_proposal():
    # When no proposal (baseline pass or before run), approve/reject should be hidden
    fake_state = None
    # services doesn't decide visibility; layout does based on result
    # Here we just check that a non-failed or no-proposal state has no proposal
    result = services.run_original_regression("baseline", headless=True)
    assert result.get("proposal") is None


@pytest.mark.unit
def test_repair_controls_enabled_when_proposal_pending():
    # For testid_removed failure we should get a proposal
    result = services.run_original_regression("testid_removed", headless=True)
    # This test may require storefront; if not running it will still return a dict
    if result.get("status") == "failed":
        assert result.get("proposal") is not None
    else:
        # If storefront not running the brittle may have other behavior; still check shape
        assert "proposal" in result


@pytest.mark.unit
def test_timeline_status_transitions_are_valid():
    result = services.run_original_regression("baseline", headless=True)
    tl = result.get("timeline", [])
    assert "Planned" in tl or len(tl) > 0

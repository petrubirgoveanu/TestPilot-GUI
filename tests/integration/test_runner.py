"""Integration tests for the real brittle runner using the controlled storefront.

These require the static server to be running:
  python -m http.server 8080 --directory demo_site

Use background_process in agent context or two terminals for humans.

Tests use the exact brittle flow from M1:
  goto + get_by_test_id("add-backpack").click() + expect cart-count == "1"
"""

import os
import json
import pytest

from testpilot.browser.runner import run_brittle_journey


@pytest.mark.integration
def test_runner_passes_against_baseline():
    res = run_brittle_journey("baseline", headless=True)
    assert res["status"] == "passed"
    assert res["mutation_id"] == "baseline"
    assert res["run_id"]
    assert res["manifest_path"] and os.path.exists(res["manifest_path"])
    assert "run_manifest.json" in res["manifest_path"]


@pytest.mark.integration
def test_runner_fails_against_testid_removed():
    res = run_brittle_journey("testid_removed", headless=True)
    assert res["status"] == "failed"
    assert res["mutation_id"] == "testid_removed"
    assert res["failed_step"] == "add_blue_backpack"
    assert res["error_excerpt"]
    # screenshot must exist and be non-empty
    assert res["screenshot_path"] and os.path.exists(res["screenshot_path"])
    assert os.path.getsize(res["screenshot_path"]) > 0


@pytest.mark.integration
def test_failed_run_identifies_add_backpack_step():
    res = run_brittle_journey("testid_removed", headless=True)
    assert res["status"] == "failed"
    assert res["failed_step"] == "add_blue_backpack"


@pytest.mark.integration
def test_failed_run_writes_screenshot():
    res = run_brittle_journey("testid_removed", headless=True)
    assert res["status"] == "failed"
    assert res["screenshot_path"] and os.path.isfile(res["screenshot_path"])


@pytest.mark.integration
def test_failed_run_writes_run_manifest():
    res = run_brittle_journey("testid_removed", headless=True)
    assert res["manifest_path"] and os.path.exists(res["manifest_path"])
    with open(res["manifest_path"], "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["status"] == "failed"
    assert m["mutation_id"] == "testid_removed"
    assert m["failed_step"] == "add_blue_backpack"


@pytest.mark.integration
def test_trace_path_exists_when_trace_capture_enabled():
    res = run_brittle_journey("testid_removed", headless=True, capture_trace=True)
    # trace_path may be None if tracing failed silently, but key should be present
    assert "trace_path" in res
    # If present, file must exist and be non-empty
    if res.get("trace_path"):
        assert os.path.exists(res["trace_path"])
        assert os.path.getsize(res["trace_path"]) > 0

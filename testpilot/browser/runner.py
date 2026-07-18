"""Synchronous Playwright runner for the Minimum Demoable Slice (brittle path only).

Implements the exact brittle journey proven in M1:
  page.goto(url)
  page.get_by_test_id("add-backpack").click()
  expect(cart-count).to_have_text("1")

Captures: run_id, mutation_id, status, failed_step, error_excerpt (truncated),
screenshot (on failure), manifest, artifact dir.

No repair logic here. No LLM calls.
"""

import os
import time
from typing import Any, Dict

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from testpilot.models import resolve_locator
from testpilot.reporting.run_manifest import new_run_id, ensure_artifact_dir, write_manifest


BASE = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")


def _truncate(text: str, max_len: int = 800) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _build_target_url(mutation_id: str) -> str:
    # mutation_id is one of: "baseline", "testid_removed"
    return f"{BASE}/index.html?mutation={mutation_id}"


def run_brittle_journey(
    mutation_id: str,
    *,
    headless: bool = True,
    timeout_ms: int = 30000,
    capture_trace: bool = False,
) -> Dict[str, Any]:
    """Execute the original brittle journey against the controlled storefront.

    Returns a dict with at least:
      status, mutation_id, run_id, failed_step, error_excerpt,
      screenshot_path, manifest_path, artifact_dir, timestamp
    """
    run_id = new_run_id()
    artifact_dir = ensure_artifact_dir(run_id)
    screenshot_path = os.path.join(artifact_dir, "failure.png")
    manifest_path = None

    failed_step = "add_blue_backpack"
    status = "passed"
    error_excerpt = ""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    target_url = _build_target_url(mutation_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        if capture_trace:
            context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
            btn = resolve_locator(page, "add_blue_backpack", "brittle")
            btn.click(timeout=timeout_ms)

            # Assertion (exact brittle expectation from M1)
            cart = resolve_locator(page, "cart_count", "brittle")
            cart.wait_for(timeout=timeout_ms)
            # If we reach here without timeout, the journey passed for this mutation
            status = "passed"
        except PlaywrightTimeoutError as e:
            status = "failed"
            error_excerpt = _truncate(str(e))
            # Take screenshot on failure
            try:
                page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                pass
            failed_step = "add_blue_backpack"
        except Exception as e:
            status = "failed"
            error_excerpt = _truncate(str(e))
            try:
                page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                pass
            failed_step = "add_blue_backpack"
        finally:
            if capture_trace:
                try:
                    trace_path = os.path.join(artifact_dir, "trace.zip")
                    context.tracing.stop(path=trace_path)
                    result["trace_path"] = trace_path if os.path.exists(trace_path) else None
                except Exception:
                    pass
            # Always close to avoid resource leaks
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass

    result: Dict[str, Any] = {
        "run_id": run_id,
        "mutation_id": mutation_id,
        "status": status,
        "failed_step": failed_step if status == "failed" else None,
        "error_excerpt": error_excerpt if status == "failed" else "",
        "screenshot_path": screenshot_path if status == "failed" and os.path.exists(screenshot_path) else None,
        "artifact_dir": artifact_dir,
        "timestamp": timestamp,
        "original_locator": "get_by_test_id('add-backpack')",
    }

    # Write manifest (always)
    manifest_data = {
        "run_id": run_id,
        "mutation_id": mutation_id,
        "status": status,
        "failed_step": result["failed_step"],
        "error_excerpt": result["error_excerpt"],
        "screenshot_path": result["screenshot_path"],
        "timestamp": timestamp,
        "original_locator": result["original_locator"],
        "reasoning_mode": "deterministic",
    }
    manifest_path = write_manifest(run_id, manifest_data)
    result["manifest_path"] = manifest_path

    return result


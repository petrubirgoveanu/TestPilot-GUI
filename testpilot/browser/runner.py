"""Synchronous Playwright runner for the Minimum Demoable Slice.

Supports two strategies:
- "brittle": original get_by_test_id (M2 contract, breaks on testid_removed)
- "repaired": get_by_role + name (survives the mutation)

Journey (golden):
  page.goto(url?mutation=...)
  <locator>.click()
  expect(cart-count).to_have_text("1")

Captures per run: run_id, mutation_id, status, strategy, locator, failed_step,
error_excerpt (truncated), screenshot (on fail), manifest, artifact_dir.

No LLM. Deterministic only.
"""

import os
import time
from typing import Any, Dict, Literal

from playwright.sync_api import sync_playwright, expect, TimeoutError as PlaywrightTimeoutError

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


def run_journey(
    mutation_id: str,
    *,
    strategy: Literal["brittle", "repaired"] = "brittle",
    headless: bool = True,
    timeout_ms: int = 30000,
    capture_trace: bool = False,
) -> Dict[str, Any]:
    """Execute the golden journey using the chosen locator strategy.

    strategy:
      - "brittle": original get_by_test_id (breaks on testid_removed)
      - "repaired": get_by_role + accessible name (survives the mutation)

    Returns a dict with at least:
      status, mutation_id, run_id, failed_step, error_excerpt,
      screenshot_path, manifest_path, artifact_dir, timestamp, strategy
    """
    run_id = new_run_id()
    artifact_dir = ensure_artifact_dir(run_id)
    screenshot_path = os.path.join(artifact_dir, "failure.png")

    failed_step = "add_blue_backpack"
    status = "passed"
    error_excerpt = ""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    target_url = _build_target_url(mutation_id)
    locator_strategy = strategy

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        if capture_trace:
            context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
            btn = resolve_locator(page, "add_blue_backpack", locator_strategy)
            btn.click(timeout=timeout_ms)

            cart = resolve_locator(page, "cart_count", "brittle")
            cart.wait_for(timeout=timeout_ms)
            expect(cart).to_have_text("1", timeout=timeout_ms)
            status = "passed"
        except PlaywrightTimeoutError as e:
            status = "failed"
            error_excerpt = _truncate(str(e))
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
                    # note: we do not assign to undefined 'result' here
                except Exception:
                    pass
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
        "strategy": strategy,
        "locator": (
            "get_by_test_id('add-backpack')"
            if strategy == "brittle"
            else 'get_by_role("button", name="Add Blue Backpack")'
        ),
    }

    manifest_data = {
        "run_id": run_id,
        "mutation_id": mutation_id,
        "status": status,
        "failed_step": result["failed_step"],
        "error_excerpt": result["error_excerpt"],
        "screenshot_path": result["screenshot_path"],
        "timestamp": timestamp,
        "strategy": strategy,
        "locator": result["locator"],
        "reasoning_mode": "deterministic",
    }
    manifest_path = write_manifest(run_id, manifest_data)
    result["manifest_path"] = manifest_path

    return result


# Back-compat alias used by M2 tests
def run_brittle_journey(
    mutation_id: str,
    *,
    headless: bool = True,
    timeout_ms: int = 30000,
    capture_trace: bool = False,
) -> Dict[str, Any]:
    """Legacy wrapper: always uses brittle strategy (M2 contract)."""
    return run_journey(
        mutation_id,
        strategy="brittle",
        headless=headless,
        timeout_ms=timeout_ms,
        capture_trace=capture_trace,
    )


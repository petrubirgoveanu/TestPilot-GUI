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
import queue
import threading
import time
from typing import Any, Dict, Literal
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, expect, TimeoutError as PlaywrightTimeoutError

from testpilot.models import resolve_locator
from testpilot.reporting.run_manifest import new_run_id, ensure_artifact_dir, write_manifest

BASE = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")

LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "0.0.0.0"}


def _truncate(text: str, max_len: int = 800) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def build_target_url_candidates(mutation_id: str) -> list[str]:
    """Return target URL candidates, including a cloud-friendly /shop fallback.

    Candidate order is intentional:
    1. configured BASE_URL + /index.html (preserves explicit user config)
    2. BASE_URL + /shop/index.html when BASE_URL is host-root on non-local hosts
    """
    primary = f"{BASE}/index.html?mutation={mutation_id}"
    candidates = [primary]

    parsed = urlparse(BASE)
    path = (parsed.path or "").rstrip("/")
    hostname = (parsed.hostname or "").lower()
    should_try_shop = path == "" and hostname not in LOCAL_HOSTS

    if should_try_shop:
        candidates.append(f"{BASE}/shop/index.html?mutation={mutation_id}")

    # Preserve order and remove duplicates.
    return list(dict.fromkeys(candidates))


def build_target_url(mutation_id: str) -> str:
    # mutation_id is one of: "baseline", "testid_removed"
    return build_target_url_candidates(mutation_id)[0]


def _build_target_url(mutation_id: str) -> str:
    """Back-compat alias for existing tests and legacy imports."""
    return build_target_url(mutation_id)


def run_in_thread(func, *args, **kwargs):
    """Run a function in a clean background thread to avoid asyncio loop collisions with Playwright Sync API."""
    q = queue.Queue()
    def target():
        try:
            res = func(*args, **kwargs)
            q.put((True, res))
        except Exception as e:
            q.put((False, e))
    t = threading.Thread(target=target)
    t.start()
    t.join()
    success, val = q.get()
    if success:
        return val
    raise val


def run_journey(
    mutation_id: str,
    *,
    strategy: Literal["brittle", "repaired"] = "brittle",
    headless: bool = True,
    slow_mo_ms: int = 0,
    timeout_ms: int = 30000,
    capture_trace: bool = False,
) -> Dict[str, Any]:
    """Execute the journey inside a separate thread to bypass asyncio loop errors."""
    return run_in_thread(
        _run_journey_impl,
        mutation_id,
        strategy=strategy,
        headless=headless,
        slow_mo_ms=slow_mo_ms,
        timeout_ms=timeout_ms,
        capture_trace=capture_trace,
    )



def _run_journey_impl(
    mutation_id: str,
    *,
    strategy: Literal["brittle", "repaired"] = "brittle",
    headless: bool = True,
    slow_mo_ms: int = 0,
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
    trace_path = None

    failed_step = "add_blue_backpack"
    status = "passed"
    error_excerpt = ""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    target_urls = build_target_url_candidates(mutation_id)
    target_url = target_urls[0]
    locator_strategy = strategy

    with sync_playwright() as p:
        # headless=False makes the browser window visible for manual observation.
        # slow_mo_ms adds a delay (ms) between every Playwright action so you can
        # follow each step in the visible browser. Use together: headless=False, slow_mo_ms=500.
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
        context = browser.new_context()
        if capture_trace:
            context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()

        try:
            for idx, candidate_url in enumerate(target_urls):
                target_url = candidate_url
                is_last_candidate = idx == len(target_urls) - 1

                try:
                    page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
                    btn = resolve_locator(page, "add_blue_backpack", locator_strategy)
                    btn.click(timeout=timeout_ms)

                    cart = resolve_locator(page, "cart_count", "brittle")
                    cart.wait_for(timeout=timeout_ms)
                    expect(cart).to_have_text("1", timeout=timeout_ms)
                    status = "passed"
                    error_excerpt = ""
                    break
                except PlaywrightTimeoutError as e:
                    status = "failed"
                    error_excerpt = _truncate(str(e))
                    failed_step = "add_blue_backpack"
                    if not is_last_candidate:
                        continue
                    try:
                        page.screenshot(path=screenshot_path, full_page=True)
                    except Exception:
                        pass
                except Exception as e:
                    status = "failed"
                    error_excerpt = _truncate(str(e))
                    failed_step = "add_blue_backpack"
                    if not is_last_candidate:
                        continue
                    try:
                        page.screenshot(path=screenshot_path, full_page=True)
                    except Exception:
                        pass
        finally:
            if capture_trace:
                try:
                    trace_path = os.path.join(artifact_dir, "trace.zip")
                    context.tracing.stop(path=trace_path)
                except Exception:
                    trace_path = None
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
        "trace_path": trace_path if trace_path and os.path.exists(trace_path) else None,
        "timestamp": timestamp,
        "strategy": strategy,
        "target_url": target_url,
        "target_url_candidates": target_urls,
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
        "trace_path": result["trace_path"],
        "timestamp": timestamp,
        "strategy": strategy,
        "target_url": result["target_url"],
        "target_url_candidates": result["target_url_candidates"],
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
    slow_mo_ms: int = 0,
    timeout_ms: int = 30000,
    capture_trace: bool = False,
) -> Dict[str, Any]:
    """Legacy wrapper: always uses brittle strategy (M2 contract)."""
    return run_journey(
        mutation_id,
        strategy="brittle",
        headless=headless,
        slow_mo_ms=slow_mo_ms,
        timeout_ms=timeout_ms,
        capture_trace=capture_trace,
    )


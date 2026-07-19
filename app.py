"""TestPilot — M4 Gradio UI entrypoint.

Run with: python app.py
Uses real runner (M2) + deterministic repair/approval (M3).
No LLM calls.
"""
import os

import gradio as gr
import testpilot.config  # noqa: F401
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from testpilot.ui.layout import build_ui

demo = build_ui()

# Enable queue + concurrency for browser actions (critical for M4)
# Use default_concurrency_limit (concurrency_count is deprecated/removed in this Gradio)
demo = demo.queue(default_concurrency_limit=1)


def create_app() -> FastAPI:
    """Serve Gradio plus static demo storefront and run artifacts."""
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # Keep artifact path available for debug evidence links and manifest downloads.
    os.makedirs("artifacts", exist_ok=True)
    app.mount("/artifacts", StaticFiles(directory="artifacts", html=False), name="artifacts")
    app.mount("/app/artifacts", StaticFiles(directory="artifacts", html=False), name="app_artifacts")

    app.mount("/shop", StaticFiles(directory="demo_site", html=True), name="shop")
    return gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Cloud platforms provide PORT dynamically; keep 7860 as local default.
    port = int(os.getenv("PORT", "7860"))

    # Startup diagnostics for deployment debugging.
    base_url = os.getenv("BASE_URL", "").rstrip("/")
    public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").rstrip("/")
    app_root = f"https://{public_domain}" if public_domain else "(unknown public domain)"

    print(f"[startup] PORT={port}")
    print(f"[startup] BASE_URL={base_url or '(not set)'}")
    print(f"[startup] App URL hint={app_root}")
    if base_url:
        print(f"[startup] Baseline URL={base_url}/index.html?mutation=baseline")
        print(f"[startup] Mutation URL={base_url}/index.html?mutation=testid_removed")
    if public_domain:
        print(f"[startup] Same-service shop URL=https://{public_domain}/shop/index.html?mutation=baseline")

    uvicorn.run(create_app(), host="0.0.0.0", port=port)

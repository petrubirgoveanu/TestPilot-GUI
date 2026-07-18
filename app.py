"""TestPilot — M4 Gradio UI entrypoint.

Run with: python app.py
Uses real runner (M2) + deterministic repair/approval (M3).
No LLM calls.
"""
import gradio as gr
from testpilot.ui.layout import build_ui

demo = build_ui()

# Enable queue + concurrency for browser actions (critical for M4)
# Use default_concurrency_limit (concurrency_count is deprecated/removed in this Gradio)
demo = demo.queue(default_concurrency_limit=1)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

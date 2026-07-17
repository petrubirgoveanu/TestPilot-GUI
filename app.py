"""Minimal placeholder for Day 0.

Run with: python app.py
Later replace with real workflow.
"""
import gradio as gr

# Single source of truth for the supported golden path request
from testpilot.models import GOLDEN_INTENT

def run_placeholder():
    return "Run clicked (placeholder). Build the real flow next."

with gr.Blocks(title="TestPilot - Day 0") as demo:
    gr.Markdown("# TestPilot (Day 0 Placeholder)")
    gr.Markdown("**Goal:** Get the 3-step journey + one mutation + manual repair working first.")
    intent = gr.Textbox(
        label="Intent (supported only)",
        value=GOLDEN_INTENT,
    )
    run_btn = gr.Button("Run (will fail on mutated UI)")
    result = gr.Textbox(label="Result")
    run_btn.click(run_placeholder, inputs=[], outputs=result)

    gr.Markdown("### Next: implement storefront, Playwright run, screenshot, approve, validate.")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

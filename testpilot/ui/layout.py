"""Gradio UI layout placeholder for Milestone 4.

Keep callbacks thin. Business logic belongs in services.
"""

import gradio as gr

def build_ui():
    with gr.Blocks(title="TestPilot — AI-Assisted Self-Healing Browser Tests") as demo:
        gr.Markdown("# TestPilot — AI-Assisted Self-Healing Browser Tests")
        gr.Markdown("**UI Change Lab** (placeholder — implement in Milestone 4)")
        # All real controls will be added in Milestone 4
    return demo

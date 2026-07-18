"""Full Gradio Blocks UI for Milestone 4.

Wired to real runner (M2) + deterministic diagnosis/repair/validator (M3).
No LLM calls.
Uses Gradio queue + concurrency for browser actions.
"""
import gradio as gr
from typing import Any, Dict, Optional

from testpilot.models import GOLDEN_INTENT
from testpilot.ui import services

# State shape example (kept in gr.State):
# {
#   "run_id": "...",
#   "mutation_id": "testid_removed",
#   "status": "failed",
#   "brittle_result": {...},
#   "diagnosis": {...},
#   "proposal": {...},
#   "approved": False,
#   "validation": {...},
#   "repaired_result": {...},
#   "final_status": "healed",
#   "timeline": [...],
#   ...
# }


def build_ui():
    with gr.Blocks(title="TestPilot — AI-Assisted Self-Healing Browser Tests") as demo:
        gr.Markdown("# TestPilot — AI-Assisted Self-Healing Browser Tests")
        gr.Markdown("**Minimum Demoable Slice** — deterministic repair with explicit human approval.")

        # Top controls
        with gr.Row():
            with gr.Column(scale=2):
                intent = gr.Textbox(
                    label="Supported Intent (locked for slice)",
                    value=GOLDEN_INTENT,
                    interactive=False,
                )
            with gr.Column(scale=1):
                mutation = gr.Radio(
                    choices=services.get_mutation_choices(),
                    label="UI Change Lab — Select Mutation",
                    value="baseline",
                )

        # Preview + explanation
        preview = gr.HTML(label="Before / After Preview")
        mutation_desc = gr.Markdown()
        target_url_display = gr.Textbox(label="Target URL used by Playwright", interactive=False)

        # Run button
        run_btn = gr.Button("Generate & Run Original Regression", variant="primary")

        # Timeline
        timeline_md = gr.Markdown("**Timeline:** Planned")

        # Main evidence area
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Error / Evidence")
                error_box = gr.Textbox(label="Error excerpt", lines=4, interactive=False)
                screenshot = gr.Image(label="Failure Screenshot", type="filepath", interactive=False)
            with gr.Column():
                gr.Markdown("### Diagnosis")
                diagnosis_box = gr.Textbox(label="Diagnosis", lines=3, interactive=False)
                gr.Markdown("### Repair Proposal (code diff)")
                repair_diff = gr.HTML(label="Locator change")

        # FlowSpec + Playwright code (simplified for slice)
        with gr.Row():
            with gr.Column():
                gr.Markdown("### FlowSpec (business intent only)")
                flowspec_md = gr.Markdown("`goto storefront` → `click add_blue_backpack` → `assert cart_count == 1`")
            with gr.Column():
                gr.Markdown("### Playwright Code (before / after)")
                code_diff = gr.HTML()

        # Approval gate
        with gr.Row():
            approve_btn = gr.Button("Approve & Validate Repair", variant="secondary", visible=False)
            reject_btn = gr.Button("Reject Repair", visible=False)

        # Final result
        final_status = gr.Textbox(label="Final Status", interactive=False)
        manifest_path_box = gr.Textbox(label="Run Manifest Path", interactive=False)
        download_manifest = gr.File(label="Download manifest JSON", interactive=False, visible=False)

        # Hidden state
        run_state = gr.State(value=None)

        # --- Event wiring ---

        def on_mutation_change(mut_id: str):
            html = services.build_storefront_preview_html(mut_id)
            desc = services.get_mutation_description(mut_id)
            url = services.build_target_url(mut_id)
            return html, desc, url

        mutation.change(
            on_mutation_change,
            inputs=[mutation],
            outputs=[preview, mutation_desc, target_url_display],
        )

        def on_run(mut_id: str, current_state: Optional[Dict[str, Any]]):
            # Always run the original brittle regression using real runner
            result = services.run_original_regression(mut_id, headless=True)
            # Update preview to current selection just in case
            preview_html = services.build_storefront_preview_html(mut_id)
            desc = services.get_mutation_description(mut_id)
            url = services.build_target_url(mut_id)

            # Prepare UI values
            err = result.get("error_excerpt", "") or ""
            shot = result.get("screenshot_path")
            diag = ""
            if result.get("diagnosis"):
                diag = result["diagnosis"].get("reason", "")
            diff_html = services.get_repair_diff_html(result)
            code_html = services.get_repair_diff_html(result)  # reuse for simplicity
            tl = services.get_timeline_markdown(result.get("timeline", []))
            final = result.get("final_status", result.get("status", ""))

            show_approve = bool(result.get("proposal")) and not result.get("approved", False)
            show_reject = show_approve

            return (
                preview_html,
                desc,
                url,
                tl,
                err,
                shot,
                diag,
                diff_html,
                code_html,
                final,
                result.get("manifest_path", ""),
                result.get("manifest_path") if result.get("manifest_path") else None,
                result,  # run_state
                gr.update(visible=show_approve),  # approve_btn
                gr.update(visible=show_reject),   # reject_btn
            )

        run_btn.click(
            on_run,
            inputs=[mutation, run_state],
            outputs=[
                preview, mutation_desc, target_url_display,
                timeline_md,
                error_box, screenshot,
                diagnosis_box, repair_diff, code_diff,
                final_status, manifest_path_box, download_manifest,
                run_state,
                approve_btn, reject_btn,
            ],
            concurrency_id="browser_runner",
        )

        def on_approve(current: Optional[Dict[str, Any]]):
            if not current:
                return (gr.update(),) * 9 + (current, gr.update(visible=False), gr.update(visible=False))
            updated = services.approve_and_validate(current, headless=True)
            tl = services.get_timeline_markdown(updated.get("timeline", []))
            diag = updated.get("diagnosis", {}).get("reason", "") if updated.get("diagnosis") else ""
            diff_html = services.get_repair_diff_html(updated)
            final = updated.get("final_status", "")
            manifest = updated.get("manifest_path", "")
            show_approve = False
            show_reject = False
            return (
                tl,
                updated.get("error_excerpt", "") or "",
                updated.get("screenshot_path"),
                diag,
                diff_html,
                diff_html,
                final,
                manifest,
                manifest if manifest else None,
                updated,
                gr.update(visible=show_approve),
                gr.update(visible=show_reject),
            )

        approve_btn.click(
            on_approve,
            inputs=[run_state],
            outputs=[
                timeline_md, error_box, screenshot,
                diagnosis_box, repair_diff, code_diff,
                final_status, manifest_path_box, download_manifest,
                run_state, approve_btn, reject_btn,
            ],
            concurrency_id="browser_runner",
        )

        def on_reject(current: Optional[Dict[str, Any]]):
            if not current:
                return (gr.update(),) * 4 + (current, gr.update(visible=False), gr.update(visible=False))
            updated = services.reject_repair(current)
            tl = services.get_timeline_markdown(updated.get("timeline", []))
            final = updated.get("final_status", "")
            return (
                tl,
                final,
                updated.get("manifest_path", ""),
                updated.get("manifest_path") if updated.get("manifest_path") else None,
                updated,
                gr.update(visible=False),
                gr.update(visible=False),
            )

        reject_btn.click(
            on_reject,
            inputs=[run_state],
            outputs=[
                timeline_md, final_status, manifest_path_box, download_manifest,
                run_state, approve_btn, reject_btn,
            ],
        )

        # Initialize preview on load
        demo.load(
            lambda: on_mutation_change("baseline"),
            inputs=None,
            outputs=[preview, mutation_desc, target_url_display],
        )

    # IMPORTANT: enable queue for concurrency control
    return demo


if __name__ == "__main__":
    # For direct testing: python -m testpilot.ui.layout
    ui = build_ui()
    ui.queue().launch(server_name="0.0.0.0", server_port=7860)

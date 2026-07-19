"""Prompt loader for narrow LLM specialists.

Loads the fixed system prompt from prompts/<specialist>.md
"""
from pathlib import Path
from typing import Literal


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def load_system_prompt(specialist: Literal["planner", "diagnosis", "repair"]) -> str:
    """Load the system prompt markdown file content for the given specialist."""
    path = PROMPTS_DIR / f"{specialist}.md"
    if not path.exists():
        raise FileNotFoundError(f"System prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()

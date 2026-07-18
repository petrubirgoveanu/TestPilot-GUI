"""Runtime configuration (DEMO_MODE, API keys, etc.).

Load from environment. Defaults are safe for the slice.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:7860")

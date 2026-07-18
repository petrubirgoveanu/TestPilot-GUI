"""Runtime configuration (DEMO_MODE, API keys, etc.).

Load from environment. Defaults are safe for the slice.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
# The storefront URL used by Playwright to load the demo page under demo_site.
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# Map LangSmith environment variables to LangChain tracing equivalents
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "testpilot-hackathon")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "")

if LANGSMITH_TRACING:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    if LANGSMITH_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    if LANGSMITH_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
else:
    # Explicitly disable tracing if LANGSMITH_TRACING is false or not set
    os.environ["LANGCHAIN_TRACING_V2"] = "false"


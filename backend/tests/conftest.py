import os

# Force deterministic, offline test behavior regardless of the developer's
# local .env: mock auth (no real Clerk instance needed) and no LLM calls
# (no real OpenRouter key/network calls during the test suite). Must be set
# before anything imports config.settings, which loads .env with
# override=False — these pre-set values take precedence.
os.environ["AUTH_PROVIDER"] = "mock"
os.environ["OPENROUTER_API_KEY"] = ""

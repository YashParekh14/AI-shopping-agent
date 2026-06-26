"""
Central configuration. All settings come from environment variables so
nothing sensitive is hardcoded. Supports both SQLite (local dev) and
PostgreSQL/Supabase (production) via DATABASE_URL.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Database -----------------------------------------------------------
# If DATABASE_URL is set (Supabase/PostgreSQL), use it.
# Otherwise fall back to local SQLite — zero setup for local dev.
DATABASE_URL = os.getenv("DATABASE_URL")
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "store.db"))

# --- Models -------------------------------------------------------------
TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-4o")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# --- LangSmith (observability) -----------------------------------------
# Sign up free at smith.langchain.com, then set these three env vars.
# If not set, tracing is simply disabled — no errors.
LANGSMITH_TRACING = os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "shopping-agent")

# --- Logging -----------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

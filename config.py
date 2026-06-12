"""
Central configuration. Reads from environment variables (loaded from .env)
with sensible defaults so the app runs out of the box.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Database ---------------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "store.db"))

# --- Models -----------------------------------------------------------------
# Kept in config (not hardcoded across files) so they can be swapped without
# touching application logic.
TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen/qwen3-32b")
VISION_MODEL = os.getenv("VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# --- Logging ----------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


import os

from dotenv import load_dotenv

load_dotenv()

# --- Database -----
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "store.db"))


TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-4o")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")   
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# --- Logging ----
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

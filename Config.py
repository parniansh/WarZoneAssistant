from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# --- PATHS ---
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "warzone.db"

# --- ACLED ---
ACLED_EMAIL = os.getenv("ACLED_EMAIL")
ACLED_PASSWORD = os.getenv("ACLED_PASSWORD")
ACLED_AUTH_URL = "https://acleddata.com/oauth/token"
ACLED_URL = "https://acleddata.com/api/acled/read?limit=10"
ACLED_CLIENT_ID = "acled"
ACLED_GRANT_TYPE = "password"
ACLED_SCOPE = "authenticated"
ACLED_LIMIT = 100

# --- OLLAMA ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4:e2b"

# --- UPDATER ---
POLL_INTERVAL = 600  # 10 minutes in seconds

# --- PROXIMITY ---
PROXIMITY_RADIUS_KM = 50
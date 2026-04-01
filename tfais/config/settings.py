"""
Central configuration for TFAIS.
All values can be overridden via environment variables / .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Target site ---
BASE_URL = "http://115.243.209.84/people_app"
ENTRY_URL = f"{BASE_URL}/fertilizer/stock/en/20/2020"
BLOCKS_URL = f"{BASE_URL}/Fertilizer/getBlocks"    # POST /{district_id}
RESULTS_URL = f"{BASE_URL}/Fertilizer/result/en"   # POST with form data

# --- Fertilizer Price endpoints ---
PRICE_ENTRY_URL = f"{BASE_URL}/fertilizer_price/index/en/20/2020"
PRICE_API_URL = f"{BASE_URL}/fertilizer_price/fertDetails"
PRICE_RATE_LIMIT = float(os.getenv("PRICE_RATE_LIMIT_SECONDS", 1.0))

# --- HTTP behaviour ---
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", 2.0))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}

# --- Database ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "tfais")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/tfais.log")

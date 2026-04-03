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

# --- Seed Stock endpoints (Phase 1: Agri, Horti, Season-Wise) ---
SEED_BASE_URL = "https://www.tnagrisnet.tn.gov.in/people_app"
SEED_AGRI_ENTRY_URL = f"{SEED_BASE_URL}/Seed/seed_gov/en"
SEED_AGRI_BLOCKS_URL = f"{SEED_BASE_URL}/Seed/getBlocks"        # POST /{district_id}
SEED_AGRI_RESULTS_URL = f"{SEED_BASE_URL}/Seed/result/en"       # POST with form data
SEED_HORTI_ENTRY_URL = f"{SEED_BASE_URL}/Horti_seed/index/en"
SEED_HORTI_STOCK_TYPE_URL = f"{SEED_BASE_URL}/Horti_seed/loadStockType"  # POST /{block_id} → [{stock_type_id, stock_type_name}]
SEED_HORTI_LOAD_STOCK_URL = f"{SEED_BASE_URL}/Horti_seed/loadStock"      # POST /{stock_type_id}/{block_id} → [{stock_id, stock_name}]
SEED_HORTI_RESULTS_URL = f"{SEED_BASE_URL}/Horti_seed/result/en"         # POST with form data
SEED_SEASON_ENTRY_URL = f"{SEED_BASE_URL}/Season/index/en"
SEED_SEASON_GET_CROP_URL = f"{SEED_BASE_URL}/Season/getCrop"             # POST /{season}/{district_id}/{block_id} → [{stock_id, stock_name}]
SEED_SEASON_RESULTS_URL = f"{SEED_BASE_URL}/Season/result/en"            # POST with form data
SEED_RATE_LIMIT = float(os.getenv("SEED_RATE_LIMIT_SECONDS", 2.0))

# --- Machinery endpoints (CHC Mobile: Tractor, Woman Mechanics, Drone) ---
MACHINERY_BASE_URL = "http://115.243.209.84/chc/Mobile"
MACHINERY_DISTRICTS_URL = f"{MACHINERY_BASE_URL}/getDistricts"
MACHINERY_BLOCKS_URL = f"{MACHINERY_BASE_URL}/getBlocks"                   # GET /{district_id}
MACHINERY_TRACTOR_RESULTS_URL = f"{MACHINERY_BASE_URL}/getPrivateOwners"  # GET /{block_id}
MACHINERY_WDS_DISTRICTS_URL = f"{MACHINERY_BASE_URL}/getWDSDistricts"
MACHINERY_WDS_BLOCKS_URL = f"{MACHINERY_BASE_URL}/getWDSBlocks"            # GET /{district_id}
MACHINERY_WDS_RESULTS_URL = f"{MACHINERY_BASE_URL}/getWDCMechanics"        # GET /{block_id}
MACHINERY_DRONE_RESULTS_URL = f"{MACHINERY_BASE_URL}/loadDrone"            # GET /{district_id}
MACHINERY_RATE_LIMIT = float(os.getenv("MACHINERY_RATE_LIMIT_SECONDS", 1.0))

# --- HTTP behaviour ---
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", 2.0))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
MAX_CONCURRENT_DISTRICTS = int(os.getenv("MAX_CONCURRENT_DISTRICTS", 10))

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

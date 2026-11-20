
from pathlib import Path
import os
from dotenv import load_dotenv


# =====================================================
# STEP 1: PROJECT DIRECTORY
# =====================================================

# Project root is the shopflow-DE folder.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# =====================================================
# STEP 2: ENVIRONMENT VARIABLES
# =====================================================

# Load settings from the .env file in the project root.
load_dotenv(PROJECT_ROOT / ".env", override=True)


# =====================================================
# STEP 3: DATA DIRECTORIES
# =====================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

LOG_DIR = PROJECT_ROOT / "logs"


# =====================================================
# STEP 4: DATABASE CONFIGURATION
# =====================================================

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "shopflow"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
}

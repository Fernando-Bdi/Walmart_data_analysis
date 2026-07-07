from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent

# Database
DATABASE = BASE_DIR / "shipment_database.db"

# Data folders
DATA_FOLDER = BASE_DIR / "data" / "source"
EXPORT_FOLDER = BASE_DIR / "exports"

# Create folders automatically
DATA_FOLDER.mkdir(parents=True, exist_ok=True)
EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
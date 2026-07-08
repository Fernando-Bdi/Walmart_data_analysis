import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import pytest
import config
from app import app
from fastapi.testclient import TestClient
import sqlite3

TESTS_DIR = PROJECT_ROOT / "tests"


@pytest.fixture(scope="session", autouse=True)
def prepare_test_db():
    # Configure test paths and ensure the DB is present for all tests
    config.DATABASE = TESTS_DIR / "test_database.db"
    config.DATA_FOLDER = TESTS_DIR / "data"
    config.EXPORT_FOLDER = TESTS_DIR / "exports"

    config.EXPORT_FOLDER.mkdir(exist_ok=True)

    # Ensure the test database exists and has required tables/data
    db_path = TESTS_DIR / "test_database.db"
    # Recreate a fresh test database for each test session
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipment(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        origin TEXT,
        destination TEXT
    )
    """)

    conn.commit()

    # Do not pre-seed data here; tests will create products/shipments as needed
    conn.close()

    yield

@pytest.fixture(scope="session")
def client():
    return TestClient(app)
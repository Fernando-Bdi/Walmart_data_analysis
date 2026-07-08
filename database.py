import sqlite3
import config

def get_connection():
    # Use config.DATABASE at call time so tests can override it via conftest
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the product/shipment tables if they don't already exist.

    Safe to call every time the app starts (CREATE TABLE IF NOT EXISTS is a
    no-op if the tables are already there), so this works whether the DB
    file is empty, missing, or already populated.
    """
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS product(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS shipment(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            origin TEXT,
            destination TEXT
        )
    """)

    conn.commit()
    conn.close()

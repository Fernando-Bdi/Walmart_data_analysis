import sqlite3
import config

def get_connection():
    # I used config.DATABASE at call time so tests can override it via conftest
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    
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

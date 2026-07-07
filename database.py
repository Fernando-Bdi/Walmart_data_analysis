import sqlite3
import config

def get_connection():
    # Use config.DATABASE at call time so tests can override it via conftest
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
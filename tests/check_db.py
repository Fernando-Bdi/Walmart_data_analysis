from pathlib import Path
import sqlite3

p = Path('test_database.db').resolve()
print('DB path:', p)
conn = sqlite3.connect(p)
c = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables:', [row[0] for row in c.fetchall()])
conn.close()

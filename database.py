import sqlite3

def init_db():
    conn = sqlite3.connect("honeypot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS attacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            username TEXT,
            password TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_to_db(ip, username, password):
    conn = sqlite3.connect("honeypot.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO attacks (ip, username, password, timestamp) VALUES (?, ?, ?, datetime('now'))",
        (ip, username, password)
    )
    conn.commit()
    conn.close()
import sqlite3
import threading
import os

DB_FILE = os.getenv("DB_FILE", "petbot.db")
_lock = threading.Lock()

def connect():
    with _lock:
        con = sqlite3.connect(DB_FILE, check_same_thread=False)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                pet_species TEXT,
                gender TEXT,
                nickname TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                hunger INTEGER DEFAULT 100,
                fun INTEGER DEFAULT 100,
                hygiene INTEGER DEFAULT 100,
                energy INTEGER DEFAULT 100,
                coins INTEGER DEFAULT 0,
                lang TEXT DEFAULT 'pt'
            )
        """)
        con.commit()
    return con

# Helpers
con = connect()
cur = con.cursor()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        return None
    cols = [col[0] for col in cur.description]
    return dict(zip(cols, row))

def save_user(user_id, data: dict):
    # Upsert (update all fields present in data)
    cols = []
    vals = []
    for k, v in data.items():
        cols.append(f"{k} = ?")
        vals.append(v)
    vals.append(user_id)
    with _lock:
        cur.execute(f"UPDATE users SET {', '.join(cols)} WHERE user_id = ?", tuple(vals))
        con.commit()

def create_user(user_id, pet_species, gender, nickname, lang="pt"):
    with _lock:
        cur.execute("""
            INSERT OR REPLACE INTO users (user_id, pet_species, gender, nickname, lang)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, pet_species, gender, nickname, lang))
        con.commit()
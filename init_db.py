# init_db.py
import sqlite3
DB = "rea.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Modifica esta sección
cur.execute("""
    CREATE TABLE IF NOT EXISTS recursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    categoria TEXT,
    enlace TEXT,
    cid TEXT,
    filename TEXT,
    embedding BLOB,
    user_id INTEGER, -- AÑADE ESTA LÍNEA
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuarios (id) -- AÑADE ESTA LÍNEA
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
    )
""")

conn.commit()
conn.close()
print("DB inicializada: rea.db")
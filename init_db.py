# init_db.py
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Get the database file path from environment variables, with a default value
DB_FILE = os.getenv("DATABASE_URL", "rea.db")

# Connect to the SQLite database
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Create the 'recursos' table if it doesn't exist
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
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
""")

# Create the 'usuarios' table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
    )
""")

# Commit the changes and close the connection
conn.commit()
conn.close()
print(f"DB initialized: {DB_FILE}")

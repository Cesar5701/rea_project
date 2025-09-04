# migra_add_embedding.py
import sqlite3

DB = "rea.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE recursos ADD COLUMN embedding BLOB")
    print("Columna 'embedding' añadida.")
except Exception as e:
    print("No se pudo añadir (quizá ya existe):", e)
conn.commit()
conn.close()

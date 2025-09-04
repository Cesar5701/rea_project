# init_db.py
import sqlite3
DB = "rea.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
conn.close()
print("DB inicializada: rea.db")# init_db.py
import sqlite3  # Import SQLite library to interact with the database
DB = "rea.db"  # Define the database file name
conn = sqlite3.connect(DB)  # Establish a connection to the database (creates it if it doesn't exist)
cur = conn.cursor()  # Create a cursor object to execute SQL commands

# Execute an SQL command to create a table named 'recursos' if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS recursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 'id' column, autoincrementing primary key
    titulo TEXT NOT NULL,  -- 'titulo' column, mandatory text
    descripcion TEXT,  -- 'descripcion' column, optional text
    categoria TEXT,  -- 'categoria' column, optional text
    enlace TEXT,  -- 'enlace' column, optional text
    cid TEXT,  -- 'cid' column to store the IPFS Content Identifier
    filename TEXT,  -- 'filename' column to store the file name
    embedding BLOB,  -- 'embedding' column to store vector representations (embeddings)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 'created_at' column, creation date with default value
    )
""")

conn.commit()  # Save the changes in the database
conn.close()  # Close the connection to the database
print("DB initialized: rea.db")  # Print a message indicating that the database has been initialized

# Explicación en español:
# Este script crea una base de datos SQLite llamada 'rea.db' (si no existe) y, dentro de ella,
# crea una tabla llamada 'recursos'. Esta tabla tiene varias columnas para almacenar información
# sobre recursos, incluyendo su título, descripción, categoría, enlaces, identificadores IPFS ('cid'),
# nombres de archivo y representaciones vectoriales ('embedding'). También incluye una columna para
# la fecha de creación.

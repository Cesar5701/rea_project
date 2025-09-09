# sync_to_chroma.py
import sqlite3
from nlp_utils import blob_to_embedding
from vector_db import add_embedding
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Get the database file path from environment variables, with a default value
DB_FILE = os.getenv("DATABASE_URL", "rea.db")

def sync_database():
    """
    Reads all resources from the SQLite database and adds them to ChromaDB.
    This script is 'idempotent', meaning you can run it multiple times
    and it will not duplicate entries thanks to the use of unique IDs in ChromaDB.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        
        # Select only the resources that have an embedding
        recursos = conn.execute("SELECT id, titulo, categoria, embedding FROM recursos WHERE embedding IS NOT NULL").fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error al leer la base de datos SQLite: {e}")
        sys.exit(1)

    if not recursos:
        print("No se encontraron recursos con embeddings en la base de datos.")
        return

    print(f"Sincronizando {len(recursos)} recursos a ChromaDB...")
    
    count = 0
    for r in recursos:
        resource_id = r['id']
        
        try:
            # Convert the BLOB to a numpy vector
            embedding_vector = blob_to_embedding(r['embedding'])
            
            # Prepare the metadata we want to store in ChromaDB
            # This is useful for filtering searches in the future
            metadata = {
                "titulo": r['titulo'],
                "categoria": r['categoria'] if r['categoria'] else "Sin clasificar"
            }
            
            # Add the resource to the vector database
            add_embedding(resource_id, embedding_vector, metadata)
            count += 1
        except Exception as e:
            print(f"No se pudo procesar el recurso con ID {resource_id}: {e}")
            
    print(f"\nSincronización completa. Se procesaron {count} de {len(recursos)} recursos.")

if __name__ == '__main__':
    sync_database()

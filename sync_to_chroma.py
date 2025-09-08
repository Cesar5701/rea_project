# sync_to_chroma.py
import sqlite3
from nlp_utils import blob_to_embedding
from vector_db import add_embedding
import sys

DB_FILE = "rea.db"

def sync_database():
    """
    Lee todos los recursos de la base de datos SQLite y los añade a ChromaDB.
    Este script es 'idempotente', lo que significa que puedes ejecutarlo varias veces
    y no duplicará las entradas gracias al uso de IDs únicos en ChromaDB.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        
        # Seleccionamos solo los recursos que tienen un embedding
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
            # Convertimos el BLOB a un vector numpy
            embedding_vector = blob_to_embedding(r['embedding'])
            
            # Preparamos los metadatos que queremos almacenar en ChromaDB
            # Esto es útil para filtrar búsquedas en el futuro
            metadata = {
                "titulo": r['titulo'],
                "categoria": r['categoria'] if r['categoria'] else "Sin clasificar"
            }
            
            # Añadimos el recurso a la base de datos vectorial
            add_embedding(resource_id, embedding_vector, metadata)
            count += 1
        except Exception as e:
            print(f"No se pudo procesar el recurso con ID {resource_id}: {e}")
            
    print(f"\nSincronización completa. Se procesaron {count} de {len(recursos)} recursos.")

if __name__ == '__main__':
    sync_database()

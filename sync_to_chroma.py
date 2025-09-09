import sqlite3
import sys
from nlp_utils import blob_to_embedding
from vector_db import add_embedding
from config import Config

# Get the database file path from environment variables, with a default value
DB_FILE = Config.DATABASE_URL

def sync_database():
    """
    Reads all resources from the SQLite database and syncs them to ChromaDB.
    This script is idempotent, meaning it can be run multiple times without
    creating duplicate entries.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        # Select only resources that have an embedding.
        recursos = conn.execute("SELECT id, titulo, categoria, embedding FROM recursos WHERE embedding IS NOT NULL").fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error reading SQLite database: {e}")
        sys.exit(1)

    if not recursos:
        print("No resources with embeddings found in the database.")
        return

    print(f"Syncing {len(recursos)} resources to ChromaDB...")
    
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
                "categoria": r['categoria'] if r['categoria'] else "Unclassified"
            }
            
            # Add the resource to the vector database
            add_embedding(resource_id, embedding_vector, metadata)
            count += 1
        except Exception as e:
            print(f"Could not process resource with ID {resource_id}: {e}")
            
    print(f"\nSync complete. Processed {count} of {len(recursos)} resources.")

if __name__ == '__main__':
    sync_database()

# vector_db.py
import chromadb
import numpy as np
from nlp_utils import blob_to_embedding

# --- CLIENTE DE CHROMADB ---
# Usamos PersistentClient para que la base de datos se guarde en el disco.
# Se creará una carpeta llamada 'chroma_db' en la raíz de tu proyecto.
try:
    client = chromadb.PersistentClient(path="chroma_db")
except Exception as e:
    print(f"Error al inicializar ChromaDB: {e}")
    client = None

# --- COLECCIÓN ---
# Una colección es como una "tabla" para tus vectores.
try:
    collection = client.get_or_create_collection(name="recursos_educativos")
except Exception as e:
    print(f"Error al obtener o crear la colección en ChromaDB: {e}")
    collection = None

def add_embedding(resource_id: int, embedding: np.ndarray, metadata: dict):
    """
    Añade un embedding y sus metadatos a la colección de ChromaDB.
    
    Args:
        resource_id (int): El ID único del recurso (de tu base de datos SQLite).
        embedding (np.ndarray): El vector de embedding generado por el modelo de NLP.
        metadata (dict): Un diccionario con datos adicionales (título, categoría, etc.).
    """
    if not collection:
        print("Error: La colección de ChromaDB no está disponible.")
        return
        
    try:
        # ChromaDB espera que el embedding sea una lista de floats, no un array de numpy.
        embedding_list = embedding.tolist()
        
        # El ID debe ser un string.
        resource_id_str = str(resource_id)

        collection.add(
            embeddings=[embedding_list],
            metadatas=[metadata],
            ids=[resource_id_str]
        )
        print(f"Recurso {resource_id_str} añadido a ChromaDB.")
    except Exception as e:
        print(f"Error al añadir el embedding a ChromaDB para el recurso {resource_id}: {e}")

def query_similar(embedding: np.ndarray, top_k: int = 5) -> (list, list):
    """
    Busca los 'top_k' recursos más similares a un embedding dado.

    Args:
        embedding (np.ndarray): El vector de la consulta de búsqueda.
        top_k (int): El número de resultados a devolver.

    Returns:
        tuple: Una tupla conteniendo una lista de IDs de los recursos y una lista de sus puntuaciones de similitud.
    """
    if not collection:
        print("Error: La colección de ChromaDB no está disponible.")
        return [], []

    try:
        embedding_list = embedding.tolist()
        results = collection.query(
            query_embeddings=[embedding_list],
            n_results=top_k
        )
        
        # Extraemos los IDs y las 'distancias' (Chroma usa distancias, no similitud de coseno directa)
        ids = results.get('ids', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        # La distancia L2 al cuadrado (la que usa Chroma por defecto) es 0 para vectores idénticos.
        # La convertimos a una "puntuación de similitud" de 0 a 1 para mostrarla al usuario.
        # Similitud = 1 / (1 + Distancia)
        scores = [1 / (1 + d) for d in distances]
        
        return ids, scores
    except Exception as e:
        print(f"Error al realizar la consulta en ChromaDB: {e}")
        return [], []

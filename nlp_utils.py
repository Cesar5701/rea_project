# nlp_utils.py

import numpy as np
import torch
from transformers import pipeline, AutoTokenizer, AutoModel
import logging

# Configura el logging para suprimir las advertencias de transformers
logging.basicConfig(level=logging.ERROR)

# --- Constantes y Carga de Modelos (una sola vez) ---
MODEL_NAME = "dccuchile/bert-base-spanish-wwm-uncased"
CLASSIFIER_MODEL = "facebook/bart-large-mnli" # Un buen modelo para zero-shot

# Cargar modelos una sola vez para eficiencia
try:
    print("Cargando modelos de NLP... (puede tardar un momento la primera vez)")
    # Modelo para embeddings
    tokenizer_emb = AutoTokenizer.from_pretrained(MODEL_NAME)
    model_emb = AutoModel.from_pretrained(MODEL_NAME)
    
    # Pipeline para clasificación zero-shot
    # Usamos un modelo diferente y más adecuado para esta tarea
    classifier = pipeline("zero-shot-classification", model=CLASSIFIER_MODEL)
    print("Modelos cargados correctamente.")

except Exception as e:
    print(f"Error crítico al cargar modelos de NLP: {e}")
    # Si los modelos no cargan, las funciones fallarán. Podríamos salir o manejarlo.
    tokenizer_emb, model_emb, classifier = None, None, None

# Categorías predefinidas para la clasificación
CATEGORIAS_POSIBLES = [
    "programación", "diseño web", "matemáticas", "física", "química",
    "biología", "historia", "literatura", "arte", "música", "idiomas"
]

def generar_embedding(texto: str) -> np.ndarray:
    """Genera un embedding para un texto usando el modelo BERT."""
    if not tokenizer_emb or not model_emb:
        raise RuntimeError("El modelo de embeddings no está cargado.")
        
    inputs = tokenizer_emb(texto, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model_emb(**inputs)
    # Usamos el embedding del token [CLS] (primera posición)
    embedding = outputs.last_hidden_state[0, 0, :].cpu().numpy()
    # Normalizar el vector (mejora la similitud de coseno)
    norm = np.linalg.norm(embedding)
    return embedding / norm if norm != 0 else embedding

def clasificar_texto(texto: str) -> str:
    """Clasifica un texto en una de las categorías predefinidas usando zero-shot."""
    if not classifier:
        raise RuntimeError("El pipeline de clasificación no está cargado.")

    # El pipeline se encarga de todo
    resultado = classifier(texto, candidate_labels=CATEGORIAS_POSIBLES)
    # Devuelve la categoría con la puntuación más alta
    return resultado['labels'][0]

# --- Funciones de Serialización (sin cambios) ---
def embedding_to_blob(embedding: np.ndarray) -> bytes:
    """Convierte un vector numpy a bytes para guardarlo en la DB."""
    return embedding.tobytes()

def blob_to_embedding(blob: bytes) -> np.ndarray:
    """Convierte bytes de la DB de vuelta a un vector numpy."""
    return np.frombuffer(blob, dtype=np.float32)


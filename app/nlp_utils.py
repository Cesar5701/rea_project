# nlp_utils.py

import numpy as np
import torch
from transformers import pipeline, AutoTokenizer, AutoModel
import logging

# Configure logging to suppress transformers warnings
logging.basicConfig(level=logging.ERROR)

# --- Constants and Model Loading (once) ---
MODEL_NAME = "dccuchile/bert-base-spanish-wwm-uncased"
CLASSIFIER_MODEL = "facebook/bart-large-mnli" # A good model for zero-shot

# Load models once for efficiency
try:
    print("Cargando modelos de NLP... (puede tardar un momento la primera vez)")
    # Model for embeddings
    tokenizer_emb = AutoTokenizer.from_pretrained(MODEL_NAME)
    model_emb = AutoModel.from_pretrained(MODEL_NAME)
    
    # Pipeline for zero-shot classification
    # We use a different and more suitable model for this task
    classifier = pipeline("zero-shot-classification", model=CLASSIFIER_MODEL)
    print("Modelos cargados correctamente.")

except Exception as e:
    print(f"Error crítico al cargar modelos de NLP: {e}")
    # If the models do not load, the functions will fail. We could exit or handle it.
    tokenizer_emb, model_emb, classifier = None, None, None

# Predefined categories for classification
CATEGORIAS_POSIBLES = [
    "programación", "diseño web", "matemáticas", "física", "química",
    "biología", "historia", "literatura", "arte", "música", "idiomas"
]

def generar_embedding(texto: str) -> np.ndarray:
    """Generates an embedding for a text using the BERT model."""
    if not tokenizer_emb or not model_emb:
        raise RuntimeError("El modelo de embeddings no está cargado.")
        
    inputs = tokenizer_emb(texto, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model_emb(**inputs)
    # We use the embedding of the [CLS] token (first position)
    embedding = outputs.last_hidden_state[0, 0, :].cpu().numpy()
    # Normalize the vector (improves cosine similarity)
    norm = np.linalg.norm(embedding)
    return embedding / norm if norm != 0 else embedding

def clasificar_texto(texto: str) -> str:
    """Classifies a text into one of the predefined categories using zero-shot."""
    if not classifier:
        raise RuntimeError("El pipeline de clasificación no está cargado.")

    # The pipeline handles everything
    resultado = classifier(texto, candidate_labels=CATEGORIAS_POSIBLES)
    # Returns the category with the highest score
    return resultado['labels'][0]

# --- Serialization Functions (unchanged) ---
def embedding_to_blob(embedding: np.ndarray) -> bytes:
    """Converts a numpy vector to bytes to save it in the DB."""
    return embedding.tobytes()

def blob_to_embedding(blob: bytes) -> np.ndarray:
    """Converts bytes from the DB back to a numpy vector."""
    return np.frombuffer(blob, dtype=np.float32)

import pytest
import sqlite3
import os
from app import app as flask_app

# Ubicación de la base de datos de pruebas
TEST_DB = "test_rea.db"

@pytest.fixture(scope="module")
def app():
    """
    Fixture de nivel de módulo para crear y configurar la aplicación Flask
    una vez por cada sesión de pruebas.
    """
    # Configuración para el entorno de pruebas
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "testing-secret-key",
        "WTF_CSRF_ENABLED": False,  # Deshabilitar CSRF para pruebas de formularios
        "LOGIN_DISABLED": False,
        "DATABASE": TEST_DB,
    })

    # --- Creación de la base de datos de pruebas ---
    # Asegurarnos de que no exista una DB de pruebas anterior
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Conectar y crear las tablas usando el esquema de init_db.py
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)
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
    conn.commit()
    conn.close()
    
    # Cedemos la aplicación a las pruebas
    yield flask_app

    # --- Limpieza después de que todas las pruebas del módulo hayan terminado ---
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture()
def client(app):
    """
    Un cliente de pruebas para la aplicación.
    Se ejecuta para cada función de prueba.
    """
    return app.test_client()


@pytest.fixture()
def runner(app):
    """
    Un runner para ejecutar comandos CLI de la app.
    """
    return app.test_cli_runner()

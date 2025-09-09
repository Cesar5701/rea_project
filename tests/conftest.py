import pytest
import sqlite3
import os
import sys

# --- FIX FOR IMPORT ERROR ---
# Add the project root directory to the Python path.
# This allows pytest to find the 'app' package.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --- END OF FIX ---

from app import create_app
from config import TestingConfig

@pytest.fixture(scope='module')
def app():
    """
    Module-level fixture to create and configure the Flask application
    once per test session, using the testing configuration.
    """
    # FIX: create_app returns a tuple (app, socketio). We only need the app object here.
    flask_app, _ = create_app(config_class=TestingConfig)
    
    # Get the test database path from the app config.
    db_path = flask_app.config['DATABASE_URL']
    
    # Make sure no previous test DB exists.
    if os.path.exists(db_path):
        os.remove(db_path)

    # Establish the test database schema within the application context.
    with flask_app.app_context():
        conn = sqlite3.connect(db_path)
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
    
    yield flask_app

    # --- Cleanup after all module tests have finished ---
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture()
def client(app):
    """
    A test client for the application.
    Runs for each test function.
    """
    return app.test_client()


@pytest.fixture()
def runner(app):
    """
    A runner to execute CLI commands of the app.
    """
    return app.test_cli_runner()
import pytest
import sqlite3
import os
from app import app as flask_app

# Location of the test database
TEST_DB = "test_rea.db"

@pytest.fixture(scope="module")
def app():
    """
    Module-level fixture to create and configure the Flask application
    once per test session.
    """
    # Configuration for the test environment
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "testing-secret-key",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for form tests
        "LOGIN_DISABLED": False,
        "DATABASE": TEST_DB,
    })

    # --- Creation of the test database ---
    # Make sure no previous test DB exists
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Connect and create the tables using the schema from init_db.py
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
    
    # Yield the application to the tests
    yield flask_app

    # --- Cleanup after all module tests have finished ---
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


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

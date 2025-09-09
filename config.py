import os
from dotenv import load_dotenv

# Load environment variables from the .env file.
# This is the only place in the project where we need to call load_dotenv.
load_dotenv()

class Config:
    """Base configuration class."""
    # Secret key for signing session cookies and other security-related needs.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-default-unsafe-secret-key')
    
    # Main database URL.
    DATABASE_URL = os.environ.get('DATABASE_URL', 'rea.db')
    
    # Maximum file upload size (e.g., 16 MB).
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # API Token for Web3.Storage (IPFS).
    WEB3_STORAGE_TOKEN = os.environ.get('WEB3_STORAGE_TOKEN')

class DevelopmentConfig(Config):
    """Configuration for the development environment."""
    DEBUG = True

class TestingConfig(Config):
    """Configuration for the testing environment."""
    TESTING = True
    # Use a separate database for tests to avoid data corruption.
    DATABASE_URL = 'test_rea.db'
    # Disable CSRF protection in forms during tests for simplicity.
    WTF_CSRF_ENABLED = False
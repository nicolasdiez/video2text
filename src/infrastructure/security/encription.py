# src/infrastructure/security/mongodb.py

from cryptography.fernet import Fernet
import config

# Initialize Fernet with the DB_ENCRIPTION_SECRET_KEY defined in .env (and loaded in config.py).
# This key must be a valid Fernet key (base64-encoded 32-byte string).
# To generate one: Fernet.generate_key().decode()

DB_ENCRIPTION_SECRET_KEY = config.DB_ENCRIPTION_SECRET_KEY

if not DB_ENCRIPTION_SECRET_KEY:
    raise ValueError("DB_ENCRIPTION_SECRET_KEY is not set in environment variables")

fernet = Fernet(DB_ENCRIPTION_SECRET_KEY.encode())

def encrypt_value(value: str) -> str:
    """
    Encrypt a plain text string using Fernet symmetric encryption.
    Returns the encrypted value as a base64-encoded string.
    """
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    """
    Decrypt a previously encrypted string using Fernet symmetric encryption.
    Returns the original plain text value.
    """
    return fernet.decrypt(value.encode()).decode()
# src/infrastructure/security/mongodb.py

from cryptography.fernet import Fernet
import config

# Initialize Fernet with the SECRET_KEY defined in .env (and loaded in config.py).
# This key must be a valid Fernet key (base64-encoded 32-byte string).
# To generate one: Fernet.generate_key().decode()

SECRET_KEY = config.SECRET_KEY

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in environment variables")

fernet = Fernet(SECRET_KEY.encode())

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
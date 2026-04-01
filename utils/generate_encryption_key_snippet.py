# /utils/generate_encryption_key_snippet.py

# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base. It is meant to be used only once 
# What´s this script used for? --> generate encryption key in console, Then manually SAVE it to .env (DB_ENCRIPTION_SECRET_KEY). Encryption key is used to encrypt user credentials before saving to mongoDB.

from cryptography.fernet import Fernet

# Generate a new Fernet key (base64-encoded 32-byte string)
key = Fernet.generate_key()

print(key.decode())
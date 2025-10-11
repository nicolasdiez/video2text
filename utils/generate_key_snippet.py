# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base. 
# it is meant to be used only once --> generate encryption key in console and SAVE it to .env. Encryption key is used to encrypt user credentials before saving to mongoDB.

from cryptography.fernet import Fernet

# Generate a new Fernet key (base64-encoded 32-byte string)
key = Fernet.generate_key()

print(key.decode())
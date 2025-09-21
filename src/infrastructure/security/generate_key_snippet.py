# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base. 
# it is meant to be used only once --> generate key in console and SAVE it in .env

from cryptography.fernet import Fernet

# Generate a new Fernet key (base64-encoded 32-byte string)
key = Fernet.generate_key()

print(key.decode())
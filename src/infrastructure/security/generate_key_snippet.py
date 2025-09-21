# this is a snippet code, NOT part of the application code base. 
# meant to be used only once.

from cryptography.fernet import Fernet

# Generate a new Fernet key (base64-encoded 32-byte string)
key = Fernet.generate_key()

print(key.decode())
# src/infrastructure/security/password_hasher.py

# TODO: Instalación necesaria --> pip install passlib[bcrypt]

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """
    Interface-like class for hashing and verifying passwords.
    """

    def hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)


class BcryptPasswordHasher(PasswordHasher):
    """
    Concrete implementation using bcrypt via passlib.
    """
    pass

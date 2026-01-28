# src/security/jwt_service.py

# generar un JWT_SECRET_KEY --> bash terminal --> python -c "import secrets; print(secrets.token_hex(32))"

# TODO: Instalación necesaria --> pip install jose

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
import src.config as config


class JWTService:
    """
    Handles creation and validation of JWT access tokens.
    Reads configuration from src.config.
    """

    def __init__(self):
        self.secret_key = config.JWT_SECRET_KEY
        self.algorithm = config.JWT_ALGORITHM
        self.expire_minutes = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, subject: str) -> str:
        """
        Create a signed JWT containing the user ID as the subject.
        """
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)

        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_access_token(self, token: str) -> Optional[str]:
        """
        Validate a JWT and return the subject (user_id) if valid.
        Returns None if token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except JWTError:
            return None

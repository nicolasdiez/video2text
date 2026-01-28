# src/api/schemas/auth_schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequestDTO(BaseModel):
    """
    DTO for login requests.
    """
    email: EmailStr
    password: str


class UserResponseDTO(BaseModel):
    """
    DTO for returning user information to the client.
    """
    id: str
    email: EmailStr
    is_active: bool

    @classmethod
    def from_domain(cls, user) -> "UserResponseDTO":
        # Map from your domain User model to the DTO
        return cls(
            id=str(user.id),
            email=user.email,
            is_active=getattr(user, "is_active", True),
        )


class LoginResponseDTO(BaseModel):
    """
    DTO for login responses, including access token and user info.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO

# src/services/auth_service.py

from typing import Optional

from adapters.outbound.mongodb.user_repository import MongoUserRepository
from infrastructure.security.password_hasher import PasswordHasher
from security.jwt_service import JWTService
from api.schemas.auth_schemas import LoginResponseDTO, UserResponseDTO
from domain.entities.user import User


class AuthService:
    """
    Handles authentication-related use cases:
    - user login
    - user registration
    - password change
    - JWT token issuance
    """

    def __init__(
        self,
        user_repo: MongoUserRepository,
        password_hasher: PasswordHasher,
        jwt_service: JWTService,
    ):
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._jwt_service = jwt_service

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------

    async def login(self, email: str, password: str) -> Optional[LoginResponseDTO]:
        """
        Validate credentials and return a JWT + user info.
        """
        # 1. Retrieve user by email
        user = await self._user_repo.get_by_email(email)
        if not user:
            return None

        # 2. Verify password
        if not self._password_hasher.verify(password, user.hashed_password):
            return None

        # 3. Generate JWT
        access_token = self._jwt_service.create_access_token(subject=str(user.id))

        # 4. Build response DTO
        return LoginResponseDTO(
            access_token=access_token,
            user=UserResponseDTO.from_domain(user),
        )

    # ---------------------------------------------------------
    # REGISTER
    # ---------------------------------------------------------

    async def register(self, email: str, password: str) -> User:
        """
        Register a new user:
        - hash password
        - create User entity
        - persist it
        """
        hashed = self._password_hasher.hash(password)

        new_user = User(
            email=email,
            username=email,          # You can change this later if username != email
            hashed_password=hashed,
            is_active=True,
        )

        new_id = await self._user_repo.save(new_user)
        new_user.id = new_id

        return new_user

    # ---------------------------------------------------------
    # CHANGE PASSWORD
    # ---------------------------------------------------------

    async def change_password(self, user_id: str, new_password: str) -> None:
        """
        Change the password of an existing user:
        - hash the new password
        - persist the new hashed password
        """
        hashed = self._password_hasher.hash(new_password)
        await self._user_repo.update_password(user_id=user_id, hashed_password=hashed)


# ---------------------------------------------------------
# DEPENDENCY FACTORY (Composition Root)
# ---------------------------------------------------------

def get_auth_service() -> AuthService:
    """
    Composition root for AuthService.
    Instantiates dependencies explicitly.
    """
    user_repo = MongoUserRepository()
    password_hasher = PasswordHasher()
    jwt_service = JWTService()

    return AuthService(
        user_repo=user_repo,
        password_hasher=password_hasher,
        jwt_service=jwt_service,
    )

# src/application/services/dependencies.py

# Este module agrupa dependencias de FastAPI que no pertenecen al dominio ni a infraestructura pura, sino al “application layer”.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from adapters.outbound.mongodb.user_repository import MongoUserRepository
from security.jwt_service import JWTService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: MongoUserRepository = Depends(MongoUserRepository),
    jwt_service: JWTService = Depends(JWTService),
):
    """
    Extract and validate the current authenticated user from the JWT token.
    """
    # 1. Decode token
    user_id = jwt_service.verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # 2. Load user from DB
    user = await user_repo.find_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
